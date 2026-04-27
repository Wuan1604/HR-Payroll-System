import { BrowserRouter, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import './App.css'

import DashboardPage from './pages/DashboardPage'
import EmployeesPage from './pages/EmployeesPage'
import AddEmployeePage from './pages/AddEmployeePage'
import PayrollSalariesPage from './pages/PayrollSalariesPage'
import TimekeepingPage from './pages/TimekeepingPage'
import UpdateSalaryPage from './pages/UpdateSalaryPage'
import SendSalaryEmailsPage from './pages/SendSalaryEmailsPage'
import NotImplementedPage from './pages/NotImplementedPage'
import RequireAuth from './components/RequireAuth'
import DepartmentPage from './pages/DepartmentPage'
import PositionPage from './pages/PositionPage'
import HistorySalariesPage from './pages/HistorySalariesPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import UnauthorizedPage from './pages/UnauthorizedPage'
import UserManagementPage from './pages/UserManagementPage'
import EmployeeProfilePage from './pages/EmployeeProfilePage'
import SeniorityPage from './pages/SeniorityPage'
import { logout } from './api/authApi'
import { clearAuth, getCurrentUser, getRole } from './utils/auth'

const ADMIN = ['Admin']
const ADMIN_MANAGER = ['Admin', 'Manager']
const ALL_ROLES = ['Admin', 'Manager', 'Employee']

function RoleLink({ to, children, roles }) {
  const role = getRole()
  if (roles?.length && !roles.includes(role)) return null
  return <NavLink to={to} className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>{children}</NavLink>
}

function Sidebar() {
  const navigate = useNavigate()
  const user = getCurrentUser()
  const role = user?.Role

  async function handleLogout() {
    try { await logout() } catch {}
    clearAuth()
    navigate('/login', { replace: true })
  }

  if (!user) return null

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">HR & Payroll</div>
      <div className="sidebar__user">
        <strong>{user.FullName}</strong>
        <span>{role}</span>
      </div>

      <nav className="sidebar__nav">
        <RoleLink to="/" roles={ADMIN_MANAGER}>Tổng quan</RoleLink>
        <RoleLink to="/my-profile" roles={['Employee']}>Thông tin cá nhân</RoleLink>

        {role === 'Admin' || role === 'Manager' ? <div className="sidebar__section">Quản lý Nhân sự</div> : null}
        <RoleLink to="/employees-page" roles={ADMIN_MANAGER}>Danh sách nhân viên</RoleLink>
        <RoleLink to="/add-employee" roles={ADMIN_MANAGER}>Thêm nhân viên</RoleLink>
        <RoleLink to="/show-department" roles={ADMIN}>Phòng ban</RoleLink>
        <RoleLink to="/show-human" roles={ADMIN}>Chức vụ</RoleLink>

        <div className="sidebar__section">Quản lý Tiền lương</div>
        <RoleLink to="/show-salaries" roles={ADMIN_MANAGER}>Bảng lương</RoleLink>
        <RoleLink to="/show-salaries" roles={['Employee']}>Lương của tôi</RoleLink>
        <RoleLink to="/update-salary" roles={ADMIN_MANAGER}>Tạo bảng lương</RoleLink>
        <RoleLink to="/history-salaries" roles={ADMIN_MANAGER}>Báo cáo và lịch sử lương</RoleLink>
        <RoleLink to="/history-salaries" roles={['Employee']}>Lịch sử lương của tôi</RoleLink>
        <RoleLink to="/timekeeping" roles={ADMIN_MANAGER}>Chấm công</RoleLink>
        <RoleLink to="/seniority" roles={ADMIN_MANAGER}>Thâm niên nhân viên</RoleLink>
        <RoleLink to="/timekeeping" roles={['Employee']}>Chấm công của tôi</RoleLink>
        <RoleLink to="/seniority" roles={['Employee']}>Thâm niên của tôi</RoleLink>
        <RoleLink to="/send-salary-emails" roles={ADMIN_MANAGER}>Gửi email phiếu lương</RoleLink>

        {role === 'Admin' ? <div className="sidebar__section">Hệ thống</div> : null}
        <RoleLink to="/users" roles={ADMIN}>Quản lý tài khoản</RoleLink>
      </nav>

      <button className="sidebar__logout" onClick={handleLogout}>Đăng xuất</button>
    </aside>
  )
}

function ProtectedLayout() {
  return (
    <div className="layout">
      <Sidebar />
      <main className="content">
        <Routes>
          <Route path="/" element={<RequireAuth roles={ADMIN_MANAGER}><DashboardPage /></RequireAuth>} />
          <Route path="/my-profile" element={<RequireAuth roles={['Employee']}><EmployeeProfilePage /></RequireAuth>} />
          <Route path="/employees-page" element={<RequireAuth roles={ADMIN_MANAGER}><EmployeesPage /></RequireAuth>} />
          <Route path="/add-employee" element={<RequireAuth roles={ADMIN_MANAGER}><AddEmployeePage /></RequireAuth>} />
          <Route path="/show-department" element={<RequireAuth roles={ADMIN}><DepartmentPage /></RequireAuth>} />
          <Route path="/show-human" element={<RequireAuth roles={ADMIN}><PositionPage /></RequireAuth>} />

          <Route path="/show-salaries" element={<RequireAuth roles={ALL_ROLES}><PayrollSalariesPage /></RequireAuth>} />
          <Route path="/update-salary" element={<RequireAuth roles={ADMIN_MANAGER}><UpdateSalaryPage /></RequireAuth>} />
          <Route path="/history-salaries" element={<RequireAuth roles={ALL_ROLES}><HistorySalariesPage /></RequireAuth>} />
          <Route path="/timekeeping" element={<RequireAuth roles={ALL_ROLES}><TimekeepingPage /></RequireAuth>} />
          <Route path="/send-salary-emails" element={<RequireAuth roles={ADMIN_MANAGER}><SendSalaryEmailsPage /></RequireAuth>} />
          <Route path="/seniority" element={<RequireAuth roles={ALL_ROLES}><SeniorityPage /></RequireAuth>} />
          <Route path="/users" element={<RequireAuth roles={ADMIN}><UserManagementPage /></RequireAuth>} />

          <Route path="/unauthorized" element={<RequireAuth roles={ALL_ROLES}><UnauthorizedPage /></RequireAuth>} />
          <Route path="*" element={<RequireAuth roles={ALL_ROLES}><NotImplementedPage apiPath="N/A" /></RequireAuth>} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/*" element={<ProtectedLayout />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
