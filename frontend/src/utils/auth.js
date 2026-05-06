export function saveAuth(token, user) {
  clearLegacyAuth()
  sessionStorage.setItem('token', token)
  sessionStorage.setItem('user', JSON.stringify(user || {}))
}

export function clearAuth() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('user')
  clearLegacyAuth()
}

export function getToken() {
  return sessionStorage.getItem('token')
}

export function getCurrentUser() {
  try {
    const user = JSON.parse(sessionStorage.getItem('user') || 'null')
    return getToken() && user ? user : null
  } catch {
    return null
  }
}

export function updateCurrentUser(updates = {}) {
  const currentUser = getCurrentUser()
  if (!currentUser) return
  sessionStorage.setItem('user', JSON.stringify({ ...currentUser, ...updates }))
}

export function getRole() {
  return getCurrentUser()?.Role || null
}

export function hasRole(allowedRoles = []) {
  const role = getRole()
  return allowedRoles.includes(role)
}

function clearLegacyAuth() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}
