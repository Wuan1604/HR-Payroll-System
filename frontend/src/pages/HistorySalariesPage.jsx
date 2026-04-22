import { useEffect, useMemo, useState } from 'react'
import ApiError from '../components/ApiError'
import DataTable from '../components/DataTable'
import Loading from '../components/Loading'
import { getSalaries, historySalaries } from '../api/payrollApi'

export default function HistorySalariesPage() {
  const [loadingEmployees, setLoadingEmployees] = useState(true)
  const [loadingHistory, setLoadingHistory] = useState(false)
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
    return Array.from(seen.values()).sort((a, b) => Number(a.EmployeeID) - Number(b.EmployeeID))
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedEmployeeID) {
      loadHistory(selectedEmployeeID)
    }
  }, [selectedEmployeeID])

  const employee = data?.employee
  const latest = data?.latest_salary
  const history = Array.isArray(data?.history) ? data.history : []

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Lịch sử lương nhân viên</h2>
        <div className="muted">
          Chọn nhân viên để xem toàn bộ các bản ghi lương theo tháng.
        </div>
      </div>

      {loadingEmployees ? <Loading text="Đang tải danh sách nhân viên..." /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loadingEmployees ? (
        <div className="card">
          <div className="row">
            <label style={{ display: 'flex', flexDirection: 'column', minWidth: 320 }}>
              <span className="muted" style={{ marginBottom: 6 }}>
                Chọn nhân viên
              </span>
              <select
                className="input"
                value={selectedEmployeeID}
                onChange={(e) => setSelectedEmployeeID(e.target.value)}
              >
                {employeeOptions.map((item) => (
                  <option key={item.EmployeeID} value={item.EmployeeID}>
                    {item.EmployeeID} - {item.FullName}
                  </option>
                ))}
              </select>
            </label>

            <button className="btn" onClick={() => loadHistory(selectedEmployeeID)} disabled={loadingHistory || !selectedEmployeeID}>
              {loadingHistory ? 'Đang tải...' : 'Xem lịch sử'}
            </button>
          </div>
        </div>
      ) : null}

      {employee ? (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Thông tin nhân viên</h3>
          <div className="row" style={{ gap: 24, flexWrap: 'wrap' }}>
            <div><span className="muted">Mã NV:</span> <b>{employee.EmployeeID}</b></div>
            <div><span className="muted">Họ tên:</span> <b>{employee.FullName}</b></div>
            <div><span className="muted">Phòng ban:</span> <b>{employee.DepartmentName || 'N/A'}</b></div>
            <div><span className="muted">Chức vụ:</span> <b>{employee.PositionName || 'N/A'}</b></div>
            <div><span className="muted">Trạng thái:</span> <b>{employee.Status || 'N/A'}</b></div>
          </div>
        </div>
      ) : null}

      {latest ? (
        <div className="row" style={{ gap: 16, marginBottom: 16 }}>
          <div className="card" style={{ flex: 1 }}>
            <div className="muted">Tháng lương gần nhất</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{latest.SalaryMonth}</div>
          </div>
          <div className="card" style={{ flex: 1 }}>
            <div className="muted">Lương thực nhận gần nhất</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{latest.NetSalary}</div>
          </div>
          <div className="card" style={{ flex: 1 }}>
            <div className="muted">Số bản ghi lương</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{data?.count ?? 0}</div>
          </div>
        </div>
      ) : null}

      {loadingHistory ? <Loading text="Đang tải lịch sử lương..." /> : null}
      {!loadingHistory && !error ? <DataTable rows={history} title="Danh sách lịch sử lương" /> : null}
    </div>
  )
}
