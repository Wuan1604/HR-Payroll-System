import { useEffect, useState } from 'react'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getMyProfile, updateMyProfile } from '../api/humanApi'
import '../styles/EmployeeProfilePage.css'

export default function EmployeeProfilePage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState('')
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({
    FullName: '',
    DateOfBirth: '',
    Gender: '',
    PhoneNumber: '',
    Email: '',
  })

  async function loadProfile() {
    setLoading(true)
    setError(null)
    setMessage('')

    try {
      const res = await getMyProfile()
      const data = res?.employee || res
      setProfile(data)
      setForm({
        FullName: data?.FullName || '',
        DateOfBirth: data?.DateOfBirth || '',
        Gender: data?.Gender || '',
        PhoneNumber: data?.PhoneNumber || '',
        Email: data?.Email || '',
      })
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProfile()
  }, [])

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    setMessage('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setMessage('')

    try {
      const res = await updateMyProfile(form)
      const data = res?.employee || res
      setProfile(data)
      setForm({
        FullName: data?.FullName || '',
        DateOfBirth: data?.DateOfBirth || '',
        Gender: data?.Gender || '',
        PhoneNumber: data?.PhoneNumber || '',
        Email: data?.Email || '',
      })
      try {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
        localStorage.setItem('user', JSON.stringify({
          ...currentUser,
          FullName: data?.FullName || currentUser.FullName,
          Email: data?.Email || currentUser.Email,
        }))
      } catch {}
      setMessage(res?.message || 'Cập nhật thông tin cá nhân thành công.')
    } catch (e) {
      setError(e)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="profile-page">
      <div className="profile-header-card">
        <div>
          <h2>Thông tin cá nhân</h2>
          <p>Employee có thể xem và cập nhật thông tin cá nhân của chính mình.</p>
        </div>

        <button className="profile-refresh-btn" onClick={loadProfile} disabled={loading || saving}>
          Làm mới
        </button>
      </div>

      {loading ? <Loading text="Đang tải thông tin cá nhân..." /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loading && !error ? (
        <div className="profile-content-grid">
          <div className="profile-info-card">
            <h3>Hồ sơ nhân viên</h3>

            <div className="profile-avatar">
              {(profile?.FullName || 'NV').slice(0, 1).toUpperCase()}
            </div>

            <div className="profile-name">{profile?.FullName || 'Chưa có tên'}</div>
            <div className="profile-role">Employee</div>

            <div className="profile-info-list">
              <div>
                <span>Mã nhân viên</span>
                <strong>{profile?.EmployeeID}</strong>
              </div>

              <div>
                <span>Phòng ban</span>
                <strong>{profile?.DepartmentName || 'Chưa có'}</strong>
              </div>

              <div>
                <span>Chức vụ</span>
                <strong>{profile?.PositionName || 'Chưa có'}</strong>
              </div>

              <div>
                <span>Trạng thái</span>
                <strong>{profile?.Status || 'Chưa có'}</strong>
              </div>
            </div>
          </div>

          <form className="profile-form-card" onSubmit={handleSubmit}>
            <h3>Cập nhật thông tin</h3>

            <div className="profile-form-grid">
              <label className="profile-field">
                <span>Họ và tên</span>
                <input name="FullName" value={form.FullName} onChange={handleChange} placeholder="Nhập họ và tên" />
              </label>

              <label className="profile-field">
                <span>Ngày sinh</span>
                <input type="date" name="DateOfBirth" value={form.DateOfBirth} onChange={handleChange} />
              </label>

              <label className="profile-field">
                <span>Giới tính</span>
                <select name="Gender" value={form.Gender} onChange={handleChange}>
                  <option value="">-- Chọn giới tính --</option>
                  <option value="Nam">Nam</option>
                  <option value="Nữ">Nữ</option>
                  <option value="Khác">Khác</option>
                </select>
              </label>

              <label className="profile-field">
                <span>Số điện thoại</span>
                <input name="PhoneNumber" value={form.PhoneNumber} onChange={handleChange} placeholder="Nhập số điện thoại" />
              </label>

              <label className="profile-field profile-field-full">
                <span>Email</span>
                <input type="email" name="Email" value={form.Email} onChange={handleChange} placeholder="Nhập email" />
              </label>
            </div>

            <div className="profile-note">
              Bạn chỉ được cập nhật thông tin cá nhân cơ bản. Phòng ban, chức vụ và trạng thái do Admin quản lý.
            </div>

            <div className="profile-actions">
              <button className="profile-save-btn" type="submit" disabled={saving}>
                {saving ? 'Đang lưu...' : 'Lưu thông tin'}
              </button>
            </div>

            {message ? <div className="profile-success-message">{message}</div> : null}
          </form>
        </div>
      ) : null}
    </div>
  )
}
