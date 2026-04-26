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

export function reportSalaries() {
    return apiFetch('/api/payroll/report-salaries')
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
