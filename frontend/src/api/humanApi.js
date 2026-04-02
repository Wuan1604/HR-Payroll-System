import { apiFetch } from './http'

// 1. Lấy danh sách nhân viên
export function getEmployees() {
    return apiFetch('/api/human/employees-page')
}

// 2. Thêm mới nhân viên và đồng bộ
export function addEmployee(payload) {
    return apiFetch('/api/human/add-employee', {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

// 3. Lấy danh sách Phòng ban (Đã sửa lại dùng apiFetch)
export function getDepartments() {
    return apiFetch('/api/human/departments')
}

// 4. Lấy danh sách Chức vụ (Đã sửa lại dùng apiFetch)
export function getPositions() {
    return apiFetch('/api/human/positions')
}

// 5. Lấy báo cáo tổng quan nhân sự
export function getReportHuman() {
    return apiFetch('/api/human/report-human')
}

// 6. Hiển thị danh mục phòng ban (nếu cần quản lý riêng)
export function showDepartments() {
    return apiFetch('/api/human/show-department')
}

// 7. Hiển thị danh mục chức vụ (nếu cần quản lý riêng)
export function showPositions() {
    return apiFetch('/api/human/show-human')
}