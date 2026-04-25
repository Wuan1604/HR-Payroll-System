import { apiFetch } from './http'

export function login(payload) {
  return apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function logout() {
  return apiFetch('/api/auth/logout', { method: 'POST' })
}

export function getMe() {
  return apiFetch('/api/auth/me')
}

export function getRoles() {
  return apiFetch('/api/auth/roles')
}

export function getUsers() {
  return apiFetch('/api/auth/users')
}

export function createUser(payload) {
  return apiFetch('/api/auth/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateUser(userId, payload) {
  return apiFetch(`/api/auth/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteUser(userId) {
  return apiFetch(`/api/auth/users/${userId}`, {
    method: 'DELETE',
  })
}

export function register(payload) {
  return apiFetch('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
