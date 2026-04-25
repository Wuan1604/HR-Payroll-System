import { Link } from 'react-router-dom'

export default function UnauthorizedPage() {
  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Không có quyền truy cập</h2>
      <p>Bạn không được phân quyền sử dụng chức năng này.</p>
      <Link className="btn" to="/">Quay về tổng quan</Link>
    </div>
  )
}
