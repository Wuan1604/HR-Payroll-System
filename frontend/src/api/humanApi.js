import { apiFetch } from './http'

// ==========================================
// 1. QUẢN LÝ NHÂN VIÊN
// ==========================================

// Lấy danh sách nhân viên
export function getEmployees() {
    return apiFetch('/api/human/employees-page')
}

// Thêm mới nhân viên và đồng bộ sang MySQL
export function addEmployee(payload) {
    return apiFetch('/api/human/add-employee', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

// Lấy báo cáo tổng quan nhân sự (Dashboard)
export function getReportHuman() {
    return apiFetch('/api/human/report-human')
}

// ==========================================
// 2. QUẢN LÝ PHÒNG BAN (DEPARTMENTS)
// ==========================================

// Xem danh sách phòng ban
export function showDepartments() {
    return apiFetch('/api/human/show-department')
}

// Thêm phòng ban mới (Đồng bộ MySQL)
export function addDepartment(name) {
    return apiFetch('/api/human/add-department', {
        method: 'POST',
        body: JSON.stringify({ DepartmentName: name }),
    })
}

// Cập nhật thông tin phòng ban (Đồng bộ MySQL)
export function updateDepartment(payload) {
    return apiFetch('/api/human/update-department', {
        method: 'PUT',
        body: JSON.stringify(payload), // payload gồm { DepartmentID, DepartmentName }
    })
}

// Xóa phòng ban (Đồng bộ MySQL)
export function deleteDepartment(id) {
    return apiFetch(`/api/human/delete-department/${id}`, {
        method: 'DELETE',
    })
}

// ==========================================
// 3. QUẢN LÝ CHỨC VỤ (POSITIONS)
// ==========================================

// Xem danh sách chức vụ
export function showPositions() {
    return apiFetch('/api/human/show-human')
}

// Thêm chức vụ mới (Đồng bộ MySQL)
export function addPosition(name) {
    return apiFetch('/api/human/add-position', {
        method: 'POST',
        body: JSON.stringify({ PositionName: name }),
    })
}

// Cập nhật thông tin chức vụ (Đồng bộ MySQL)
export function updatePosition(payload) {
    return apiFetch('/api/human/update-position', {
        method: 'PUT',
        body: JSON.stringify(payload), // payload gồm { PositionID, PositionName }
    })
}

// Xóa chức vụ (Đồng bộ MySQL)
export function deletePosition(id) {
    return apiFetch(`/api/human/delete-position/${id}`, {
        method: 'DELETE',
    })
}

// ==========================================
// 4. HÀM HỖ TRỢ ĐỔ DỮ LIỆU VÀO SELECT/DROPDOWN
// ==========================================
export function getDepartments() {
    return apiFetch('/api/human/departments')
}

export function getPositions() {
    return apiFetch('/api/human/positions')
}