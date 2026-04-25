import { clearAuth, getToken } from '../utils/auth'

export async function apiFetch(endpoint, options = {}) {
  const token = getToken()
  const headers = {
    ...(options.headers || {}),
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(endpoint, {
    ...options,
    credentials: 'include',
    headers,
  })

  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const data = await res.json()
      message = data?.error ? data.error : message
    } catch {
      try {
        const text = await res.text()
        message = text || message
      } catch {}
    }

    if (res.status === 401) {
      clearAuth()
    }

    const err = new Error(message)
    err.status = res.status
    throw err
  }

  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return res.text()
}
