import { useEffect, useState } from 'react'
import Loading from '../components/Loading'
import ApiError from '../components/ApiError'
import DataTable from '../components/DataTable'
import { getReportHuman } from '../api/humanApi'

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await getReportHuman()
      setData(res)
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
        <h2 style={{ marginTop: 0 }}>Tổng quan</h2>
        <div className="row">
          <button className="btn" onClick={load} disabled={loading}>
            Làm mới
          </button>
          <div className="muted">
            Backend hiện tại có endpoint `report-human`.
          </div>
        </div>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}

      {data ? (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Thống kê nhân sự</h3>
          <div className="row" style={{ gap: 24 }}>
            <div>
              <div className="muted">Tổng số nhân viên</div>
              <div style={{ fontSize: 28, fontWeight: 700 }}>
                {data?.total_employees ?? ''}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Placeholder để sau này có biểu đồ/diagram */}
      {!loading && !error ? <DataTable rows={[]} title="Biểu đồ (chưa có)" /> : null}
    </div>
  )
}

