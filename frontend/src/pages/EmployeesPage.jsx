import { useEffect, useState } from 'react'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getEmployees, deleteEmployee, updateEmployee } from '../api/humanApi'
import '../styles/EmployeesPage.css'
import { getRole } from '../utils/auth'

export default function EmployeesPage() {
  const role = getRole()
  const canManageEmployees = role === 'Admin' || role === 'Manager'
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [rows, setRows] = useState([])
  const [editingEmployee, setEditingEmployee] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await getEmployees()
      setRows(res?.employees || [])
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleDelete = async (id) => {
    if (!window.confirm('Bạn có chắc muốn xóa nhân viên này không?')) return

    try {
      await deleteEmployee(id)
      alert('Xóa thành công')
      load()
    } catch (err) {
      alert('Xóa thất bại')
    }
  }

  const handleEdit = (emp) => {
    setEditingEmployee({ ...emp })
  }

  const handleUpdate = async () => {
    try {
      await updateEmployee(editingEmployee)
      alert('Cập nhật thành công')
      setEditingEmployee(null)
      load()
    } catch (err) {
      alert(err?.message || err?.error || 'Cập nhật thất bại')
    }
  }

  return (
    <div className="employees-page">
      <div className="employees-header card">
        <div>
          <h2>Danh sách nhân viên</h2>
          <p>{canManageEmployees ? 'Quản lý, chỉnh sửa và xóa thông tin nhân viên' : 'Xem danh sách nhân viên'}</p>
        </div>

        <button className="btn-refresh" onClick={load} disabled={loading}>
          Làm mới
        </button>
      </div>

      {loading && <Loading />}
      {error && <ApiError error={error} />}

      {!loading && !error && (
        <div className="employees-table-wrapper">
          <table className="employees-table">
            <thead>
              <tr>
                <th>STT</th>
                <th>Họ tên</th>
                <th>Email</th>
                <th>Phòng ban</th>
                <th>Chức vụ</th>
                <th>Trạng thái</th>
                {canManageEmployees ? <th>Hành động</th> : null}
              </tr>
            </thead>

            <tbody>
              {rows.map((emp, index) => (
                <tr key={emp.EmployeeID}>
                  <td>{index + 1}</td>
                  <td className="employee-name">{emp.FullName}</td>
                  <td>{emp.Email}</td>
                  <td>{emp.DepartmentName}</td>
                  <td>{emp.PositionName}</td>
                  <td>
                    <span className="status-badge">{emp.Status}</span>
                  </td>
                  {canManageEmployees ? (
                    <td>
                      <div className="action-buttons">
                        <button className="btn-edit" onClick={() => handleEdit(emp)}>
                          Sửa
                        </button>
                        <button className="btn-delete" onClick={() => handleDelete(emp.EmployeeID)}>
                          Xóa
                        </button>
                      </div>
                    </td>
                  ) : null}
                </tr>
              ))}

              {rows.length === 0 && (
                <tr>
                  <td colSpan={canManageEmployees ? 7 : 6} className="empty-row">
                    Không có dữ liệu nhân viên
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {canManageEmployees && editingEmployee && (
        <div className="modal-overlay">
          <div className="employee-modal">
            <div className="modal-header">
              <h3>Sửa nhân viên</h3>
              <button className="modal-close" onClick={() => setEditingEmployee(null)}>
                ×
              </button>
            </div>

            <div className="form-group">
              <label>Họ tên</label>
              <input
                value={editingEmployee.FullName || ''}
                onChange={(e) =>
                  setEditingEmployee({ ...editingEmployee, FullName: e.target.value })
                }
              />
            </div>

            <div className="form-group">
              <label>Email</label>
              <input
                value={editingEmployee.Email || ''}
                onChange={(e) =>
                  setEditingEmployee({ ...editingEmployee, Email: e.target.value })
                }
              />
            </div>

            <div className="form-group">
              <label>Số điện thoại</label>
              <input
                value={editingEmployee.PhoneNumber || ''}
                onChange={(e) =>
                  setEditingEmployee({ ...editingEmployee, PhoneNumber: e.target.value })
                }
              />
            </div>

            <div className="form-group">
              <label>Trạng thái</label>
              <select
                value={editingEmployee.Status || 'Đang làm việc'}
                onChange={(e) =>
                  setEditingEmployee({ ...editingEmployee, Status: e.target.value })
                }
              >
                <option>Đang làm việc</option>
                <option>Thử việc</option>
                <option>Đã nghỉ việc</option>
                <option>Tạm hoãn</option>
              </select>
            </div>

            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setEditingEmployee(null)}>
                Hủy
              </button>
              <button className="btn-save" onClick={handleUpdate}>
                Lưu thay đổi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}