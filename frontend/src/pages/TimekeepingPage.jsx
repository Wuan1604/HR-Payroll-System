import { useEffect, useMemo, useState } from 'react'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import {
  getAttendanceDetails,
  getAttendanceEmployees,
  saveAttendanceCheck,
} from '../api/payrollApi'
import '../styles/TimekeepingPage.css'
import { getRole } from '../utils/auth'

function getToday() {
  return new Date().toISOString().slice(0, 10)
}

function getCurrentMonth() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString('vi-VN') + ' VNĐ'
}

function formatDate(value) {
  if (!value) return 'Chưa có'
  return String(value).slice(0, 10)
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('vi-VN')
}

export default function TimekeepingPage() {
  const [loading, setLoading] = useState(true)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState('')
  const [employees, setEmployees] = useState([])
  const [summary, setSummary] = useState(null)

  const [selectedEmployeeId, setSelectedEmployeeId] = useState('')
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth())
  const [baseSalary, setBaseSalary] = useState('')

  const [form, setForm] = useState({
    WorkDate: getToday(),
    CheckIn: '08:00',
    CheckOut: '17:00',
    Status: 'Đi làm',
    Note: '',
  })

  const role = getRole()
  const canManageAttendance = role === 'Admin' || role === 'Manager'

  const selectedEmployee = useMemo(() => {
    return employees.find(
      (item) => String(item.EmployeeID) === String(selectedEmployeeId)
    )
  }, [employees, selectedEmployeeId])

  async function loadEmployees() {
    setLoading(true)
    setError(null)

    try {
      const res = await getAttendanceEmployees()
      const data = Array.isArray(res) ? res : []
      setEmployees(data)

      if (data.length > 0 && !selectedEmployeeId) {
        setSelectedEmployeeId(String(data[0].EmployeeID))
      }
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  async function loadDetails(employeeId = selectedEmployeeId, month = selectedMonth, salary = baseSalary) {
    if (!employeeId || !month) return

    setLoadingDetails(true)
    setError(null)

    try {
      const res = await getAttendanceDetails(employeeId, month, salary || 0)
      setSummary(res)
    } catch (e) {
      setError(e)
      setSummary(null)
    } finally {
      setLoadingDetails(false)
    }
  }

  useEffect(() => {
    loadEmployees()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedEmployeeId && selectedMonth) {
      loadDetails(selectedEmployeeId, selectedMonth, baseSalary)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEmployeeId, selectedMonth])

  function handleFormChange(e) {
    const { name, value } = e.target

    setForm((prev) => {
      const next = {
        ...prev,
        [name]: value,
      }

      if (name === 'Status' && value !== 'Đi làm') {
        next.CheckIn = ''
        next.CheckOut = ''
      }

      if (name === 'Status' && value === 'Đi làm') {
        next.CheckIn = prev.CheckIn || '08:00'
        next.CheckOut = prev.CheckOut || '17:00'
      }

      return next
    })

    setMessage('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setMessage('')

    try {
      if (!selectedEmployeeId) {
        throw new Error('Vui lòng chọn nhân viên cần chấm công.')
      }

      const payload = {
        EmployeeID: Number(selectedEmployeeId),
        WorkDate: form.WorkDate,
        CheckIn: form.CheckIn || null,
        CheckOut: form.CheckOut || null,
        Status: form.Status,
        Note: form.Note,
      }

      const res = await saveAttendanceCheck(payload)
      setMessage(res?.message || 'Lưu chấm công thành công.')
      await loadDetails(selectedEmployeeId, selectedMonth, baseSalary)
    } catch (e) {
      setError(e)
    } finally {
      setSaving(false)
    }
  }

  const details = Array.isArray(summary?.details) ? summary.details : []

  return (
    <div className="timekeeping-page">
      <div className="timekeeping-header-card">
        <div>
          <h2>Chấm công nhân viên</h2>
          <p>
            Chọn nhân viên, nhập giờ vào/giờ ra theo ngày và tổng hợp công theo tháng.
          </p>
        </div>

        <button
          className="timekeeping-refresh-btn"
          onClick={() => loadDetails()}
          disabled={loadingDetails || !selectedEmployeeId}
        >
          {loadingDetails ? 'Đang tải...' : 'Làm mới'}
        </button>
      </div>

      {loading ? <Loading text="Đang tải danh sách nhân viên..." /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loading ? (
        <>
          <div className="timekeeping-filter-card">
            <label className="timekeeping-field">
              <span>Nhân viên</span>
              <select
                value={selectedEmployeeId}
                onChange={(e) => setSelectedEmployeeId(e.target.value)}
              >
                {employees.length === 0 ? (
                  <option value="">Chưa có nhân viên</option>
                ) : null}

                {employees.map((emp) => (
                  <option key={emp.EmployeeID} value={emp.EmployeeID}>
                    {emp.EmployeeID} - {emp.FullName}
                  </option>
                ))}
              </select>
            </label>

            <label className="timekeeping-field small">
              <span>Tháng chấm công</span>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
              />
            </label>

            <label className="timekeeping-field small">
              <span>Lương cơ bản để tính khấu trừ</span>
              <input
                type="number"
                value={baseSalary}
                onChange={(e) => setBaseSalary(e.target.value)}
                onBlur={() => loadDetails(selectedEmployeeId, selectedMonth, baseSalary)}
                placeholder="Ví dụ: 12000000"
              />
            </label>

            <button
              className="timekeeping-search-btn"
              type="button"
              onClick={() => loadDetails(selectedEmployeeId, selectedMonth, baseSalary)}
              disabled={loadingDetails || !selectedEmployeeId}
            >
              Xem tổng hợp
            </button>
          </div>

          {selectedEmployee ? (
            <div className="timekeeping-employee-card">
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
            </div>
          ) : null}

          {canManageAttendance ? (
          <form className="timekeeping-form-card" onSubmit={handleSubmit}>
            <div className="timekeeping-section-title">Nhập chấm công theo ngày</div>

            <div className="timekeeping-form-grid">
              <label className="timekeeping-field">
                <span>Ngày chấm công</span>
                <input
                  type="date"
                  name="WorkDate"
                  value={form.WorkDate}
                  onChange={(e) => {
                    handleFormChange(e)
                    setSelectedMonth(String(e.target.value).slice(0, 7))
                  }}
                />
              </label>

              <label className="timekeeping-field">
                <span>Trạng thái</span>
                <select name="Status" value={form.Status} onChange={handleFormChange}>
                  <option value="Đi làm">Đi làm</option>
                  <option value="Nghỉ phép">Nghỉ phép</option>
                  <option value="Nghỉ không phép">Nghỉ không phép</option>
                </select>
              </label>

              <label className="timekeeping-field">
                <span>Giờ vào</span>
                <input
                  type="time"
                  name="CheckIn"
                  value={form.CheckIn}
                  onChange={handleFormChange}
                  disabled={form.Status !== 'Đi làm'}
                />
              </label>

              <label className="timekeeping-field">
                <span>Giờ ra</span>
                <input
                  type="time"
                  name="CheckOut"
                  value={form.CheckOut}
                  onChange={handleFormChange}
                  disabled={form.Status !== 'Đi làm'}
                />
              </label>
            </div>

            <label className="timekeeping-field note-field">
              <span>Ghi chú lý do thiếu công / nghỉ</span>
              <textarea
                name="Note"
                value={form.Note}
                onChange={handleFormChange}
                placeholder="Ví dụ: Nghỉ bệnh có phép, đi muộn, về sớm, thiếu giờ làm..."
              />
            </label>

            <div className="timekeeping-actions-row">
              <div className="timekeeping-rule-note">
                Quy định: 1 tuần làm 6 ngày, 1 ngày đủ công khi làm từ 8 tiếng trở lên.
              </div>

              <button className="timekeeping-save-btn" type="submit" disabled={saving || !selectedEmployeeId}>
                {saving ? 'Đang lưu...' : 'Lưu chấm công'}
              </button>
            </div>

            {message ? <div className="timekeeping-success-message">{message}</div> : null}
          </form>
          ) : null}

          <div className="timekeeping-summary-grid">
            <div className="timekeeping-summary-card">
              <span>Công chuẩn trong tháng</span>
              <strong>{formatNumber(summary?.standardWorkDays)}</strong>
            </div>

            <div className="timekeeping-summary-card">
              <span>Công thực tế</span>
              <strong>{formatNumber(summary?.workDays)}</strong>
            </div>

            <div className="timekeeping-summary-card">
              <span>Tổng giờ làm</span>
              <strong>{formatNumber(summary?.totalHours)} giờ</strong>
            </div>

            <div className="timekeeping-summary-card">
              <span>Nghỉ phép</span>
              <strong>{formatNumber(summary?.leaveDays)} ngày</strong>
            </div>

            <div className="timekeeping-summary-card">
              <span>Thiếu công / nghỉ</span>
              <strong>{formatNumber(summary?.missingWorkUnits)} công</strong>
            </div>

            <div className="timekeeping-summary-card highlight">
              <span>Khấu trừ đề xuất</span>
              <strong>{formatMoney(summary?.suggestedDeductions)}</strong>
            </div>
          </div>

          {loadingDetails ? <Loading text="Đang tải chi tiết chấm công..." /> : null}

          <div className="timekeeping-table-card">
            <div className="timekeeping-table-header">
              <h3>Chi tiết chấm công tháng {selectedMonth}</h3>
              <span>{details.length} bản ghi</span>
            </div>

            <div className="timekeeping-table-wrapper">
              <table className="timekeeping-table">
                <thead>
                  <tr>
                    <th>Ngày</th>
                    <th>Giờ vào</th>
                    <th>Giờ ra</th>
                    <th>Tổng giờ</th>
                    <th>Công</th>
                    <th>Trạng thái</th>
                    <th>Ghi chú</th>
                  </tr>
                </thead>

                <tbody>
                  {details.length > 0 ? (
                    details.map((item) => (
                      <tr key={item.DetailID || `${item.EmployeeID}-${item.WorkDate}`}>
                        <td>{formatDate(item.WorkDate)}</td>
                        <td>{item.CheckIn || '-'}</td>
                        <td>{item.CheckOut || '-'}</td>
                        <td>{formatNumber(item.TotalHours)} giờ</td>
                        <td>{formatNumber(item.WorkUnit)}</td>
                        <td>
                          <span className={`attendance-status ${item.Status === 'Đi làm' ? 'ok' : item.Status === 'Nghỉ phép' ? 'leave' : 'absent'}`}>
                            {item.Status}
                          </span>
                        </td>
                        <td>{item.Note || '-'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="timekeeping-empty-row">
                        Chưa có dữ liệu chấm công trong tháng này
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
