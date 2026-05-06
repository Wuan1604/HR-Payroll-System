import { useEffect, useMemo, useState } from 'react'
import { FileText, RefreshCw, X } from '../components/LineIcons'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getSalaries, downloadSalaryReport } from '../api/payrollApi'
import '../styles/PayrollSalariesPage.css'

function formatMoney(value) {
  return Number(value || 0).toLocaleString('en-US') + ' VNĐ'
}

function formatDate(value) {
  if (!value) return 'Chưa có'
  return String(value).slice(0, 10)
}

function getCurrentMonth() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}

function getMonthFromDate(value) {
  if (!value) return ''
  return String(value).slice(0, 7)
}

export default function PayrollSalariesPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [rows, setRows] = useState([])
  const [selectedMonth, setSelectedMonth] = useState('')
  const [selectedDepartmentId, setSelectedDepartmentId] = useState('')
  const [selectedReportEmployeeId, setSelectedReportEmployeeId] = useState('')
  const [exporting, setExporting] = useState(false)

  async function load() {
    setLoading(true)
    setError(null)

    try {
      const res = await getSalaries()
      const data = Array.isArray(res) ? res : []
      setRows(data)

      if (!selectedMonth) {
        const currentMonth = getCurrentMonth()
        const hasCurrentMonth = data.some(
          (item) => getMonthFromDate(item.SalaryMonth) === currentMonth
        )

        if (hasCurrentMonth) {
          setSelectedMonth(currentMonth)
        } else if (data.length > 0) {
          setSelectedMonth(getMonthFromDate(data[0].SalaryMonth))
        }
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

  const departmentOptions = useMemo(() => {
    const map = new Map()
    rows.forEach((item) => {
      const id = item.DepartmentID != null ? String(item.DepartmentID) : ''
      const name = item.DepartmentName || 'Chưa có'
      if (!map.has(id)) map.set(id, name)
    })
    return Array.from(map.entries()).map(([DepartmentID, DepartmentName]) => ({ DepartmentID, DepartmentName }))
  }, [rows])

  const employeeOptions = useMemo(() => {
    const map = new Map()
    rows.forEach((item) => {
      if (item.EmployeeID) map.set(item.EmployeeID, item.FullName || 'NV ' + item.EmployeeID)
    })
    return Array.from(map.entries()).map(([EmployeeID, FullName]) => ({ EmployeeID, FullName }))
  }, [rows])

  const selectedDepartmentName = useMemo(() => {
    const option = departmentOptions.find((item) => item.DepartmentID === selectedDepartmentId)
    return option ? option.DepartmentName : 'Tất cả phòng ban'
  }, [departmentOptions, selectedDepartmentId])

  async function handleExportSalaryReport(format = 'pdf') {
    setExporting(true)
    setError(null)
    try {
      const blob = await downloadSalaryReport({
        month: selectedMonth,
        department_id: selectedDepartmentId,
        employee_id: selectedReportEmployeeId,
        format,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const employeePart = selectedReportEmployeeId ? '-nv-' + selectedReportEmployeeId : ''
      const departmentPart = selectedDepartmentId ? '-pb-' + selectedDepartmentId : ''
      a.href = url
      a.download = 'bao-cao-luong-' + (selectedMonth || 'tat-ca') + departmentPart + employeePart + '.' + format
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e)
    } finally {
      setExporting(false)
    }
  }

  const availableMonths = useMemo(() => {
    const months = new Set()

    rows.forEach((item) => {
      const month = getMonthFromDate(item.SalaryMonth)
      if (month) months.add(month)
    })

    return Array.from(months).sort((a, b) => b.localeCompare(a))
  }, [rows])

  const filteredRows = useMemo(() => {
    return rows.filter((item) => {
      if (selectedMonth && getMonthFromDate(item.SalaryMonth) !== selectedMonth) {
        return false
      }
      if (selectedDepartmentId && String(item.DepartmentID || '') !== selectedDepartmentId) {
        return false
      }
      return true
    })
  }, [rows, selectedMonth, selectedDepartmentId])

  const summary = useMemo(() => {
    return filteredRows.reduce(
      (total, item) => {
        total.employeeCount += 1
        total.baseSalary += Number(item.BaseSalary || 0)
        total.bonus += Number(item.Bonus || 0)
        total.deductions += Number(item.Deductions || 0)
        total.netSalary += Number(item.NetSalary || 0)
        return total
      },
      {
        employeeCount: 0,
        baseSalary: 0,
        bonus: 0,
        deductions: 0,
        netSalary: 0,
      }
    )
  }, [filteredRows])

  return (
    <div className="payroll-page">
      <div className="payroll-header-card">
        <div>
          <h2 className="page-title-with-icon"><FileText size={24} strokeWidth={1.8} aria-hidden="true" /> Bảng lương</h2>
          <p>
            Theo dõi bảng lương nhân viên theo từng tháng.
          </p>
        </div>

        <button className="payroll-refresh-btn" onClick={load} disabled={loading}>
          <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> Làm mới
        </button>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loading && !error ? (
        <>
                    <div className="payroll-filter-card">
            <label className="payroll-field">
              <span>Lọc theo tháng lương</span>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
              />
            </label>

            <label className="payroll-field">
              <span>Chọn nhanh tháng có dữ liệu</span>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
              >
                <option value="">Tất cả tháng</option>
                {availableMonths.map((month) => (
                  <option key={month} value={month}>
                    {month}
                  </option>
                ))}
              </select>
            </label>

            <label className="payroll-field">
              <span>Lọc theo phòng ban</span>
              <select
                value={selectedDepartmentId}
                onChange={(e) => setSelectedDepartmentId(e.target.value)}
              >
                <option value="">Tất cả phòng ban</option>
                {departmentOptions.map((dept) => (
                  <option key={dept.DepartmentID} value={dept.DepartmentID}>
                    {dept.DepartmentName}
                  </option>
                ))}
              </select>
            </label>

            <label className="payroll-field">
              <span>Nhân viên khi xuất báo cáo</span>
              <select
                value={selectedReportEmployeeId}
                onChange={(e) => setSelectedReportEmployeeId(e.target.value)}
              >
                <option value="">Toàn bộ nhân viên</option>
                {employeeOptions.map((emp) => (
                  <option key={emp.EmployeeID} value={emp.EmployeeID}>
                    {emp.EmployeeID} - {emp.FullName}
                  </option>
                ))}
              </select>
            </label>

            <button
              className="payroll-clear-btn"
              type="button"
              onClick={() => handleExportSalaryReport('pdf')}
              disabled={exporting}
            >
              <FileText size={16} strokeWidth={1.8} aria-hidden="true" /> {exporting ? 'Đang xuất...' : 'Xuất PDF bảng lương'}
            </button>

            <button
              className="payroll-clear-btn"
              type="button"
              onClick={() => {
                setSelectedMonth('')
                setSelectedDepartmentId('')
                setSelectedReportEmployeeId('')
              }}
            >
              <X size={15} strokeWidth={1.8} aria-hidden="true" /> Xem tất cả
            </button>
          </div>


          <div className="payroll-summary-grid">
            <div className="payroll-summary-card">
              <span>Số nhân viên</span>
              <strong>{summary.employeeCount}</strong>
            </div>

            <div className="payroll-summary-card">
              <span>Tổng lương cơ bản</span>
              <strong>{formatMoney(summary.baseSalary)}</strong>
            </div>

            <div className="payroll-summary-card">
              <span>Tổng thưởng</span>
              <strong>{formatMoney(summary.bonus)}</strong>
            </div>

            <div className="payroll-summary-card">
              <span>Tổng khấu trừ</span>
              <strong>{formatMoney(summary.deductions)}</strong>
            </div>

            <div className="payroll-summary-card highlight">
              <span>Tổng thực nhận</span>
              <strong>{formatMoney(summary.netSalary)}</strong>
            </div>
          </div>

          <div className="payroll-table-card">
            <div className="payroll-table-header">
              <h3>
                {selectedMonth
                  ? `Bảng lương tháng ${selectedMonth}`
                  : 'Tất cả bảng lương'}
              </h3>
              <span>
                {selectedDepartmentId ? `Phòng ban: ${selectedDepartmentName} • ` : ''}
                {filteredRows.length} bản ghi
              </span>
            </div>

            <div className="payroll-table-wrapper">
              <table className="payroll-table">
                <thead>
                  <tr>
                    <th>Mã NV</th>
                    <th>Họ và tên</th>
                    <th>Phòng ban</th>
                    <th>Chức vụ</th>
                    <th>Tháng lương</th>
                    <th>Lương cơ bản</th>
                    <th>Thưởng</th>
                    <th>Khấu trừ</th>
                    <th>Thực nhận</th>
                    <th>Trạng thái</th>
                    <th>Ngày tạo</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredRows.length > 0 ? (
                    filteredRows.map((item) => (
                      <tr key={`${item.EmployeeID}-${item.SalaryID}-${item.SalaryMonth}`}>
                        <td>{item.EmployeeID}</td>
                        <td>{item.FullName || 'Chưa có'}</td>
                        <td>{item.DepartmentName || 'Chưa có'}</td>
                        <td>{item.PositionName || 'Chưa có'}</td>
                        <td>{formatDate(item.SalaryMonth)}</td>
                        <td>{formatMoney(item.BaseSalary)}</td>
                        <td>{formatMoney(item.Bonus)}</td>
                        <td>{formatMoney(item.Deductions)}</td>
                        <td>
                          <strong>{formatMoney(item.NetSalary)}</strong>
                        </td>
                        <td>{item.Status || 'Chưa có'}</td>
                        <td>{formatDate(item.CreatedAt)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="11" className="payroll-empty-row">
                        Không có dữ liệu bảng lương cho tháng này
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
