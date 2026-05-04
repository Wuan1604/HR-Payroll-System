import { useEffect, useMemo, useState } from 'react'
import { RefreshCw, Calculator, Save } from '../components/LineIcons'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getAttendanceSummary, getBaseSalaries, getSalaries, updateSalary } from '../api/payrollApi'
import { formatMoney, formatNumberWithCommas, parseMoneyInput } from '../utils/money'
import '../styles/UpdateSalaryPage.css'

function normalizeDate(value) {
  if (!value) return ''
  return String(value).slice(0, 10)
}

function toMonthInputValue(value) {
  if (!value) return ''
  return String(value).slice(0, 7)
}

function toSalaryDate(monthValue) {
  if (!monthValue) return ''
  return `${monthValue}-01`
}

function getCurrentMonth() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}

export default function UpdateSalaryPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [rows, setRows] = useState([])
  const [baseSalaryRows, setBaseSalaryRows] = useState([])
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [attendanceSummary, setAttendanceSummary] = useState(null)
  const [loadingAttendance, setLoadingAttendance] = useState(false)

  const [form, setForm] = useState({
    SalaryMonth: getCurrentMonth(),
    BaseSalary: '',
    Bonus: '',
    Deductions: '',
  })

  async function load() {
    setLoading(true)
    setError(null)

    try {
      const [salaryRes, baseRes] = await Promise.all([getSalaries(), getBaseSalaries()])
      const arr = Array.isArray(salaryRes) ? salaryRes : []
      const baseArr = Array.isArray(baseRes) ? baseRes : []
      setRows(arr)
      setBaseSalaryRows(baseArr)

      if (arr.length > 0 && !selectedEmployeeId) {
        const firstEmployeeId = String(arr[0].EmployeeID)
        setSelectedEmployeeId(firstEmployeeId)
        const defaultSalary = baseArr.find((item) => String(item.EmployeeID) === firstEmployeeId)?.BaseSalary || arr[0].DefaultBaseSalary || ''
        setForm((prev) => ({ ...prev, BaseSalary: defaultSalary || '' }))
      }
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const employees = useMemo(() => {
    const map = new Map()

    rows.forEach((item) => {
      if (!map.has(item.EmployeeID)) {
        map.set(item.EmployeeID, {
          EmployeeID: item.EmployeeID,
          FullName: item.FullName,
          DepartmentName: item.DepartmentName,
          PositionName: item.PositionName,
          Status: item.Status,
          DefaultBaseSalary: item.DefaultBaseSalary || 0,
          DefaultBaseSalaryEffectiveDate: item.DefaultBaseSalaryEffectiveDate || null,
        })
      }
    })

    baseSalaryRows.forEach((item) => {
      const existing = map.get(item.EmployeeID)
      if (existing) {
        existing.DefaultBaseSalary = item.BaseSalary || 0
        existing.DefaultBaseSalaryEffectiveDate = item.EffectiveDate || null
      } else {
        map.set(item.EmployeeID, {
          EmployeeID: item.EmployeeID,
          FullName: item.FullName,
          DepartmentName: item.DepartmentName,
          PositionName: item.PositionName,
          Status: item.Status,
          DefaultBaseSalary: item.BaseSalary || 0,
          DefaultBaseSalaryEffectiveDate: item.EffectiveDate || null,
        })
      }
    })

    return Array.from(map.values())
  }, [rows, baseSalaryRows])

  const selectedEmployee = useMemo(() => {
    return employees.find(
      (item) => String(item.EmployeeID) === String(selectedEmployeeId)
    )
  }, [employees, selectedEmployeeId])

  const selectedSalary = useMemo(() => {
    const salaryDate = toSalaryDate(form.SalaryMonth)

    return rows.find(
      (item) =>
        String(item.EmployeeID) === String(selectedEmployeeId) &&
        normalizeDate(item.SalaryMonth) === salaryDate &&
        Number(item.SalaryID || 0) > 0
    )
  }, [rows, selectedEmployeeId, form.SalaryMonth])

  const netSalary =
    Number(form.BaseSalary || 0) +
    Number(form.Bonus || 0) -
    Number(form.Deductions || 0)

  async function loadAttendanceSuggestion(employeeId, monthValue, baseSalaryValue) {
    if (!employeeId || !monthValue) {
      setAttendanceSummary(null)
      return
    }

    setLoadingAttendance(true)
    try {
      const res = await getAttendanceSummary(employeeId, monthValue, baseSalaryValue || 0)
      setAttendanceSummary(res)
    } catch {
      setAttendanceSummary(null)
    } finally {
      setLoadingAttendance(false)
    }
  }

  useEffect(() => {
    if (selectedEmployeeId && form.SalaryMonth) {
      loadAttendanceSuggestion(selectedEmployeeId, form.SalaryMonth, form.BaseSalary)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEmployeeId, form.SalaryMonth])

  function fillSalaryByEmployeeAndMonth(employeeId, monthValue) {
    const salaryDate = toSalaryDate(monthValue)

    const oldSalary = rows.find(
      (item) =>
        String(item.EmployeeID) === String(employeeId) &&
        normalizeDate(item.SalaryMonth) === salaryDate &&
        Number(item.SalaryID || 0) > 0
    )

    if (oldSalary) {
      setForm({
        SalaryMonth: monthValue,
        BaseSalary: oldSalary.BaseSalary ?? '',
        Bonus: oldSalary.Bonus ?? '',
        Deductions: oldSalary.Deductions ?? '',
      })
      loadAttendanceSuggestion(employeeId, monthValue, oldSalary.BaseSalary ?? 0)
    } else {
      const defaultBaseSalary =
        baseSalaryRows.find((item) => String(item.EmployeeID) === String(employeeId))?.BaseSalary ??
        rows.find((item) => String(item.EmployeeID) === String(employeeId))?.DefaultBaseSalary ??
        ''

      setForm({
        SalaryMonth: monthValue,
        BaseSalary: defaultBaseSalary || '',
        Bonus: '',
        Deductions: '',
      })
      loadAttendanceSuggestion(employeeId, monthValue, defaultBaseSalary || 0)
    }
  }

  function handleSelectEmployee(e) {
    const employeeId = e.target.value
    setSelectedEmployeeId(employeeId)
    fillSalaryByEmployeeAndMonth(employeeId, form.SalaryMonth)
    setMessage('')
  }

  function handleSelectMonth(e) {
    const monthValue = e.target.value
    fillSalaryByEmployeeAndMonth(selectedEmployeeId, monthValue)
    setMessage('')
  }

  function handleChange(e) {
    const { name, value } = e.target
    const moneyFields = ['BaseSalary', 'Bonus', 'Deductions']

    setForm((prev) => ({
      ...prev,
      [name]: moneyFields.includes(name) ? parseMoneyInput(value) : value,
    }))

    setMessage('')
  }

  async function refreshAttendanceDeduction() {
    await loadAttendanceSuggestion(selectedEmployeeId, form.SalaryMonth, form.BaseSalary)
  }

  async function applySuggestedDeduction() {
    const res = await getAttendanceSummary(
      selectedEmployeeId,
      form.SalaryMonth,
      form.BaseSalary || 0
    )
    setAttendanceSummary(res)
    setForm((prev) => ({
      ...prev,
      Deductions: Math.round(Number(res?.suggestedDeductions || 0)),
    }))
    setMessage('Đã áp dụng khấu trừ đề xuất từ dữ liệu chấm công.')
  }

  async function onSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setMessage('')

    try {
      if (!selectedEmployee?.EmployeeID) {
        throw new Error('Bạn cần chọn nhân viên để tạo bảng lương.')
      }

      if (!form.SalaryMonth) {
        throw new Error('Bạn cần chọn tháng lương.')
      }

      const payload = {
        EmployeeID: Number(selectedEmployee.EmployeeID),
        SalaryID: Number(selectedSalary?.SalaryID || 0),
        SalaryMonth: toSalaryDate(form.SalaryMonth),
        BaseSalary: Number(form.BaseSalary || 0),
        Bonus: Number(form.Bonus || 0),
        Deductions: Number(form.Deductions || 0),
      }

      const res = await updateSalary(payload)

      setMessage(
        selectedSalary
          ? 'Cập nhật bảng lương thành công.'
          : 'Tạo bảng lương mới thành công.'
      )

      await load()

      if (res?.EmployeeID) {
        setSelectedEmployeeId(String(res.EmployeeID))
      }
    } catch (e) {
      setError(e)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="update-salary-page">
      <div className="salary-header-card">
        <div>
          <h2 className="page-title-with-icon"><Calculator size={24} strokeWidth={1.8} aria-hidden="true" /> Tạo bảng lương hàng tháng</h2>
          <p>
            Chọn nhân viên, chọn tháng lương, nhập các khoản tiền và lưu bảng lương.
          </p>
        </div>

        <button className="btn salary-refresh-btn" onClick={load} disabled={loading || saving}>
          <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> Làm mới
        </button>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loading && !error ? (
        <form className="salary-form-card" onSubmit={onSubmit}>
          <div className="salary-section">
            <h3>Thông tin nhân viên</h3>

            <div className="salary-grid two-cols">
              <label className="salary-field">
                <span>Chọn nhân viên</span>
                <select value={selectedEmployeeId} onChange={handleSelectEmployee}>
                  {employees.length === 0 ? (
                    <option value="">Chưa có nhân viên trong payroll</option>
                  ) : (
                    <option value="">-- Chọn nhân viên --</option>
                  )}

                  {employees.map((emp) => (
                    <option key={emp.EmployeeID} value={emp.EmployeeID}>
                      {emp.EmployeeID} - {emp.FullName}
                    </option>
                  ))}
                </select>
              </label>

              <label className="salary-field">
                <span>Tháng lương</span>
                <input type="month" value={form.SalaryMonth} onChange={handleSelectMonth} />
              </label>
            </div>

            {selectedEmployee ? (
              <div className="employee-summary-box">
                <div>
                  <span>Mã nhân viên</span>
                  <strong>{selectedEmployee.EmployeeID}</strong>
                </div>
                <div>
                  <span>Họ và tên</span>
                  <strong>{selectedEmployee.FullName}</strong>
                </div>
                <div>
                  <span>Phòng ban</span>
                  <strong>{selectedEmployee.DepartmentName || 'Chưa có'}</strong>
                </div>
                <div>
                  <span>Chức vụ</span>
                  <strong>{selectedEmployee.PositionName || 'Chưa có'}</strong>
                </div>
                <div>
                  <span>Trạng thái</span>
                  <strong>{selectedEmployee.Status || 'Chưa có'}</strong>
                </div>
                <div>
                  <span>Lương cơ bản đang lưu</span>
                  <strong>{selectedEmployee.DefaultBaseSalary ? formatMoney(selectedEmployee.DefaultBaseSalary) : 'Chưa nhập'}</strong>
                </div>
              </div>
            ) : null}

            {selectedEmployee ? (
              <div className={selectedSalary ? 'salary-note warning' : 'salary-note'}>
                {selectedSalary
                  ? `Tháng ${toMonthInputValue(selectedSalary.SalaryMonth)} đã có bảng lương. Khi lưu, hệ thống sẽ cập nhật lại dữ liệu.`
                  : 'Tháng này chưa có bảng lương. Khi lưu, hệ thống sẽ tạo bảng lương mới.'}
              </div>
            ) : null}
          </div>

          <div className="salary-section">
            <h3>Thông tin chấm công liên quan</h3>

            <div className="salary-attendance-summary">
              <div>
                <span>Công chuẩn</span>
                <strong>{attendanceSummary?.standardWorkDays ?? 0}</strong>
              </div>
              <div>
                <span>Công thực tế</span>
                <strong>{attendanceSummary?.workDays ?? 0}</strong>
              </div>
              <div>
                <span>Thiếu công</span>
                <strong>{attendanceSummary?.missingWorkUnits ?? 0}</strong>
              </div>
              <div>
                <span>Khấu trừ đề xuất</span>
                <strong>{formatMoney(attendanceSummary?.suggestedDeductions || 0)}</strong>
              </div>
            </div>

            <div className="salary-attendance-actions">
              <button
                type="button"
                className="salary-secondary-btn"
                onClick={refreshAttendanceDeduction}
                disabled={loadingAttendance || !selectedEmployeeId}
              >
                <Calculator size={16} strokeWidth={1.8} aria-hidden="true" /> {loadingAttendance ? 'Đang tính...' : 'Tính lại từ chấm công'}
              </button>

              <button
                type="button"
                className="salary-secondary-btn apply"
                onClick={applySuggestedDeduction}
                disabled={!selectedEmployeeId}
              >
                <Calculator size={16} strokeWidth={1.8} aria-hidden="true" /> Áp dụng khấu trừ đề xuất
              </button>
            </div>
          </div>

          <div className="salary-section">
            <h3>Thông tin tiền lương</h3>

            <div className="salary-grid three-cols">
              <label className="salary-field">
                <span>Lương cơ bản</span>
                <input
                  type="text"
                  inputMode="numeric"
                  name="BaseSalary"
                  value={formatNumberWithCommas(form.BaseSalary)}
                  onChange={handleChange}
                  onBlur={refreshAttendanceDeduction}
                  placeholder="Nhập lương cơ bản"
                />
                {!selectedSalary && selectedEmployee?.DefaultBaseSalary ? (
                  <small className="salary-field-note">Đã tự điền từ lương cơ bản đang lưu.</small>
                ) : null}
              </label>

              <label className="salary-field">
                <span>Thưởng</span>
                <input
                  type="text"
                  inputMode="numeric"
                  name="Bonus"
                  value={formatNumberWithCommas(form.Bonus)}
                  onChange={handleChange}
                  placeholder="Nhập tiền thưởng"
                />
              </label>

              <label className="salary-field">
                <span>Khấu trừ</span>
                <input
                  type="text"
                  inputMode="numeric"
                  name="Deductions"
                  value={formatNumberWithCommas(form.Deductions)}
                  onChange={handleChange}
                  placeholder="Nhập tiền khấu trừ"
                />
              </label>
            </div>
          </div>

          <div className="salary-total-card">
            <div>
              <span>Lương thực nhận dự kiến</span>
              <strong>{formatMoney(netSalary)}</strong>
            </div>

            <button className="btn salary-save-btn" type="submit" disabled={saving || !selectedEmployee}>
              <Save size={16} strokeWidth={1.8} aria-hidden="true" /> {saving ? 'Đang lưu...' : selectedSalary ? 'Cập nhật bảng lương' : 'Tạo bảng lương'}
            </button>
          </div>

          {message ? <div className="salary-success-message">{message}</div> : null}
        </form>
      ) : null}
    </div>
  )
}
