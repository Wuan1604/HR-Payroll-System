import { useState } from 'react'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { sendSalaryEmails } from '../api/payrollApi'

export default function SendSalaryEmailsPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function onSend() {
    const ok = window.confirm(
      'Bạn có chắc muốn gửi email phiếu lương cho các nhân viên không? (NetSalary > 0)',
    )
    if (!ok) return

    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await sendSalaryEmails()
      setResult(res)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Gửi email phiếu lương</h2>
        <div className="muted">
          Gọi GET <code>/api/payroll/send-salary-emails</code>.
        </div>
      </div>

      <div className="card">
        <button className="btn" onClick={onSend} disabled={loading}>
          {loading ? 'Đang gửi...' : 'Gửi email'}
        </button>
      </div>

      {loading ? <Loading text="Đang gửi email..." /> : null}
      {error ? <ApiError error={error} /> : null}

      {result ? (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Kết quả</h3>
          <div className="muted">{result?.message || 'OK'}</div>
          <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap', marginTop: 10 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  )
}

