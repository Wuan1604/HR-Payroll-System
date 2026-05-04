import { useMemo, useState } from 'react'
import { LockKeyhole, LogIn } from '../components/LineIcons'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api/authApi'
import '../styles/AuthPages.css'

export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = useMemo(() => searchParams.get('token') || '', [searchParams])
  const [form, setForm] = useState({ password: '', confirmPassword: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')

    try {
      const res = await resetPassword({ token, password: form.password, confirmPassword: form.confirmPassword })
      setMessage(res.message || 'Đặt lại mật khẩu thành công.')
      setTimeout(() => navigate('/login', { replace: true }), 1200)
    } catch (err) {
      setError(err.message || 'Không thể đặt lại mật khẩu')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-brand">HR & Payroll</div>
        <h1>Đặt lại mật khẩu</h1>
        <p>Tạo mật khẩu mới cho tài khoản của bạn.</p>

        {!token ? <div className="auth-error">Liên kết đặt lại mật khẩu không hợp lệ hoặc thiếu mã token.</div> : null}
        {error ? <div className="auth-error">{error}</div> : null}
        {message ? <div className="auth-success">{message}</div> : null}

        <label>
          <span>Mật khẩu mới</span>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            placeholder="Tối thiểu 6 ký tự"
            minLength={6}
            required
          />
        </label>

        <label>
          <span>Xác nhận mật khẩu mới</span>
          <input
            type="password"
            value={form.confirmPassword}
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
            placeholder="Nhập lại mật khẩu mới"
            minLength={6}
            required
          />
        </label>

        <button type="submit" disabled={loading || !token}>
          <LockKeyhole size={18} strokeWidth={1.8} aria-hidden="true" /> {loading ? 'Đang cập nhật...' : 'Đặt lại mật khẩu'}
        </button>

        <div className="auth-hint">
          <Link to="/login"><LogIn size={15} strokeWidth={1.8} aria-hidden="true" /> Quay lại đăng nhập</Link>
        </div>
      </form>
    </div>
  )
}
