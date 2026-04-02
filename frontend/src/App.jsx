import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
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

function App() {
  const linkClassName = ({ isActive }) =>
    `nav-link${isActive ? ' nav-link--active' : ''}`

  return (
    <BrowserRouter>
      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar__brand">HR & Payroll</div>
          <nav className="sidebar__nav">
            <NavLink to="/" className={linkClassName}>
              Tổng quan
            </NavLink>
            <div className="sidebar__section">Quản lý Nhân sự</div>
            <NavLink to="/employees-page" className={linkClassName}>
              Danh sách nhân viên
            </NavLink>
            <NavLink to="/add-employee" className={linkClassName}>
              Thêm nhân viên
            </NavLink>
            <NavLink to="/show-department" className={linkClassName}>
              Phòng ban (chưa có)
            </NavLink>
            <NavLink to="/show-human" className={linkClassName}>
              Chức vụ (chưa có)
            </NavLink>

            <div className="sidebar__section">Quản lý Tiền lương</div>
            <NavLink to="/show-salaries" className={linkClassName}>
              Bảng lương
            </NavLink>
            <NavLink to="/update-salary" className={linkClassName}>
              Cập nhật lương
            </NavLink>
            <NavLink to="/history-salaries" className={linkClassName}>
              Lịch sử lương (chưa có)
            </NavLink>
            <NavLink to="/salaries-month" className={linkClassName}>
              Lọc theo tháng (chưa có)
            </NavLink>
            <NavLink to="/report-salaries" className={linkClassName}>
              Báo cáo lương (chưa có)
            </NavLink>
            <NavLink to="/timekeeping" className={linkClassName}>
              Chấm công
            </NavLink>
            <NavLink to="/send-salary-emails" className={linkClassName}>
              Gửi email phiếu lương
            </NavLink>

            <div className="sidebar__section">Alerts & Reports</div>
            <NavLink to="/employee-anniversary-warning" className={linkClassName}>
              Kỷ niệm thâm niên (chưa có)
            </NavLink>
            <NavLink to="/leave-days-warning" className={linkClassName}>
              Nghỉ phép quá hạn (chưa có)
            </NavLink>
            <NavLink to="/salary-alerts" className={linkClassName}>
              Cảnh báo biến động lương (chưa có)
            </NavLink>
            <NavLink to="/report-human-full" className={linkClassName}>
              Báo cáo thống kê (chưa có)
            </NavLink>
          </nav>
        </aside>

        <main className="content">
          <Routes>
            <Route
              path="/"
              element={
                <RequireAuth>
                  <DashboardPage />
                </RequireAuth>
              }
            />
            <Route
              path="/employees-page"
              element={
                <RequireAuth>
                  <EmployeesPage />
                </RequireAuth>
              }
            />
            <Route
              path="/add-employee"
              element={
                <RequireAuth>
                  <AddEmployeePage />
                </RequireAuth>
              }
            />

            <Route
              path="/show-salaries"
              element={
                <RequireAuth>
                  <PayrollSalariesPage />
                </RequireAuth>
              }
            />
            <Route
              path="/timekeeping"
              element={
                <RequireAuth>
                  <TimekeepingPage />
                </RequireAuth>
              }
            />
            <Route
              path="/update-salary"
              element={
                <RequireAuth>
                  <UpdateSalaryPage />
                </RequireAuth>
              }
            />
            <Route
              path="/send-salary-emails"
              element={
                <RequireAuth>
                  <SendSalaryEmailsPage />
                </RequireAuth>
              }
            />

            <Route
              path="/show-department"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/human/show-department" />
                </RequireAuth>
              }
            />
            <Route
              path="/show-human"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/human/show-human" />
                </RequireAuth>
              }
            />
            <Route
              path="/history-salaries"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/payroll/history-salaries/1" />
                </RequireAuth>
              }
            />
            <Route
              path="/salaries-month"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/payroll/salaries/month/1/2026" />
                </RequireAuth>
              }
            />
            <Route
              path="/report-salaries"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/payroll/report-salaries" />
                </RequireAuth>
              }
            />

            <Route
              path="/employee-anniversary-warning"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/payroll/employee-anniversary-warning" />
                </RequireAuth>
              }
            />
            <Route
              path="/leave-days-warning"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/payroll/leave-days-warning" />
                </RequireAuth>
              }
            />
            <Route
              path="/salary-alerts"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/payroll/salary-alerts" />
                </RequireAuth>
              }
            />
            <Route
              path="/report-human-full"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="/api/human/report-human" />
                </RequireAuth>
              }
            />

            <Route
              path="*"
              element={
                <RequireAuth>
                  <NotImplementedPage apiPath="N/A" />
                </RequireAuth>
              }
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
