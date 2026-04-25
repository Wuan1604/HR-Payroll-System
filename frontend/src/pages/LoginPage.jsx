import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { login } from '../api/authApi'
import { getCurrentUser, saveAuth } from '../utils/auth'
import '../styles/AuthPages.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ account: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (getCurrentUser()) return <Navigate to="/" replace />

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await login({ email: form.account, username: form.account, password: form.password })
      saveAuth(res.token, res.user)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'Đăng nhập thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-brand">HR & Payroll</div>
        <h1>Đăng nhập hệ thống</h1>
        <p>Đăng nhập để sử dụng chức năng theo quyền Admin, Manager hoặc Employee.</p>

        {error ? <div className="auth-error">{error}</div> : null}

        <label>
          <span>Email hoặc tên đăng nhập</span>
          <input
            value={form.account}
            onChange={(e) => setForm({ ...form, account: e.target.value })}
            placeholder="admin@gmail.com hoặc admin"
          />
        </label>

        <label>
          <span>Mật khẩu</span>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            placeholder="Nhập mật khẩu"
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>

        <div className="auth-hint">
          Tài khoản mẫu: admin/admin123, manager/manager123, employee/employee123<br />
          Chưa có tài khoản? <Link to="/register">Đăng ký Employee</Link>
        </div>
      </form>
    </div>
  )
}
