import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { addEmployee } from '../api/humanApi'

const fields = [
  { key: 'FullName', label: 'Họ tên' },
  { key: 'DateOfBirth', label: 'Ngày sinh', type: 'date' },
  { key: 'Gender', label: 'Giới tính' },
  { key: 'PhoneNumber', label: 'SĐT' },
  { key: 'Email', label: 'Email' },
  { key: 'HireDate', label: 'Ngày vào làm', type: 'date' },
  { key: 'DepartmentID', label: 'Mã phòng ban' },
  { key: 'PositionID', label: 'Mã chức vụ' },
  { key: 'Status', label: 'Trạng thái' },
]

export default function AddEmployeePage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  const initial = useMemo(
    () => ({
      FullName: '',
      DateOfBirth: '',
      Gender: '',
      PhoneNumber: '',
      Email: '',
      HireDate: '',
      DepartmentID: '',
      PositionID: '',
      Status: '',
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
      // Điều hướng sang danh sách
      navigate('/employees-page')
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
          Gọi POST <code>/api/human/add-employee</code>. Backend sẽ đồng bộ sang
          MySQL để quản lý lương.
        </div>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}
      {message ? <div className="card">{message}</div> : null}

      <form className="card" onSubmit={onSubmit}>
        <div className="row">
          {fields.map((f) => (
            <label key={f.key} style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="muted" style={{ marginBottom: 6 }}>
                {f.label}
              </span>
              <input
                className="input"
                type={f.type || 'text'}
                value={form[f.key]}
                onChange={(e) => update(f.key, e.target.value)}
              />
            </label>
          ))}
        </div>
        <div className="row" style={{ marginTop: 14 }}>
          <button className="btn" type="submit" disabled={loading}>
            Lưu nhân viên
          </button>
          <button
            className="btn"
            type="button"
            onClick={() => navigate('/employees-page')}
            disabled={loading}
          >
            Quay lại
          </button>
        </div>
      </form>
    </div>
  )
}

