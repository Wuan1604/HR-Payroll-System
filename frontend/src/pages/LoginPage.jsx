import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { apiFetch } from '../api/http'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const fromPath = useMemo(
    () => location.state?.from || '/',
    [location.state?.from],
  )

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  async function onSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      setMessage('Đăng nhập thành công')
      navigate(fromPath, { replace: true })
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Đăng nhập</h2>
      <div className="muted">
        Tài khoản admin được cấu hình hardcoded trong backend qua `.env`.
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}
      {message ? <div className="muted">{message}</div> : null}

      <form onSubmit={onSubmit} style={{ marginTop: 14 }}>
        <div className="row">
          <label style={{ display: 'flex', flexDirection: 'column' }}>
            <span className="muted" style={{ marginBottom: 6 }}>
              Username
            </span>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column' }}>
            <span className="muted" style={{ marginBottom: 6 }}>
              Password
            </span>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
        </div>

        <div className="row" style={{ marginTop: 14 }}>
          <button className="btn" type="submit" disabled={loading}>
            Đăng nhập
          </button>
        </div>
      </form>
    </div>
  )
}

