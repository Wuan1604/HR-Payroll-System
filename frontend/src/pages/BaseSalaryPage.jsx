import { useEffect, useMemo, useState } from 'react'
import { RefreshCw, Save, Pencil, Trash2, Search, X, Wallet } from '../components/LineIcons'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { deleteBaseSalary, getBaseSalaries, saveBaseSalary } from '../api/payrollApi'
import { formatMoney, formatNumberWithCommas, parseMoneyInput } from '../utils/money'
import '../styles/BaseSalaryPage.css'

function todayValue() {
  return new Date().toISOString().slice(0, 10)
}

const emptyForm = {
  EmployeeID: '',
  BaseSalary: '',
  EffectiveDate: todayValue(),
  Note: '',
}

export default function BaseSalaryPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState('')
  const [rows, setRows] = useState([])
  const [keyword, setKeyword] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [employeeQuery, setEmployeeQuery] = useState('')
  const [showEmployeeSuggestions, setShowEmployeeSuggestions] = useState(false)
  const [editingEmployeeId, setEditingEmployeeId] = useState('')

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await getBaseSalaries()
      setRows(Array.isArray(res) ? res : [])
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const filteredRows = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return rows
    return rows.filter((item) => {
      return [
        item.EmployeeID,
        item.FullName,
        item.DepartmentName,
        item.PositionName,
        item.Status,
      ].some((value) => String(value || '').toLowerCase().includes(q))
    })
  }, [rows, keyword])

  const selectedEmployee = useMemo(() => {
    return rows.find((item) => String(item.EmployeeID) === String(form.EmployeeID))
  }, [rows, form.EmployeeID])

  const employeeSuggestions = useMemo(() => {
    const q = employeeQuery.trim().toLowerCase()
    const source = q
      ? rows.filter((item) => {
          return [item.EmployeeID, item.FullName, item.DepartmentName, item.PositionName]
            .some((value) => String(value || '').toLowerCase().includes(q))
        })
      : rows
    return source.slice(0, 5)
  }, [rows, employeeQuery])

  function resetForm() {
    setForm(emptyForm)
    setEmployeeQuery('')
    setShowEmployeeSuggestions(false)
    setEditingEmployeeId('')
    setMessage('')
  }

  function handleChange(e) {
    const { name, value } = e.target
    const nextValue = name === 'BaseSalary' ? parseMoneyInput(value) : value
    setForm((prev) => ({ ...prev, [name]: nextValue }))
    setMessage('')
  }

  function selectEmployee(employee) {
    const employeeId = employee ? employee.EmployeeID : ''
    setForm({
      EmployeeID: employeeId,
      BaseSalary: employee?.HasBaseSalary ? employee.BaseSalary : '',
      EffectiveDate: employee?.EffectiveDate || todayValue(),
      Note: employee?.Note || '',
    })
    setEmployeeQuery(employee ? `${employee.EmployeeID} - ${employee.FullName}` : '')
    setShowEmployeeSuggestions(false)
    setEditingEmployeeId(employee?.HasBaseSalary ? String(employeeId) : '')
    setMessage('')
  }

  function handleEmployeeSearch(e) {
    const value = e.target.value
    setEmployeeQuery(value)
    setShowEmployeeSuggestions(true)
    setForm((prev) => ({ ...prev, EmployeeID: '' }))
    setEditingEmployeeId('')
    setMessage('')
  }

  function startEdit(item) {
    setForm({
      EmployeeID: item.EmployeeID,
      BaseSalary: item.BaseSalary || '',
      EffectiveDate: item.EffectiveDate || todayValue(),
      Note: item.Note || '',
    })
    setEmployeeQuery(`${item.EmployeeID} - ${item.FullName}`)
    setShowEmployeeSuggestions(false)
    setEditingEmployeeId(String(item.EmployeeID))
    setMessage('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function onSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setMessage('')

    try {
      if (!form.EmployeeID) throw new Error('Vui lòng chọn nhân viên.')
      if (form.BaseSalary === '') throw new Error('Vui lòng nhập lương cơ bản.')

      await saveBaseSalary({
        EmployeeID: Number(form.EmployeeID),
        BaseSalary: Number(form.BaseSalary || 0),
        EffectiveDate: form.EffectiveDate || null,
        Note: form.Note || '',
      })

      setMessage(editingEmployeeId ? 'Cập nhật lương cơ bản thành công.' : 'Thêm lương cơ bản thành công.')
      await load()
      setEditingEmployeeId(String(form.EmployeeID))
    } catch (e) {
      setError(e)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(item) {
    const ok = window.confirm(`Xóa lương cơ bản của nhân viên ${item.FullName}?`)
    if (!ok) return

    setError(null)
    setMessage('')
    try {
      await deleteBaseSalary(item.EmployeeID)
      setMessage('Đã xóa lương cơ bản của nhân viên.')
      await load()
      if (String(form.EmployeeID) === String(item.EmployeeID)) resetForm()
    } catch (e) {
      setError(e)
    }
  }

  return (
    <div className="base-salary-page">
      <div className="base-salary-header-card">
        <div>
          <h2><Wallet size={24} strokeWidth={1.8} aria-hidden="true" /> Quản lý lương cơ bản</h2>
          <p>
            Lưu mức lương cơ bản riêng cho từng nhân viên. Khi tạo bảng lương, hệ thống sẽ tự điền mức lương này sau khi chọn nhân viên.
          </p>
        </div>
        <button className="btn" onClick={load} disabled={loading || saving}>
          <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> Làm mới
        </button>
      </div>

      {error ? <ApiError error={error} /> : null}
      {message ? <div className="base-salary-message">{message}</div> : null}

      <form className="base-salary-form-card" onSubmit={onSubmit}>
        <div className="base-salary-form-title">
          <h3>{editingEmployeeId ? 'Sửa lương cơ bản' : 'Thêm lương cơ bản'}</h3>
          <button type="button" className="base-salary-clear-btn" onClick={resetForm}>
            <X size={16} strokeWidth={1.8} aria-hidden="true" /> Nhập mới
          </button>
        </div>

        <div className="base-salary-grid">
          <label className="base-salary-employee-field">
            <span>Nhân viên</span>
            <div className="base-salary-autocomplete">
              <input
                type="text"
                value={employeeQuery}
                onChange={handleEmployeeSearch}
                onFocus={() => setShowEmployeeSuggestions(true)}
                onBlur={() => setTimeout(() => setShowEmployeeSuggestions(false), 120)}
                placeholder="Tìm theo mã hoặc tên nhân viên"
                disabled={saving}
                autoComplete="off"
              />
              {showEmployeeSuggestions ? (
                <div className="base-salary-suggestions">
                  {employeeSuggestions.length === 0 ? (
                    <div className="base-salary-suggestion-empty">Không tìm thấy nhân viên</div>
                  ) : employeeSuggestions.map((item) => (
                    <button type="button" key={item.EmployeeID} onMouseDown={() => selectEmployee(item)}>
                      <strong>{item.EmployeeID} - {item.FullName}</strong>
                      <span>{item.DepartmentName || 'Chưa có phòng ban'} • {item.PositionName || 'Chưa có chức vụ'}</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </label>

          <label>
            <span>Lương cơ bản</span>
            <input
              type="text"
              inputMode="numeric"
              name="BaseSalary"
              value={formatNumberWithCommas(form.BaseSalary)}
              onChange={handleChange}
              placeholder="Ví dụ: 12,000,000"
              disabled={saving}
            />
          </label>

          <label>
            <span>Ngày áp dụng</span>
            <input type="date" name="EffectiveDate" value={form.EffectiveDate} onChange={handleChange} disabled={saving} />
          </label>
        </div>

        {selectedEmployee ? (
          <div className="base-salary-employee-box">
            <div><span>Phòng ban</span><strong>{selectedEmployee.DepartmentName || 'N/A'}</strong></div>
            <div><span>Chức vụ</span><strong>{selectedEmployee.PositionName || 'N/A'}</strong></div>
            <div><span>Trạng thái</span><strong>{selectedEmployee.Status || 'N/A'}</strong></div>
            <div><span>Lương đang lưu</span><strong>{selectedEmployee.HasBaseSalary ? formatMoney(selectedEmployee.BaseSalary) : 'Chưa có'}</strong></div>
          </div>
        ) : null}

        <label className="base-salary-note-field">
          <span>Ghi chú</span>
          <textarea name="Note" value={form.Note} onChange={handleChange} rows="3" placeholder="Ghi chú thay đổi lương cơ bản nếu có" disabled={saving} />
        </label>

        <div className="base-salary-form-actions">
          <button className="btn" type="submit" disabled={saving}>
            <Save size={16} strokeWidth={1.8} aria-hidden="true" /> {saving ? 'Đang lưu...' : editingEmployeeId ? 'Cập nhật lương cơ bản' : 'Thêm lương cơ bản'}
          </button>
        </div>
      </form>

      <div className="base-salary-table-card">
        <div className="base-salary-toolbar">
          <h3>Danh sách lương cơ bản</h3>
          <label className="base-salary-search">
            <Search size={16} strokeWidth={1.8} aria-hidden="true" />
            <input value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Tìm nhân viên, phòng ban, chức vụ..." />
          </label>
        </div>

        {loading ? <Loading /> : (
          <div className="base-salary-table-wrap">
            <table className="base-salary-table">
              <thead>
                <tr>
                  <th>Mã NV</th>
                  <th>Họ tên</th>
                  <th>Phòng ban</th>
                  <th>Chức vụ</th>
                  <th>Lương cơ bản</th>
                  <th>Ngày áp dụng</th>
                  <th>Ghi chú</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.length === 0 ? (
                  <tr><td colSpan="8" className="empty-cell">Không có dữ liệu phù hợp.</td></tr>
                ) : filteredRows.map((item) => (
                  <tr key={item.EmployeeID} className={!item.HasBaseSalary ? 'row-missing-salary' : ''}>
                    <td>{item.EmployeeID}</td>
                    <td>{item.FullName}</td>
                    <td>{item.DepartmentName}</td>
                    <td>{item.PositionName}</td>
                    <td><strong>{item.HasBaseSalary ? formatMoney(item.BaseSalary) : 'Chưa nhập'}</strong></td>
                    <td>{item.EffectiveDate || 'Chưa có'}</td>
                    <td>{item.Note || ''}</td>
                    <td>
                      <div className="base-salary-actions">
                        <button type="button" onClick={() => startEdit(item)} title="Sửa lương cơ bản">
                          <Pencil size={15} strokeWidth={1.8} aria-hidden="true" /> Sửa
                        </button>
                        <button type="button" className="danger" onClick={() => handleDelete(item)} disabled={!item.HasBaseSalary} title="Xóa lương cơ bản">
                          <Trash2 size={15} strokeWidth={1.8} aria-hidden="true" /> Xóa
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
