import { useState } from 'react'
import { UserRoundPlus, LogIn } from '../components/LineIcons'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/authApi'
import '../styles/AuthPages.css'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ EmployeeID: '', FullName: '', Email: '', Username: '', Password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const res = await register({ ...form, EmployeeID: form.EmployeeID || null })
      setMessage(res.message || 'Đăng ký thành công')
      setTimeout(() => navigate('/login'), 900)
    } catch (err) {
      setError(err.message || 'Đăng ký thất bại')
    } finally {
      setLoading(false)
    }
  }

  function change(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-brand">HR & Payroll</div>
        <h1>Đăng ký tài khoản</h1>
        <p>Tài khoản đăng ký mới mặc định là Employee. Admin có thể đổi quyền trong Quản lý tài khoản.</p>
        {error ? <div className="auth-error">{error}</div> : null}
        {message ? <div className="users-success">{message}</div> : null}
        <label><span>EmployeeID</span><input name="EmployeeID" value={form.EmployeeID} onChange={change} placeholder="Mã nhân viên nếu có" /></label>
        <label><span>Họ và tên</span><input name="FullName" value={form.FullName} onChange={change} required /></label>
        <label><span>Email</span><input name="Email" value={form.Email} onChange={change} required /></label>
        <label><span>Username</span><input name="Username" value={form.Username} onChange={change} required /></label>
        <label><span>Mật khẩu</span><input name="Password" type="password" value={form.Password} onChange={change} required /></label>
        <button type="submit" disabled={loading}><UserRoundPlus size={18} strokeWidth={1.8} aria-hidden="true" /> {loading ? 'Đang đăng ký...' : 'Đăng ký'}</button>
        <div className="auth-hint">Đã có tài khoản? <Link to="/login"><LogIn size={15} strokeWidth={1.8} aria-hidden="true" /> Đăng nhập</Link></div>
      </form>
    </div>
  )
}
