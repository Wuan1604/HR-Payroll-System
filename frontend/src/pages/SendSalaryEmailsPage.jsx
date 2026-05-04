import { useEffect, useMemo, useState } from 'react'
import { RefreshCw, Send } from '../components/LineIcons'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getEmployees } from '../api/humanApi'
import { sendSalaryEmails } from '../api/payrollApi'
import '../styles/SendSalaryEmailsPage.css'

function getCurrentMonth() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}

export default function SendSalaryEmailsPage() {
  const [loadingEmployees, setLoadingEmployees] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [employees, setEmployees] = useState([])
  const [search, setSearch] = useState('')
  const [selectAll, setSelectAll] = useState(true)
  const [selectedIds, setSelectedIds] = useState([])

  const [form, setForm] = useState({
    month: getCurrentMonth(),
    sendProfile: true,
    sendAttendance: false,
    sendSalary: true,
  })

  async function loadEmployees() {
    setLoadingEmployees(true)
    setError(null)

    try {
      const res = await getEmployees()
      const rows = Array.isArray(res?.employees) ? res.employees : []
      setEmployees(rows)
      setSelectedIds(rows.map((item) => Number(item.EmployeeID)))
    } catch (e) {
      setError(e)
    } finally {
      setLoadingEmployees(false)
    }
  }

  useEffect(() => {
    loadEmployees()
  }, [])

  const filteredEmployees = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    if (!keyword) return employees

    return employees.filter((item) => {
      const content = [
        item.EmployeeID,
        item.FullName,
        item.Email,
        item.DepartmentName,
        item.PositionName,
        item.Status,
      ]
        .join(' ')
        .toLowerCase()

      return content.includes(keyword)
    })
  }, [employees, search])

  const selectedCount = selectAll ? employees.length : selectedIds.length

  function updateOption(name, checked) {
    setForm((prev) => ({
      ...prev,
      [name]: checked,
    }))
    setResult(null)
  }

  function toggleSelectAll(checked) {
    setSelectAll(checked)
    setSelectedIds(checked ? employees.map((item) => Number(item.EmployeeID)) : [])
    setResult(null)
  }

  function toggleEmployee(employeeId, checked) {
    const id = Number(employeeId)
    setSelectAll(false)
    setSelectedIds((prev) => {
      if (checked) {
        return Array.from(new Set([...prev, id]))
      }
      return prev.filter((item) => Number(item) !== id)
    })
    setResult(null)
  }

  async function onSend() {
    setError(null)
    setResult(null)

    if (!form.sendProfile && !form.sendAttendance && !form.sendSalary) {
      setError(new Error('Vui lòng chọn ít nhất một loại nội dung cần gửi.'))
      return
    }

    if (!selectAll && selectedIds.length === 0) {
      setError(new Error('Vui lòng chọn ít nhất một nhân viên để gửi email.'))
      return
    }

    const contentLabels = []
    if (form.sendProfile) contentLabels.push('thông tin cá nhân')
    if (form.sendAttendance) contentLabels.push('bảng chấm công')
    if (form.sendSalary) contentLabels.push('bảng lương')

    const ok = window.confirm(
      `Bạn có chắc muốn gửi ${contentLabels.join(', ')} tháng ${form.month} cho ${selectedCount} nhân viên không?`,
    )

    if (!ok) return

    setSending(true)

    try {
      const payload = {
        month: form.month,
        selectAll,
        employeeIds: selectAll ? [] : selectedIds,
        sendProfile: form.sendProfile,
        sendAttendance: form.sendAttendance,
        sendSalary: form.sendSalary,
      }

      const res = await sendSalaryEmails(payload)
      setResult(res)
    } catch (e) {
      setError(e)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="mail-page">
      <div className="mail-header-card">
        <div>
          <h2>Gửi email cho nhân viên</h2>
          <p>
            Chọn nhân viên và loại nội dung cần gửi: thông tin cá nhân, bảng chấm công hoặc bảng lương.
          </p>
        </div>

        <button className="mail-refresh-btn" onClick={loadEmployees} disabled={loadingEmployees || sending}>
          <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> Làm mới
        </button>
      </div>

      {loadingEmployees ? <Loading text="Đang tải danh sách nhân viên..." /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loadingEmployees ? (
        <>
          <div className="mail-config-card">
            <div className="mail-section-title">1. Nội dung email</div>

            <div className="mail-options-grid">
              <label className="mail-option-card">
                <input
                  type="checkbox"
                  checked={form.sendProfile}
                  onChange={(e) => updateOption('sendProfile', e.target.checked)}
                />
                <div>
                  <strong>Gửi thông tin cá nhân</strong>
                  <span>Họ tên, email, số điện thoại, phòng ban, chức vụ, trạng thái.</span>
                </div>
              </label>

              <label className="mail-option-card">
                <input
                  type="checkbox"
                  checked={form.sendAttendance}
                  onChange={(e) => updateOption('sendAttendance', e.target.checked)}
                />
                <div>
                  <strong>Gửi bảng chấm công</strong>
                  <span>Công chuẩn, công thực tế, tổng giờ làm, ngày nghỉ, ghi chú.</span>
                </div>
              </label>

              <label className="mail-option-card">
                <input
                  type="checkbox"
                  checked={form.sendSalary}
                  onChange={(e) => updateOption('sendSalary', e.target.checked)}
                />
                <div>
                  <strong>Gửi bảng lương</strong>
                  <span>Lương cơ bản, thưởng, khấu trừ và lương thực nhận.</span>
                </div>
              </label>
            </div>

            <div className="mail-form-row">
              <label className="mail-field">
                <span>Tháng áp dụng</span>
                <input
                  type="month"
                  value={form.month}
                  onChange={(e) => {
                    setForm((prev) => ({ ...prev, month: e.target.value }))
                    setResult(null)
                  }}
                />
              </label>

              <div className="mail-summary-box">
                <span>Số nhân viên sẽ gửi</span>
                <strong>{selectedCount}</strong>
              </div>
            </div>
          </div>

          <div className="mail-employees-card">
            <div className="mail-table-header">
              <div>
                <h3>2. Chọn nhân viên nhận email</h3>
                <p>Có thể gửi cho tất cả hoặc chọn một vài nhân viên cụ thể.</p>
              </div>

              <label className="mail-select-all">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={(e) => toggleSelectAll(e.target.checked)}
                />
                <span>Gửi tất cả</span>
              </label>
            </div>

            <div className="mail-search-row">
              <input
                type="text"
                placeholder="Tìm theo tên, email, phòng ban, chức vụ..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="mail-table-wrapper">
              <table className="mail-table">
                <thead>
                  <tr>
                    <th>Chọn</th>
                    <th>STT</th>
                    <th>Họ và tên</th>
                    <th>Email</th>
                    <th>Phòng ban</th>
                    <th>Chức vụ</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredEmployees.length > 0 ? (
                    filteredEmployees.map((item, index) => {
                      const checked = selectAll || selectedIds.includes(Number(item.EmployeeID))

                      return (
                        <tr key={item.EmployeeID}>
                          <td>
                            <input
                              type="checkbox"
                              checked={checked}
                              disabled={selectAll}
                              onChange={(e) => toggleEmployee(item.EmployeeID, e.target.checked)}
                            />
                          </td>
                          <td>{index + 1}</td>
                          <td><strong>{item.FullName}</strong></td>
                          <td>{item.Email || 'Chưa có email'}</td>
                          <td>{item.DepartmentName || 'Chưa có'}</td>
                          <td>{item.PositionName || 'Chưa có'}</td>
                          <td><span className="mail-status-badge">{item.Status || 'Chưa có'}</span></td>
                        </tr>
                      )
                    })
                  ) : (
                    <tr>
                      <td colSpan="7" className="mail-empty-row">
                        Không tìm thấy nhân viên phù hợp
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mail-action-card">
            <div>
              <span>Loại nội dung đã chọn</span>
              <strong>
                {[
                  form.sendProfile ? 'Thông tin cá nhân' : null,
                  form.sendAttendance ? 'Bảng chấm công' : null,
                  form.sendSalary ? 'Bảng lương' : null,
                ].filter(Boolean).join(' + ') || 'Chưa chọn'}
              </strong>
            </div>

            <button className="mail-send-btn" onClick={onSend} disabled={sending || selectedCount === 0}>
              <Send size={17} strokeWidth={1.8} aria-hidden="true" /> {sending ? 'Đang gửi...' : 'Gửi email'}
            </button>
          </div>

          {sending ? <Loading text="Đang gửi email..." /> : null}

          {result ? (
            <div className="mail-result-card">
              <div className="mail-result-header">
                <h3>Kết quả gửi email</h3>
                <span>{result?.message || 'Hoàn tất'}</span>
              </div>

              <div className="mail-result-grid">
                <div>
                  <span>Đã gửi</span>
                  <strong>{result?.sent_count ?? 0}</strong>
                </div>
                <div>
                  <span>Tổng đã chọn</span>
                  <strong>{result?.total_selected ?? 0}</strong>
                </div>
                <div>
                  <span>Tháng</span>
                  <strong>{result?.month}</strong>
                </div>
              </div>

              {Array.isArray(result?.failed) && result.failed.length > 0 ? (
                <div className="mail-warning-box">
                  <strong>Có {result.failed.length} email gửi thất bại.</strong>
                  <div className="mail-result-list">
                    {result.failed.map((item) => (
                      <div key={item.EmployeeID}>
                        <b>{item.FullName}</b> - {item.Email || 'Chưa có email'}
                        <br />
                        <span>Lý do: {item.reason || 'Gửi email thất bại'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {Array.isArray(result?.skipped) && result.skipped.length > 0 ? (
                <div className="mail-warning-box">
                  <strong>Có {result.skipped.length} nhân viên bị bỏ qua vì chưa có email.</strong>
                  <div className="mail-result-list">
                    {result.skipped.map((item) => (
                      <div key={item.EmployeeID}>
                        <b>{item.FullName}</b> - {item.reason}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {Array.isArray(result?.results) && result.results.length > 0 ? (
                <div className="mail-success-box">
                  <strong>Danh sách gửi thành công</strong>
                  <div className="mail-result-list">
                    {result.results.map((item) => (
                      <div key={item.EmployeeID}>
                        <b>{item.FullName}</b> - {item.Email}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
