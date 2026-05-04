import { useEffect, useMemo, useState } from 'react'
import { RefreshCw } from '../components/LineIcons'
import Loading from '../components/Loading'
import ApiError from '../components/ApiError'
import { getEmployees, getReportHuman } from '../api/humanApi'
import { employeeAnniversaryWarning, getSalaries, getTimekeeping, leaveDaysWarning, salaryAlerts } from '../api/payrollApi'
import '../styles/DashboardPage.css'

const formatMoney = (value) => {
  const number = Number(value || 0)
  if (number >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)} tỷ`
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(1)} triệu`
  return number.toLocaleString('en-US')
}

const normalizeMonth = (value) => {
  if (!value) return 'Chưa có tháng'
  const text = String(value)
  return text.length >= 7 ? text.slice(0, 7) : text
}

const toIsoDate = (value) => {
  if (!value) return ''
  const text = String(value)
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0, 10)
  const date = new Date(text)
  return Number.isNaN(date.getTime()) ? '' : date.toISOString().slice(0, 10)
}

const getPeriodValue = (mode, dateValue, monthValue, yearValue) => {
  if (mode === 'all') return ''
  if (mode === 'day') return dateValue
  if (mode === 'year') return String(yearValue || new Date().getFullYear())
  return monthValue
}

const matchPeriod = (value, mode, selectedValue) => {
  if (mode === 'all' || !selectedValue) return true
  const iso = toIsoDate(value)
  if (!iso) return false
  if (mode === 'day') return iso === selectedValue
  if (mode === 'year') return iso.slice(0, 4) === selectedValue
  return iso.slice(0, 7) === selectedValue
}

const matchMonthLikePeriod = (value, createdAt, mode, selectedValue) => {
  if (mode === 'all' || !selectedValue) return true
  const primary = toIsoDate(value)
  const created = toIsoDate(createdAt)
  if (mode === 'day') {
    return created ? created === selectedValue : primary === selectedValue
  }
  if (mode === 'year') {
    return (primary || created).slice(0, 4) === selectedValue
  }
  return (primary || created).slice(0, 7) === selectedValue
}

const getPeriodLabel = (mode, selectedValue) => {
  if (mode === 'all' || !selectedValue) return 'Từ trước đến nay'
  if (mode === 'day') return `Ngày ${selectedValue.split('-').reverse().join('/')}`
  if (mode === 'year') return `Năm ${selectedValue}`
  const [year, month] = selectedValue.split('-')
  return `Tháng ${month}/${year}`
}

const groupLabel = (dateValue, mode) => {
  const iso = toIsoDate(dateValue)
  if (!iso) return 'Không rõ'
  if (mode === 'day') return iso.slice(5, 10)
  if (mode === 'year') return iso.slice(0, 4)
  if (mode === 'all') return iso.slice(0, 7)
  return iso.slice(0, 7)
}

const countBy = (items, keyGetter) => {
  const map = {}
  items.forEach((item) => {
    const key = keyGetter(item) || 'Chưa xác định'
    map[key] = (map[key] || 0) + 1
  })
  return Object.entries(map)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
}

const chartColors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#a855f7', '#14b8a6', '#f97316']


function PeriodFilter({ mode, setMode, dateValue, setDateValue, monthValue, setMonthValue, yearValue, setYearValue }) {
  const years = Array.from({ length: 9 }, (_, index) => String(new Date().getFullYear() - 4 + index))
  return (
    <div className="dashboard-filter-card">
      <div>
        <p className="dashboard-filter-card__label">Bộ lọc thống kê</p>
        <h3>{getPeriodLabel(mode, getPeriodValue(mode, dateValue, monthValue, yearValue))}</h3>
        <span>Chọn theo ngày, tháng, năm hoặc xem toàn bộ dữ liệu từ trước đến nay.</span>
      </div>
      <div className="dashboard-filter-controls">
        <select value={mode} onChange={(event) => setMode(event.target.value)} aria-label="Chọn kiểu thống kê">
          <option value="all">Từ trước đến nay</option>
          <option value="day">Theo ngày</option>
          <option value="month">Theo tháng</option>
          <option value="year">Theo năm</option>
        </select>
        {mode === 'day' ? (
          <input type="date" value={dateValue} onChange={(event) => setDateValue(event.target.value)} aria-label="Chọn ngày" />
        ) : null}
        {mode === 'month' ? (
          <input type="month" value={monthValue} onChange={(event) => setMonthValue(event.target.value)} aria-label="Chọn tháng" />
        ) : null}
        {mode === 'year' ? (
          <select value={yearValue} onChange={(event) => setYearValue(event.target.value)} aria-label="Chọn năm">
            {years.map((year) => <option key={year} value={year}>{year}</option>)}
          </select>
        ) : null}
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, note, tone = 'blue' }) {
  return (
    <div className={`dashboard-stat dashboard-stat--${tone}`}>
      <div className="dashboard-stat__icon">{icon}</div>
      <div>
        <div className="dashboard-stat__title">{title}</div>
        <div className="dashboard-stat__value">{value}</div>
        <div className="dashboard-stat__note">{note}</div>
      </div>
    </div>
  )
}

function DonutChart({ title, data, centerLabel, centerValue }) {
  const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0)
  let offset = 0
  const radius = 58
  const circumference = 2 * Math.PI * radius

  return (
    <div className="dashboard-panel dashboard-panel--chart">
      <div className="dashboard-panel__head">
        <h3>{title}</h3>
        <span>{total} mục</span>
      </div>
      <div className="donut-wrap">
        <div className="donut-box">
          <svg viewBox="0 0 160 160" className="donut-chart" role="img" aria-label={title}>
            <circle cx="80" cy="80" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="24" />
            {total > 0 && data.map((item, index) => {
              const dash = (Number(item.value || 0) / total) * circumference
              const segment = (
                <circle
                  key={item.name}
                  cx="80"
                  cy="80"
                  r={radius}
                  fill="none"
                  stroke={chartColors[index % chartColors.length]}
                  strokeWidth="24"
                  strokeDasharray={`${dash} ${circumference - dash}`}
                  strokeDashoffset={-offset}
                  strokeLinecap="round"
                  transform="rotate(-90 80 80)"
                />
              )
              offset += dash
              return segment
            })}
          </svg>
          <div className="donut-center">
            <strong>{centerValue ?? total}</strong>
            <span>{centerLabel}</span>
          </div>
        </div>
        <div className="chart-legend">
          {data.slice(0, 6).map((item, index) => (
            <div className="legend-row" key={item.name}>
              <span className="legend-dot" style={{ background: chartColors[index % chartColors.length] }} />
              <span className="legend-name">{item.name}</span>
              <strong>{item.value}</strong>
              <em>{total ? Math.round((item.value / total) * 100) : 0}%</em>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function BarChart({ title, data, valueLabel = '' }) {
  const max = Math.max(...data.map((item) => Number(item.value || 0)), 1)
  return (
    <div className="dashboard-panel dashboard-panel--chart">
      <div className="dashboard-panel__head">
        <h3>{title}</h3>
        <span>Biểu đồ cột</span>
      </div>
      <div className="bar-chart">
        {data.map((item, index) => (
          <div className="bar-item" key={item.name}>
            <div className="bar-value">{item.value}{valueLabel}</div>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ height: `${Math.max(8, (Number(item.value || 0) / max) * 100)}%`, background: chartColors[index % chartColors.length] }}
              />
            </div>
            <div className="bar-label" title={item.name}>{item.name}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function LineChart({ title, data, suffix = '' }) {
  const width = 640
  const height = 230
  const padding = 34
  const values = data.map((item) => Number(item.value || 0))
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = Math.max(max - min, 1)
  const points = data.map((item, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(data.length - 1, 1)
    const y = height - padding - ((Number(item.value || 0) - min) / range) * (height - padding * 2)
    return { ...item, x, y }
  })
  const line = points.map((p) => `${p.x},${p.y}`).join(' ')
  const area = `${padding},${height - padding} ${line} ${width - padding},${height - padding}`

  return (
    <div className="dashboard-panel dashboard-panel--wide">
      <div className="dashboard-panel__head">
        <h3>{title}</h3>
        <span>Đường xu hướng</span>
      </div>
      <svg className="line-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
        {[0, 1, 2, 3].map((i) => {
          const y = padding + i * ((height - padding * 2) / 3)
          return <line key={i} x1={padding} x2={width - padding} y1={y} y2={y} stroke="#e5e7eb" strokeWidth="1" />
        })}
        <polygon points={area} fill="rgba(37, 99, 235, 0.12)" />
        <polyline points={line} fill="none" stroke="#2563eb" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
        {points.map((p) => (
          <g key={p.name}>
            <circle cx={p.x} cy={p.y} r="5" fill="#2563eb" stroke="#fff" strokeWidth="3" />
            <text x={p.x} y={p.y - 12} textAnchor="middle" className="line-value">{formatMoney(p.value)}{suffix}</text>
            <text x={p.x} y={height - 8} textAnchor="middle" className="line-label">{p.name}</text>
          </g>
        ))}
      </svg>
    </div>
  )
}

function AlertCard({ icon, title, value, description, tone }) {
  return (
    <div className={`alert-card alert-card--${tone}`}>
      <div className="alert-card__icon">{icon}</div>
      <div>
        <h4>{title}</h4>
        <strong>{value}</strong>
        <p>{description}</p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const [employees, setEmployees] = useState([])
  const [salaries, setSalaries] = useState([])
  const [timekeeping, setTimekeeping] = useState([])
  const today = new Date().toISOString().slice(0, 10)
  const [periodMode, setPeriodMode] = useState('all')
  const [selectedDate, setSelectedDate] = useState(today)
  const [selectedMonth, setSelectedMonth] = useState(today.slice(0, 7))
  const [selectedYear, setSelectedYear] = useState(today.slice(0, 4))
  const [warnings, setWarnings] = useState({ salary: null, leave: null, anniversary: null })

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [res, employeesRes, salariesRes, timekeepingRes, salaryRes, leaveRes, anniversaryRes] = await Promise.all([
        getReportHuman(),
        getEmployees().catch(() => ({ employees: [] })),
        getSalaries().catch(() => []),
        getTimekeeping().catch(() => []),
        salaryAlerts().catch(() => null),
        leaveDaysWarning().catch(() => null),
        employeeAnniversaryWarning().catch(() => null),
      ])
      setData(res)
      setEmployees(employeesRes?.employees || [])
      setSalaries(Array.isArray(salariesRes) ? salariesRes : [])
      setTimekeeping(Array.isArray(timekeepingRes) ? timekeepingRes : [])
      setWarnings({ salary: salaryRes, leave: leaveRes, anniversary: anniversaryRes })
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const dashboardData = useMemo(() => {
    const selectedPeriod = getPeriodValue(periodMode, selectedDate, selectedMonth, selectedYear)
    const periodLabel = getPeriodLabel(periodMode, selectedPeriod)

    const filteredEmployees = periodMode === 'all' ? employees : employees.filter((item) => matchPeriod(item.HireDate, periodMode, selectedPeriod))
    const filteredSalaries = periodMode === 'all' ? salaries : salaries.filter((item) => matchMonthLikePeriod(item.SalaryMonth, item.CreatedAt, periodMode, selectedPeriod))
    const filteredTimekeeping = periodMode === 'all' ? timekeeping : timekeeping.filter((item) => matchMonthLikePeriod(item.AttendanceMonth, item.CreatedAt, periodMode, selectedPeriod))

    const employeeScope = periodMode === 'all' ? employees : filteredEmployees
    const salaryScope = periodMode === 'all' ? salaries : filteredSalaries
    const attendanceScope = periodMode === 'all' ? timekeeping : filteredTimekeeping
    const trendGroupMode = periodMode === 'all' || periodMode === 'day' ? 'month' : periodMode

    const statusData = employeeScope.length
      ? countBy(employeeScope, (item) => item.Status)
      : Object.entries(data?.status_distribution || {}).map(([name, value]) => ({ name: name || 'Chưa xác định', value }))

    const departmentData = countBy(employeeScope, (item) => item.DepartmentName).slice(0, 7)
    const positionData = countBy(employeeScope, (item) => item.PositionName).slice(0, 7)

    const salaryByPeriodMap = {}
    const trendSource = salaryScope.length ? salaryScope : salaries
    trendSource.forEach((item) => {
      const label = groupLabel(item.SalaryMonth || item.CreatedAt, trendGroupMode)
      if (label === 'Không rõ') return
      salaryByPeriodMap[label] = (salaryByPeriodMap[label] || 0) + Number(item.NetSalary || 0)
    })
    const salaryTrend = Object.entries(salaryByPeriodMap)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => a.name.localeCompare(b.name))
      .slice(periodMode === 'all' ? -12 : -6)

    const currentTotal = salaryScope.reduce((sum, item) => sum + Number(item.NetSalary || 0), 0)
    const currentAvg = salaryScope.length ? currentTotal / salaryScope.length : 0
    const currentHighest = salaryScope.reduce((max, item) => Math.max(max, Number(item.NetSalary || 0)), 0)

    const attendanceBars = [
      { name: 'Công đã làm', value: attendanceScope.reduce((sum, item) => sum + Number(item.WorkDays || 0), 0) },
      { name: 'Nghỉ phép', value: attendanceScope.reduce((sum, item) => sum + Number(item.LeaveDays || 0), 0) },
      { name: 'Nghỉ không phép', value: attendanceScope.reduce((sum, item) => sum + Number(item.AbsentDays || 0), 0) },
    ]

    const attendanceTrendMap = {}
    const attendanceTrendSource = attendanceScope.length ? attendanceScope : timekeeping
    attendanceTrendSource.forEach((item) => {
      const label = groupLabel(item.AttendanceMonth || item.CreatedAt, trendGroupMode)
      if (label === 'Không rõ') return
      attendanceTrendMap[label] = (attendanceTrendMap[label] || 0) + Number(item.WorkDays || 0)
    })
    const attendanceTrend = Object.entries(attendanceTrendMap)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => a.name.localeCompare(b.name))
      .slice(periodMode === 'all' ? -12 : -6)

    return {
      selectedPeriod,
      periodLabel,
      filteredEmployees,
      filteredSalaries,
      filteredTimekeeping,
      statusData,
      departmentData,
      positionData,
      salaryTrend,
      latestMonth: periodLabel,
      latestTotal: currentTotal,
      avgSalary: currentAvg,
      highestSalary: currentHighest,
      attendanceBars,
      attendanceTrend,
    }
  }, [data, employees, salaries, timekeeping, periodMode, selectedDate, selectedMonth, selectedYear])

  return (
    <div className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="dashboard-kicker">HR & Payroll analytics</p>
          <h2>Tổng quan hệ thống</h2>
          <p>Theo dõi nhanh tình hình nhân sự, lương, chấm công và các cảnh báo quan trọng.</p>
        </div>
        <button className="dashboard-refresh" onClick={load} disabled={loading}>
          <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> Làm mới dữ liệu
        </button>
      </div>

      <PeriodFilter
        mode={periodMode}
        setMode={setPeriodMode}
        dateValue={selectedDate}
        setDateValue={setSelectedDate}
        monthValue={selectedMonth}
        setMonthValue={setSelectedMonth}
        yearValue={selectedYear}
        setYearValue={setSelectedYear}
      />

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}

      {data ? (
        <>
          <section className="dashboard-grid dashboard-grid--stats">
            <StatCard icon="👥" title={periodMode === 'all' ? 'Tổng nhân viên' : 'Nhân viên mới'} value={periodMode === 'all' ? data.total_employees : dashboardData.filteredEmployees.length} note={dashboardData.periodLabel} tone="indigo" />
            <StatCard icon="🏢" title="Phòng ban" value={data.total_departments} note="Đơn vị đang hoạt động" tone="green" />
            <StatCard icon="🎖️" title="Chức vụ" value={data.total_positions} note="Cơ cấu vị trí" tone="amber" />
            <StatCard icon="💰" title="Quỹ lương" value={formatMoney(dashboardData.latestTotal)} note={dashboardData.periodLabel} tone="blue" />
          </section>

          <section className="dashboard-grid dashboard-grid--charts">
            <DonutChart title="Cơ cấu nhân sự theo phòng ban" data={dashboardData.departmentData} centerLabel="nhân viên" centerValue={data.total_employees} />
            <DonutChart title="Cơ cấu nhân sự theo chức vụ" data={dashboardData.positionData} centerLabel="chức vụ" centerValue={data.total_positions} />
            <BarChart title="Trạng thái nhân sự" data={dashboardData.statusData} />
          </section>

          <section className="dashboard-grid dashboard-grid--analytics">
            <LineChart title={periodMode === 'all' ? 'Xu hướng quỹ lương từ trước đến nay' : 'Xu hướng quỹ lương theo bộ lọc'} data={dashboardData.salaryTrend.length ? dashboardData.salaryTrend : [{ name: dashboardData.periodLabel, value: dashboardData.latestTotal }]} />
            <div className="dashboard-panel salary-summary">
              <div className="dashboard-panel__head">
                <h3>Tổng quan lương</h3>
                <span>{dashboardData.periodLabel}</span>
              </div>
              <div className="salary-metric salary-metric--blue">
                <span>Tổng quỹ lương</span>
                <strong>{formatMoney(dashboardData.latestTotal)} VND</strong>
              </div>
              <div className="salary-metric salary-metric--green">
                <span>Lương trung bình</span>
                <strong>{formatMoney(dashboardData.avgSalary)} VND</strong>
              </div>
              <div className="salary-metric salary-metric--amber">
                <span>Lương cao nhất</span>
                <strong>{formatMoney(dashboardData.highestSalary)} VND</strong>
              </div>
            </div>
          </section>

          <section className="dashboard-grid dashboard-grid--bottom">
            <BarChart title={`Tình hình chấm công - ${dashboardData.periodLabel}`} data={dashboardData.attendanceBars} />
            <div className="dashboard-panel alerts-panel">
              <div className="dashboard-panel__head">
                <h3>Cảnh báo & gợi ý xử lý</h3>
                <span>Cập nhật realtime</span>
              </div>
              <AlertCard icon="⚠️" title="Cảnh báo lương" value={warnings.salary?.total ?? 0} description="Nhân viên thiếu bảng lương hoặc dữ liệu lương bất thường." tone="red" />
              <AlertCard icon="🕒" title="Nghỉ phép / thiếu công" value={warnings.leave?.total ?? 0} description="Nhân viên có nghỉ phép nhiều, nghỉ không phép hoặc thiếu công." tone="amber" />
              <AlertCard icon="📈" title="Gợi ý tăng lương" value={warnings.anniversary?.total ?? 0} description="Nhân viên đủ điều kiện xem xét tăng lương theo thâm niên." tone="green" />
            </div>
          </section>
        </>
      ) : null}

      <div className="dashboard-footer-note">
        Dữ liệu được tổng hợp từ SQL Server (Nhân sự) và MySQL (Lương, chấm công).
      </div>
    </div>
  )
}
