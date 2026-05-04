import { useState } from 'react'
import { LogIn, UserRoundPlus, KeyRound } from '../components/LineIcons'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { login } from '../api/authApi'
import { getCurrentUser, saveAuth } from '../utils/auth'
import '../styles/AuthPages.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ account: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const currentUser = getCurrentUser()
  if (currentUser) {
    return <Navigate to={currentUser.Role === 'Employee' ? '/my-profile' : '/'} replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await login({ email: form.account, username: form.account, password: form.password })
      saveAuth(res.token, res.user)
      navigate(res.user?.Role === 'Employee' ? '/my-profile' : '/', { replace: true })
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
          <LogIn size={18} strokeWidth={1.8} aria-hidden="true" /> {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>

        <div className="auth-hint auth-hint--split">
          <span>Chưa có tài khoản? <Link to="/register"><UserRoundPlus size={15} strokeWidth={1.8} aria-hidden="true" /> Đăng ký tài khoản</Link></span>
          <Link to="/forgot-password"><KeyRound size={15} strokeWidth={1.8} aria-hidden="true" /> Quên mật khẩu?</Link>
        </div>
      </form>
    </div>
  )
}
