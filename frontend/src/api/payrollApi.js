import { apiFetch } from './http'

export function getSalaries() {
    return apiFetch('/api/payroll/show-salaries')
}

export function showSalaries() {
    return apiFetch('/api/payroll/show-salaries')
}

export function getTimekeeping() {
    return apiFetch('/api/payroll/timekeeping')
}

export function getAttendanceEmployees() {
    return apiFetch('/api/payroll/attendance/employees')
}

export function saveAttendanceCheck(payload) {
    return apiFetch('/api/payroll/attendance/check', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function getAttendanceDetails(employeeId, month, baseSalary = 0) {
    const params = new URLSearchParams({
        employee_id: employeeId,
        month,
        base_salary: String(baseSalary || 0),
    })
    return apiFetch(`/api/payroll/attendance/details?${params.toString()}`)
}

export function getAttendanceSummary(employeeId, month, baseSalary = 0) {
    const params = new URLSearchParams({
        employee_id: employeeId,
        month,
        base_salary: String(baseSalary || 0),
    })
    return apiFetch(`/api/payroll/attendance/summary?${params.toString()}`)
}

export function updateSalary(payload) {
    return apiFetch('/api/payroll/update-salary', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function sendSalaryEmails(payload = null) {
    if (!payload) {
        return apiFetch('/api/payroll/send-salary-emails')
    }

    return apiFetch('/api/payroll/send-salary-emails', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function historySalaries(employeeId) {
    return apiFetch(`/api/payroll/history-salaries/${employeeId}`)
}

export function salariesMonth(month, year) {
    return apiFetch(`/api/payroll/salaries/month/${month}/${year}`)
}

export function reportSalaries(params = {}) {
    const query = new URLSearchParams()
    if (params.month) query.set('month', params.month)
    if (params.employee_id) query.set('employee_id', params.employee_id)
    if (params.format) query.set('format', params.format)
    const qs = query.toString()
    return apiFetch('/api/payroll/report-salaries' + (qs ? '?' + qs : ''))
}

export function employeeAnniversaryWarning() {
    return apiFetch('/api/payroll/employee-anniversary-warning')
}

export function leaveDaysWarning() {
    return apiFetch('/api/payroll/leave-days-warning')
}

export function salaryAlerts() {
    return apiFetch('/api/payroll/salary-alerts')
}

export function getAttendanceSeniority(employeeId = '') {
    const params = new URLSearchParams()
    if (employeeId) params.set('employee_id', employeeId)
    const query = params.toString()
    return apiFetch(`/api/payroll/attendance/seniority${query ? `?${query}` : ''}`)
}

export async function downloadSalaryReport(params = {}) {
    const { getToken } = await import('../utils/auth')
    const query = new URLSearchParams()
    if (params.month) query.set('month', params.month)
    if (params.employee_id) query.set('employee_id', params.employee_id)
    query.set('format', params.format || 'pdf')

    const token = getToken()
    const res = await fetch('/api/payroll/report-salaries?' + query.toString(), {
        credentials: 'include',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
    })

    if (!res.ok) {
        let message = `HTTP ${res.status}`
        try {
            const data = await res.json()
            message = data?.error || message
        } catch {
            try {
                message = (await res.text()) || message
            } catch {}
        }
        throw new Error(message)
    }

    return res.blob()
}

export function getBaseSalaries() {
    return apiFetch('/api/payroll/base-salaries')
}

export function saveBaseSalary(payload) {
    return apiFetch('/api/payroll/base-salaries', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function updateBaseSalary(employeeId, payload) {
    return apiFetch(`/api/payroll/base-salaries/${employeeId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
    })
}

export function deleteBaseSalary(employeeId) {
    return apiFetch(`/api/payroll/base-salaries/${employeeId}`, {
        method: 'DELETE',
    })
}
