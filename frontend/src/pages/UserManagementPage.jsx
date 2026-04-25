import { useEffect, useState } from 'react'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { createUser, deleteUser, getUsers, updateUser } from '../api/authApi'
import '../styles/UserManagementPage.css'

const emptyForm = {
  UserID: null,
  EmployeeID: '',
  FullName: '',
  Email: '',
  Username: '',
  Password: '',
  RoleName: 'Employee',
  Status: 'Active',
}

export default function UserManagementPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [users, setUsers] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [message, setMessage] = useState('')

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await getUsers()
      setUsers(Array.isArray(res) ? res : [])
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    setMessage('')
  }

  function editUser(user) {
    setForm({
      UserID: user.UserID,
      EmployeeID: user.EmployeeID || '',
      FullName: user.FullName || '',
      Email: user.Email || '',
      Username: user.Username || '',
      Password: '',
      RoleName: user.RoleName || 'Employee',
      Status: user.Status || 'Active',
    })
    setMessage('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setMessage('')

    try {
      const payload = {
        EmployeeID: form.EmployeeID || null,
        FullName: form.FullName,
        Email: form.Email,
        Username: form.Username,
        RoleName: form.RoleName,
        Status: form.Status,
      }
      if (form.Password) payload.Password = form.Password

      if (form.UserID) {
        await updateUser(form.UserID, payload)
        setMessage('Cập nhật tài khoản thành công')
      } else {
        await createUser({ ...payload, Password: form.Password })
        setMessage('Tạo tài khoản thành công')
      }

      setForm(emptyForm)
      await load()
    } catch (e) {
      setError(e)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(userId) {
    if (!window.confirm('Bạn có chắc muốn xóa tài khoản này không?')) return
    try {
      await deleteUser(userId)
      await load()
    } catch (e) {
      setError(e)
    }
  }

  return (
    <div className="users-page">
      <div className="users-header-card">
        <div>
          <h2>Quản lý tài khoản truy cập</h2>
          <p>Admin có thể thêm, sửa, xóa tài khoản và phân quyền Admin / Manager / Employee.</p>
        </div>
        <button className="btn" onClick={load} disabled={loading}>Làm mới</button>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loading ? (
        <>
          <form className="users-form-card" onSubmit={handleSubmit}>
            <h3>{form.UserID ? 'Cập nhật tài khoản' : 'Tạo tài khoản mới'}</h3>
            <div className="users-form-grid">
              <label><span>EmployeeID</span><input name="EmployeeID" value={form.EmployeeID} onChange={handleChange} placeholder="Có thể để trống" /></label>
              <label><span>Họ tên</span><input name="FullName" value={form.FullName} onChange={handleChange} required /></label>
              <label><span>Email</span><input name="Email" value={form.Email} onChange={handleChange} required /></label>
              <label><span>Username</span><input name="Username" value={form.Username} onChange={handleChange} required /></label>
              <label><span>Mật khẩu</span><input name="Password" type="password" value={form.Password} onChange={handleChange} placeholder={form.UserID ? 'Để trống nếu không đổi' : 'Nhập mật khẩu'} required={!form.UserID} /></label>
              <label><span>Quyền</span><select name="RoleName" value={form.RoleName} onChange={handleChange}><option>Admin</option><option>Manager</option><option>Employee</option></select></label>
              <label><span>Trạng thái</span><select name="Status" value={form.Status} onChange={handleChange}><option>Active</option><option>Locked</option><option>Inactive</option></select></label>
            </div>
            <div className="users-form-actions">
              <button className="btn" type="submit" disabled={saving}>{saving ? 'Đang lưu...' : form.UserID ? 'Lưu thay đổi' : 'Tạo tài khoản'}</button>
              {form.UserID ? <button type="button" className="btn-secondary" onClick={() => setForm(emptyForm)}>Hủy sửa</button> : null}
            </div>
            {message ? <div className="users-success">{message}</div> : null}
          </form>

          <div className="users-table-card">
            <div className="users-table-header"><h3>Danh sách tài khoản</h3><span>{users.length} tài khoản</span></div>
            <div className="users-table-wrapper">
              <table className="users-table">
                <thead><tr><th>ID</th><th>EmployeeID</th><th>Họ tên</th><th>Email</th><th>Username</th><th>Quyền</th><th>Trạng thái</th><th>Đăng nhập gần nhất</th><th>Hành động</th></tr></thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.UserID}>
                      <td>{u.UserID}</td><td>{u.EmployeeID || '-'}</td><td>{u.FullName}</td><td>{u.Email}</td><td>{u.Username}</td><td><b>{u.RoleName}</b></td><td>{u.Status}</td><td>{u.LastLogin || 'Chưa có'}</td>
                      <td><div className="users-actions"><button onClick={() => editUser(u)}>Sửa</button><button className="danger" onClick={() => handleDelete(u.UserID)}>Xóa</button></div></td>
                    </tr>
                  ))}
                  {users.length === 0 ? <tr><td colSpan="9" className="users-empty">Chưa có tài khoản</td></tr> : null}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
