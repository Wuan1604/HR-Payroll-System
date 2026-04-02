import { useMemo, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { addEmployee, getDepartments, getPositions } from '../api/humanApi' // Giả sử bạn đã khai báo 2 hàm này

export default function AddEmployeePage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  // --- 1. State để lưu danh sách đổ vào Dropdown ---
  const [departments, setDepartments] = useState([])
  const [positions, setPositions] = useState([])

  // --- 2. useEffect để load dữ liệu từ 2 nguồn DB khi mở trang ---
  useEffect(() => {
    async function loadData() {
      try {
        // Gọi song song 2 API từ Backend (Human.py)
        const [deptRes, posRes] = await Promise.all([
          getDepartments(), 
          getPositions()
        ])
        setDepartments(deptRes)
        setPositions(posRes)

        // Cập nhật giá trị mặc định cho form sau khi load xong data
        if (deptRes.length > 0) update('DepartmentID', deptRes[0].id)
        if (posRes.length > 0) update('PositionID', posRes[0].id)
      } catch (e) {
        setError(e)
      }
    }
    loadData()
  }, [])

  // --- 3. Định nghĩa cấu trúc các trường ---
  const fields = [
    { key: 'FullName', label: 'Họ tên' },
    { key: 'DateOfBirth', label: 'Ngày sinh', type: 'date' },
    { key: 'Gender', label: 'Giới tính', type: 'select', options: ['Nam', 'Nữ', 'Khác'] },
    { key: 'PhoneNumber', label: 'SĐT' },
    { key: 'Email', label: 'Email', type: 'email' },
    { key: 'HireDate', label: 'Ngày vào làm', type: 'date' },
    // Chọn từ danh sách lấy từ MySQL
    { key: 'DepartmentID', label: 'Phòng ban', type: 'db_select', data: departments },
    // Chọn từ danh sách lấy từ SQL Server
    { key: 'PositionID', label: 'Chức vụ', type: 'db_select', data: positions },
    { 
      key: 'Status', 
      label: 'Trạng thái', 
      type: 'select', 
      options: ['Đang làm việc', 'Thử việc', 'Đã nghỉ việc', 'Tạm hoãn'] 
    },
  ]

  const initial = useMemo(
    () => ({
      FullName: '',
      DateOfBirth: '',
      Gender: 'Nam',
      PhoneNumber: '',
      Email: '',
      HireDate: new Date().toISOString().split('T')[0],
      DepartmentID: '',
      PositionID: '',
      Status: 'Đang làm việc',
    }),
    [],
  )

  const [form, setForm] = useState(initial)

  function update(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      await addEmployee(form)
      setMessage('Thêm mới và đồng bộ thành công.')
      setTimeout(() => navigate('/employees-page'), 1500)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Thêm nhân viên</h2>
        <div className="muted">
          Thông tin sẽ được lưu đồng thời vào SSMS (Chức vụ) và Navicat (Phòng ban).
        </div>
      </div>

      {(loading && !departments.length) ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}
      {message ? <div className="card" style={{ color: 'green', fontWeight: 'bold' }}>{message}</div> : null}

      <form className="card" onSubmit={onSubmit}>
        <div className="row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {fields.map((f) => (
            <label key={f.key} style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="muted" style={{ marginBottom: 6 }}>
                {f.label}
              </span>
              
              {/* RENDER SELECT TĨNH (Gender, Status) */}
              {f.type === 'select' && (
                <select
                  className="input"
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                >
                  {f.options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                </select>
              )}

              {/* RENDER SELECT TỪ DATABASE (Phòng ban, Chức vụ) */}
              {f.type === 'db_select' && (
                <select
                  className="input"
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                >
                  {f.data.map(item => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              )}

              {/* RENDER INPUT THƯỜNG */}
              {!['select', 'db_select'].includes(f.type) && (
                <input
                  className="input"
                  type={f.type || 'text'}
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                  required={f.key === 'FullName'}
                />
              )}
            </label>
          ))}
        </div>

        <div className="row" style={{ marginTop: 20, display: 'flex', gap: '10px' }}>
          <button className="btn" type="submit" disabled={loading} style={{ backgroundColor: '#007bff', color: 'white' }}>
            Lưu nhân viên
          </button>
          <button className="btn" type="button" onClick={() => navigate('/employees-page')}>
            Quay lại
          </button>
        </div>
      </form>
    </div>
  )
}