import { useEffect, useMemo, useRef, useState } from 'react'
import { FileText, RefreshCw, Search } from '../components/LineIcons'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getSalaries, historySalaries } from '../api/payrollApi'
import '../styles/HistorySalariesPage.css'

function formatMoney(value) {
  return Number(value || 0).toLocaleString('en-US') + ' VNĐ'
}

function formatDate(value) {
  if (!value) return 'Chưa có'
  return String(value).slice(0, 10)
}

function formatFileName(value) {
  return String(value || '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[\\/:*?"<>|]/g, '')
}

export default function HistorySalariesPage() {
  const pdfRef = useRef(null)

  const [loadingEmployees, setLoadingEmployees] = useState(true)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [exportingPdf, setExportingPdf] = useState(false)
  const [error, setError] = useState(null)
  const [salaryRows, setSalaryRows] = useState([])
  const [selectedEmployeeID, setSelectedEmployeeID] = useState('')
  const [data, setData] = useState(null)

  const employeeOptions = useMemo(() => {
    const seen = new Map()

    for (const row of salaryRows) {
      const id = String(row?.EmployeeID ?? '')
      if (!id || seen.has(id)) continue

      seen.set(id, {
        EmployeeID: id,
        FullName: row?.FullName || `Nhân viên ${id}`,
      })
    }

    return Array.from(seen.values()).sort(
      (a, b) => Number(a.EmployeeID) - Number(b.EmployeeID)
    )
  }, [salaryRows])

  async function loadEmployees() {
    setLoadingEmployees(true)
    setError(null)

    try {
      const res = await getSalaries()
      const rows = Array.isArray(res) ? res : []

      setSalaryRows(rows)

      if (rows.length > 0 && !selectedEmployeeID) {
        setSelectedEmployeeID(String(rows[0].EmployeeID))
      }
    } catch (e) {
      setError(e)
    } finally {
      setLoadingEmployees(false)
    }
  }

  async function loadHistory(employeeId) {
    if (!employeeId) return

    setLoadingHistory(true)
    setError(null)

    try {
      const res = await historySalaries(employeeId)
      setData(res)
    } catch (e) {
      setError(e)
      setData(null)
    } finally {
      setLoadingHistory(false)
    }
  }

  useEffect(() => {
    loadEmployees()
  
  }, [])

  useEffect(() => {
    if (selectedEmployeeID) {
      loadHistory(selectedEmployeeID)
    }
  }, [selectedEmployeeID])

  const employee = data?.employee
  const latest = data?.latest_salary
  const history = Array.isArray(data?.history) ? data.history : []

  async function exportSalaryHistoryPDF() {
    if (!pdfRef.current || !employee || history.length === 0) {
      alert('Vui lòng chọn nhân viên có lịch sử lương trước khi xuất PDF.')
      return
    }

    setExportingPdf(true)
    setError(null)

    const pdfElement = pdfRef.current
    pdfElement.classList.add('is-exporting-pdf')

    try {
      await new Promise((resolve) => setTimeout(resolve, 80))

      const canvas = await html2canvas(pdfElement, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        windowWidth: pdfElement.scrollWidth,
      })

      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('p', 'mm', 'a4')
      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const imgWidth = pageWidth
      const imgHeight = (canvas.height * imgWidth) / canvas.width

      let heightLeft = imgHeight
      let position = 0

      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      while (heightLeft > 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }

      const fileName = formatFileName(
        `lich-su-luong-${employee.EmployeeID}-${employee.FullName || 'nhan-vien'}`
      )

      pdf.save(`${fileName || 'lich-su-luong'}.pdf`)
    } catch (e) {
      console.error(e)
      alert('Xuất PDF thất bại. Vui lòng thử lại.')
    } finally {
      pdfElement.classList.remove('is-exporting-pdf')
      setExportingPdf(false)
    }
  }

  return (
    <div className="history-salary-page">
      <div className="history-header-card">
        <div>
          <h2>Lịch sử lương nhân viên</h2>
          <p>Chọn nhân viên để xem toàn bộ lịch sử lương theo từng tháng.</p>
        </div>

        <div className="history-header-actions">
          <button
            className="history-export-btn"
            onClick={exportSalaryHistoryPDF}
            disabled={exportingPdf || loadingHistory || !employee || history.length === 0}
          >
            <FileText size={16} strokeWidth={1.8} aria-hidden="true" /> {exportingPdf ? 'Đang xuất PDF...' : 'Xuất PDF'}
          </button>

          <button
            className="history-refresh-btn"
            onClick={() => loadHistory(selectedEmployeeID)}
            disabled={loadingHistory || !selectedEmployeeID}
          >
            <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> {loadingHistory ? 'Đang tải...' : 'Làm mới'}
          </button>
        </div>
      </div>

      {loadingEmployees ? (
        <Loading text="Đang tải danh sách nhân viên..." />
      ) : null}

      {error ? <ApiError error={error} /> : null}

      {!loadingEmployees ? (
        <div className="history-filter-card">
          <label className="history-field">
            <span>Chọn nhân viên</span>
            <select
              value={selectedEmployeeID}
              onChange={(e) => setSelectedEmployeeID(e.target.value)}
            >
              {employeeOptions.length === 0 ? (
                <option value="">Chưa có nhân viên trong payroll</option>
              ) : null}

              {employeeOptions.map((item) => (
                <option key={item.EmployeeID} value={item.EmployeeID}>
                  {item.EmployeeID} - {item.FullName}
                </option>
              ))}
            </select>
          </label>

          <button
            className="history-search-btn"
            onClick={() => loadHistory(selectedEmployeeID)}
            disabled={loadingHistory || !selectedEmployeeID}
          >
            <Search size={16} strokeWidth={1.8} aria-hidden="true" /> {loadingHistory ? 'Đang tải...' : 'Xem lịch sử'}
          </button>
        </div>
      ) : null}

      <div ref={pdfRef} className="salary-history-pdf-area">
        <div className="pdf-title-block">
          <h1>PHIẾU LỊCH SỬ LƯƠNG NHÂN VIÊN</h1>
          <p>Hệ thống HR & Payroll</p>
          {employee ? (
            <p>
              Nhân viên: {employee.EmployeeID} - {employee.FullName}
            </p>
          ) : null}
        </div>

        {employee ? (
          <div className="employee-history-card">
            <h3>Thông tin nhân viên</h3>

            <div className="employee-history-grid">
              <div>
                <span>Mã nhân viên</span>
                <strong>{employee.EmployeeID}</strong>
              </div>

              <div>
                <span>Họ và tên</span>
                <strong>{employee.FullName}</strong>
              </div>

              <div>
                <span>Phòng ban</span>
                <strong>{employee.DepartmentName || 'Chưa có'}</strong>
              </div>

              <div>
                <span>Chức vụ</span>
                <strong>{employee.PositionName || 'Chưa có'}</strong>
              </div>

              <div>
                <span>Trạng thái</span>
                <strong>{employee.Status || 'Chưa có'}</strong>
              </div>
            </div>
          </div>
        ) : null}

        {latest ? (
          <div className="salary-stat-grid">
            <div className="salary-stat-card">
              <span>Tháng lương gần nhất</span>
              <strong>{formatDate(latest.SalaryMonth)}</strong>
            </div>

            <div className="salary-stat-card highlight">
              <span>Lương thực nhận gần nhất</span>
              <strong>{formatMoney(latest.NetSalary)}</strong>
            </div>

            <div className="salary-stat-card">
              <span>Số bản ghi lương</span>
              <strong>{data?.count ?? 0}</strong>
            </div>
          </div>
        ) : employee && !loadingHistory ? (
          <div className="history-empty-card">
            Nhân viên này chưa có lịch sử lương.
          </div>
        ) : null}

        {loadingHistory ? (
          <Loading text="Đang tải lịch sử lương..." />
        ) : null}

        {!loadingHistory && !error ? (
          <div className="history-table-card">
            <div className="history-table-header">
              <h3>Danh sách lịch sử lương</h3>
              <span>{history.length} bản ghi</span>
            </div>

            <div className="history-table-wrapper">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Mã lương</th>
                    <th>Tháng lương</th>
                    <th>Lương cơ bản</th>
                    <th>Thưởng</th>
                    <th>Khấu trừ</th>
                    <th>Thực nhận</th>
                    <th>Ngày tạo</th>
                  </tr>
                </thead>

                <tbody>
                  {history.length > 0 ? (
                    history.map((item) => (
                      <tr key={item.SalaryID}>
                        <td>{item.SalaryID}</td>
                        <td>{formatDate(item.SalaryMonth)}</td>
                        <td>{formatMoney(item.BaseSalary)}</td>
                        <td>{formatMoney(item.Bonus)}</td>
                        <td>{formatMoney(item.Deductions)}</td>
                        <td>
                          <strong>{formatMoney(item.NetSalary)}</strong>
                        </td>
                        <td>{formatDate(item.CreatedAt)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="history-empty-row">
                        Chưa có dữ liệu lịch sử lương
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
