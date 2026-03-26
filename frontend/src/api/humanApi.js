import { apiFetch } from './http'

export function getEmployees() {
  return apiFetch('/api/human/employees-page')
}

export function addEmployee(payload) {
  return apiFetch('/api/human/add-employee', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getReportHuman() {
  return apiFetch('/api/human/report-human')
}

export function showDepartments() {
  return apiFetch('/api/human/show-department')
}

export function showPositions() {
  return apiFetch('/api/human/show-human')
}

