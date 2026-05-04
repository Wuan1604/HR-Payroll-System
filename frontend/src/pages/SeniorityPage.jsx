import { useEffect, useMemo, useState } from 'react'
import { RefreshCw, Search, X } from '../components/LineIcons'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getAttendanceSeniority } from '../api/payrollApi'
import { getRole } from '../utils/auth'
import '../styles/SeniorityPage.css'

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-US')
}

function formatDate(value) {
  if (!value) return 'Chưa có'
  return String(value).slice(0, 10)
}

export default function SeniorityPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('')
  const [search, setSearch] = useState('')

  const role = getRole()
  const isEmployee = role === 'Employee'

  async function load(employeeId = selectedEmployeeId) {
    setLoading(true)
    setError(null)

    try {
      const res = await getAttendanceSeniority(isEmployee ? '' : employeeId)
      setData(res)
    } catch (e) {
      setError(e)
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const employees = Array.isArray(data?.employees) ? data.employees : []

  const employeeOptions = useMemo(() => {
    return employees.map((item) => ({
      EmployeeID: item.EmployeeID,
      FullName: item.FullName,
    }))
  }, [employees])

  const filteredEmployees = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    if (!keyword) return employees

    return employees.filter((item) => {
      const content = [
        item.EmployeeID,
        item.FullName,
        item.DepartmentName,
        item.PositionName,
        item.Status,
        item.SeniorityText,
        item.TotalValidDays,
      ]
        .join(' ')
        .toLowerCase()

      return content.includes(keyword)
    })
  }, [employees, search])

  const selectedEmployee = employees[0]
  const summary = data?.summary || {}

  return (
    <div className="seniority-page">
      <div className="seniority-header-card">
        <div>
          <h2>{isEmployee ? 'Thâm niên của tôi' : 'Thâm niên làm việc nhân viên'}</h2>
          <p>
            Tính thâm niên theo công đã chấm: tổng công đã làm cộng với ngày nghỉ phép được chấm. Quy đổi 26 công = 1 tháng.
          </p>
        </div>

        <button className="seniority-refresh-btn" onClick={() => load()} disabled={loading}>
          <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> {loading ? 'Đang tải...' : 'Làm mới'}
        </button>
      </div>

      {error ? <ApiError error={error} /> : null}
      {loading ? <Loading text="Đang tải dữ liệu thâm niên..." /> : null}

      {!loading && !error ? (
        <>
          {!isEmployee ? (
            <div className="seniority-filter-card">
              <label className="seniority-field">
                <span>Chọn nhân viên</span>
                <select
                  value={selectedEmployeeId}
                  onChange={(e) => setSelectedEmployeeId(e.target.value)}
                >
                  <option value="">Tất cả nhân viên</option>
                  {employeeOptions.map((emp) => (
                    <option key={emp.EmployeeID} value={emp.EmployeeID}>
                      {emp.EmployeeID} - {emp.FullName}
                    </option>
                  ))}
                </select>
              </label>

              <label className="seniority-field search-field">
                <span><Search size={16} strokeWidth={1.8} aria-hidden="true" /> Tìm kiếm trong danh sách</span>
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Tìm theo tên, phòng ban, chức vụ..."
                />
              </label>

              <button
                className="seniority-search-btn"
                type="button"
                onClick={() => load(selectedEmployeeId)}
                disabled={loading}
              >
                Xem thâm niên
              </button>

              <button
                className="seniority-clear-btn"
                type="button"
                onClick={() => {
                  setSelectedEmployeeId('')
                  setSearch('')
                  load('')
                }}
              >
                Xem tất cả
              </button>
            </div>
          ) : null}

          <div className="seniority-summary-grid">
            <div className="seniority-summary-card">
              <span>Số nhân viên</span>
              <strong>{formatNumber(summary.EmployeeCount)}</strong>
            </div>
            <div className="seniority-summary-card highlight">
              <span>Tổng công đã làm</span>
              <strong>{formatNumber(summary.TotalWorkDays)} công</strong>
            </div>
            <div className="seniority-summary-card">
              <span>Nghỉ không phép</span>
              <strong>{formatNumber(summary.TotalAbsentDays)} ngày</strong>
            </div>
            <div className="seniority-summary-card">
              <span>Nghỉ phép được tính</span>
              <strong>{formatNumber(summary.TotalLeaveDays)} ngày</strong>
            </div>
            <div className="seniority-summary-card">
              <span>Tổng công tính thâm niên</span>
              <strong>{formatNumber(summary.TotalValidDays)} công</strong>
            </div>
          </div>

          {isEmployee && selectedEmployee ? (
            <div className="seniority-profile-card">
              <div>
                <span>Nhân viên</span>
                <strong>{selectedEmployee.FullName}</strong>
              </div>
              <div>
                <span>Thâm niên quy đổi</span>
                <strong>{selectedEmployee.SeniorityText}</strong>
              </div>
              <div>
                <span>Công đã làm</span>
                <strong>{formatNumber(selectedEmployee.TotalWorkDays)} công</strong>
              </div>
              <div>
                <span>Nghỉ phép được tính</span>
                <strong>{formatNumber(selectedEmployee.TotalLeaveDays)} ngày</strong>
              </div>
              <div>
                <span>Tổng giờ làm</span>
                <strong>{formatNumber(selectedEmployee.TotalHours)} giờ</strong>
              </div>
            </div>
          ) : null}

          <div className="seniority-table-card">
            <div className="seniority-table-header">
              <h3>{isEmployee ? 'Chi tiết thâm niên của tôi' : 'Danh sách thâm niên nhân viên'}</h3>
              <span>{filteredEmployees.length} bản ghi</span>
            </div>

            <div className="seniority-table-wrapper">
              <table className="seniority-table">
                <thead>
                  <tr>
                    <th>STT</th>
                    <th>Họ và tên</th>
                    <th>Phòng ban</th>
                    <th>Chức vụ</th>
                    <th>Chấm công đầu tiên</th>
                    <th>Thâm niên quy đổi</th>
                    <th>Công đã làm</th>
                    <th>Nghỉ phép được tính</th>
                    <th>Tổng công tính thâm niên</th>
                    <th>Tổng giờ làm</th>
                    <th>Nghỉ không phép</th>
                    <th>Thiếu công</th>
                    <th>Trạng thái</th>
                    <th>Gợi ý tăng lương</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredEmployees.length > 0 ? (
                    filteredEmployees.map((item, index) => (
                      <tr key={item.EmployeeID}>
                        <td>{index + 1}</td>
                        <td><strong>{item.FullName}</strong></td>
                        <td>{item.DepartmentName || 'Chưa có'}</td>
                        <td>{item.PositionName || 'Chưa có'}</td>
                        <td>{formatDate(item.FirstAttendanceDate)}</td>
                        <td><span className="seniority-badge">{item.SeniorityText}</span></td>
                        <td>{formatNumber(item.TotalWorkDays)} công</td>
                        <td>{formatNumber(item.TotalLeaveDays)} ngày</td>
                        <td>{formatNumber(item.TotalValidDays)} công</td>
                        <td>{formatNumber(item.TotalHours)} giờ</td>
                        <td>{formatNumber(item.TotalAbsentDays)} ngày</td>
                        <td>{formatNumber(item.RecordedShortDays)} ngày</td>
                        <td><span className="seniority-status">{item.Status || 'Chưa có'}</span></td>
                        <td>{item.SalaryRaiseSuggestion?.Eligible ? <span className="seniority-raise-badge">{item.SalaryRaiseSuggestion.Text}</span> : <span className="seniority-muted">Chưa đủ điều kiện</span>}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="14" className="seniority-empty-row">
                        Chưa có dữ liệu chấm công để tính thâm niên
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
