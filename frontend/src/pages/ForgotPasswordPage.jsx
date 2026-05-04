import { useState } from 'react'
import { MailPlus, LogIn } from '../components/LineIcons'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/authApi'
import '../styles/AuthPages.css'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')

    try {
      const res = await forgotPassword({ email })
      setMessage(res.message || 'Nếu email tồn tại trong hệ thống, liên kết đặt lại mật khẩu đã được gửi.')
    } catch (err) {
      setError(err.message || 'Không thể gửi email đặt lại mật khẩu')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-brand">HR & Payroll</div>
        <h1>Quên mật khẩu</h1>
        <p>Nhập email tài khoản. Hệ thống sẽ gửi liên kết đặt lại mật khẩu qua Gmail.</p>

        {error ? <div className="auth-error">{error}</div> : null}
        {message ? <div className="auth-success">{message}</div> : null}

        <label>
          <span>Email tài khoản</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@gmail.com"
            required
          />
        </label>

        <button type="submit" disabled={loading}>
          <MailPlus size={18} strokeWidth={1.8} aria-hidden="true" /> {loading ? 'Đang gửi email...' : 'Gửi liên kết đặt lại'}
        </button>

        <div className="auth-hint">
          Đã nhớ mật khẩu? <Link to="/login"><LogIn size={15} strokeWidth={1.8} aria-hidden="true" /> Quay lại đăng nhập</Link>
        </div>
      </form>
    </div>
  )
}
