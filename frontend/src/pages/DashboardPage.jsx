import { useEffect, useState } from 'react'
import Loading from '../components/Loading'
import ApiError from '../components/ApiError'
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
        <h2 style={{ marginTop: 0 }}>Tổng quan hệ thống</h2>
        <div className="row">
          <button className="btn" onClick={load} disabled={loading}>
            Làm mới dữ liệu
          </button>
        </div>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}

      {data ? (
        <>
          {/* Hàng 1: Các con số tổng quát */}
          <div className="row" style={{ gap: 16, marginBottom: 16 }}>
            <div className="card" style={{ flex: 1, textAlign: 'center', borderTop: '4px solid #007bff' }}>
              <div className="muted">👥 Nhân viên</div>
              <div style={{ fontSize: 32, fontWeight: 700 }}>{data.total_employees}</div>
            </div>
            <div className="card" style={{ flex: 1, textAlign: 'center', borderTop: '4px solid #28a745' }}>
              <div className="muted">🏢 Phòng ban</div>
              <div style={{ fontSize: 32, fontWeight: 700 }}>{data.total_departments}</div>
            </div>
            <div className="card" style={{ flex: 1, textAlign: 'center', borderTop: '4px solid #ffc107' }}>
              <div className="muted">🎖️ Chức vụ</div>
              <div style={{ fontSize: 32, fontWeight: 700 }}>{data.total_positions}</div>
            </div>
          </div>

          {/* Hàng 2: Chi tiết trạng thái nhân sự */}
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Trạng thái nhân sự</h3>
            <div className="row" style={{ gap: 40, flexWrap: 'wrap' }}>
              {Object.entries(data.status_distribution || {}).map(([status, count]) => (
                <div key={status}>
                  <div className="muted">{status || 'Chưa xác định'}</div>
                  <div style={{ fontSize: 24, fontWeight: 600 }}>{count}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}

      <div className="card muted" style={{ textAlign: 'center', padding: '40px' }}>
         Dữ liệu được lấy từ sự kết hợp giữa SQL Server (Nhân sự) và MySQL (Lương).
      </div>
    </div>
  )
}