import { useEffect, useState } from 'react'
import ApiError from '../components/ApiError'
import DataTable from '../components/DataTable'
import Loading from '../components/Loading'
import { getTimekeeping } from '../api/payrollApi'

export default function TimekeepingPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [rows, setRows] = useState([])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await getTimekeeping()
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

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Chấm công</h2>
        <div className="row">
          <button className="btn" onClick={load} disabled={loading}>
            Làm mới
          </button>
          <div className="muted">
            Endpoint: <code>/api/payroll/timekeeping</code>
          </div>
        </div>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}
      {!loading && !error ? <DataTable rows={rows} /> : null}
    </div>
  )
}

