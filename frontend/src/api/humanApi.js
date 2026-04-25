import { apiFetch } from './http'

// ==========================================
// 1. QUẢN LÝ NHÂN VIÊN
// ==========================================

export function getEmployees() {
    return apiFetch('/api/human/employees-page')
}

export function addEmployee(payload) {
    return apiFetch('/api/human/add-employee', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function deleteEmployee(id) {
    return apiFetch(`/api/human/delete-employee/${id}`, {
        method: 'DELETE',
    })
}

export function updateEmployee(data) {
    return apiFetch('/api/human/update-employee', {
        method: 'PUT',
        body: JSON.stringify(data),
    })
}

export function getReportHuman() {
    return apiFetch('/api/human/report-human')
}

// ==========================================
// 2. QUẢN LÝ PHÒNG BAN
// ==========================================

export function showDepartments() {
    return apiFetch('/api/human/show-department')
}

export function addDepartment(name) {
    return apiFetch('/api/human/add-department', {
        method: 'POST',
        body: JSON.stringify({ DepartmentName: name }),
    })
}

export function updateDepartment(payload) {
    return apiFetch('/api/human/update-department', {
        method: 'PUT',
        body: JSON.stringify(payload),
    })
}

export function deleteDepartment(id) {
    return apiFetch(`/api/human/delete-department/${id}`, {
        method: 'DELETE',
    })
}

// ==========================================
// 3. QUẢN LÝ CHỨC VỤ
// ==========================================

export function showPositions() {
    return apiFetch('/api/human/show-human')
}

export function addPosition(PositionName) {
    return apiFetch('/api/human/add-position', {
        method: 'POST',
        body: JSON.stringify({ PositionName }),
    })
}

export function updatePosition(payload) {
    return apiFetch('/api/human/update-position', {
        method: 'PUT',
        body: JSON.stringify(payload),
    })
}

export function deletePosition(id) {
    return apiFetch(`/api/human/delete-position/${id}`, {
        method: 'DELETE',
    })
}

// ==========================================
// 4. DROPDOWN
// ==========================================

export function getDepartments() {
    return apiFetch('/api/human/departments')
}

export function getPositions() {
    return apiFetch('/api/human/positions')
}