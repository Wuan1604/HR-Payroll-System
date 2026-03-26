import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import Loading from './Loading'

export default function RequireAuth({ children }) {
  const location = useLocation()
  const [checking, setChecking] = useState(true)
  const [authed, setAuthed] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function check() {
      setChecking(true)
      setError(null)
      try {
        const res = await fetch('/api/auth/me', { credentials: 'include' })
        if (cancelled) return
        if (res.ok) {
          const data = await res.json()
          setAuthed(Boolean(data?.authenticated))
        } else {
          // 401: chưa login
          setAuthed(false)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e)
          setAuthed(false)
        }
      } finally {
        if (!cancelled) setChecking(false)
      }
    }
    check()
    return () => {
      cancelled = true
    }
  }, [])

  if (checking) return <Loading text="Đang kiểm tra đăng nhập..." />
  if (error) {
    return (
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Lỗi xác thực</h2>
        <div className="error">{String(error?.message || error)}</div>
      </div>
    )
  }

  if (!authed) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}

