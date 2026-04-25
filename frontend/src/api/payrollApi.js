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

export function updateSalary(payload) {
    return apiFetch('/api/payroll/update-salary', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function sendSalaryEmails() {
    return apiFetch('/api/payroll/send-salary-emails')
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