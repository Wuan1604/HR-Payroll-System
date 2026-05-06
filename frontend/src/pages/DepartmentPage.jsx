import { useEffect, useState } from 'react'
import { Plus, Save, Pencil, Trash2, Building2 } from '../components/LineIcons'
import { showDepartments, addDepartment, updateDepartment, deleteDepartment } from '../api/humanApi'
import Loading from '../components/Loading'
import '../styles/DepartmentPage.css'

export default function DepartmentPage() {
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(false)
  const [newDeptName, setNewDeptName] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editName, setEditName] = useState('')

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const data = await showDepartments()
      setDepartments(Array.isArray(data) ? data : [])
    } catch (e) {
      alert('Lỗi load dữ liệu')
    }
    setLoading(false)
  }

  async function handleAdd() {
    const value = newDeptName.trim()
    if (loading || !value) return

    setLoading(true)
    try {
      await addDepartment(value)
      setNewDeptName('')
      await loadData()
    } catch (e) {
      alert(e.message || 'Không thể thêm phòng ban')
      setLoading(false)
    }
  }

  async function handleDelete(id) {
    if (window.confirm('Bạn có chắc chắn muốn xóa phòng ban này?')) {
      try {
        await deleteDepartment(id)
        loadData()
      } catch (e) {
        alert(e.message)
      }
    }
  }

  async function handleUpdate(id) {
    const value = editName.trim()
    if (!value) return
    await updateDepartment({ DepartmentID: id, DepartmentName: value })
    setEditingId(null)
    loadData()
  }

  return (
    <div className="department-page">
      <div className="department-card">
        <div className="department-header">
          <div>
            <h2 className="page-title-with-icon"><Building2 size={24} strokeWidth={1.8} aria-hidden="true" /> Quản lý phòng ban</h2>
            <p>Quản lý danh sách phòng ban đang sử dụng trong hệ thống nhân sự.</p>
          </div>
        </div>

        <div className="department-add-row">
          <input
            className="department-input"
            placeholder="Tên phòng ban mới..."
            value={newDeptName}
            onChange={(e) => setNewDeptName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAdd()
            }}
          />
          <button className="department-btn primary" onClick={handleAdd} disabled={loading || !newDeptName.trim()}>
            <Plus size={16} strokeWidth={1.8} aria-hidden="true" /> Thêm mới
          </button>
        </div>

        {loading ? <Loading /> : (
          <div className="department-table-wrap">
            <table className="department-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Tên phòng ban</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {departments.length === 0 ? (
                  <tr><td colSpan="3" className="department-empty">Chưa có phòng ban.</td></tr>
                ) : departments.map((dept) => (
                  <tr key={dept.DepartmentID}>
                    <td>{dept.DepartmentID}</td>
                    <td>
                      {editingId === dept.DepartmentID ? (
                        <input
                          className="department-input edit"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleUpdate(dept.DepartmentID)
                          }}
                        />
                      ) : dept.DepartmentName}
                    </td>
                    <td>
                      <div className="department-actions">
                        {editingId === dept.DepartmentID ? (
                          <button className="department-action-btn" onClick={() => handleUpdate(dept.DepartmentID)}>
                            <Save size={15} strokeWidth={1.8} aria-hidden="true" /> Lưu
                          </button>
                        ) : (
                          <button className="department-action-btn" onClick={() => {
                            setEditingId(dept.DepartmentID)
                            setEditName(dept.DepartmentName)
                          }}>
                            <Pencil size={15} strokeWidth={1.8} aria-hidden="true" /> Sửa
                          </button>
                        )}
                        <button className="department-action-btn danger" onClick={() => handleDelete(dept.DepartmentID)}>
                          <Trash2 size={15} strokeWidth={1.8} aria-hidden="true" /> Xóa
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
