import { useState } from 'react'
import { RefreshCw } from '../components/LineIcons'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { apiFetch } from '../api/http'

export default function NotImplementedPage({ apiPath }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function handleTry() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await apiFetch(apiPath)
      setResult(data)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Chưa có/Chưa hỗ trợ</h2>
        <div className="muted">
          Route này đang ở trạng thái UI placeholder. Backend của bạn có thể
          chưa có endpoint tương ứng.
        </div>
        {apiPath && apiPath !== 'N/A' ? (
          <div className="muted" style={{ marginTop: 10 }}>
            Endpoint: <code>{apiPath}</code>
          </div>
        ) : null}
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn" onClick={handleTry} disabled={loading}>
            Thử gọi API
          </button>
        </div>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}
      {result ? (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Kết quả trả về</h3>
          <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  )
}

