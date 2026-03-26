export async function apiFetch(endpoint, options = {}) {
  const res = await fetch(endpoint, {
    ...options,
    credentials: 'include',
    headers: {
      ...(options.headers || {}),
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    },
  })

  // Backend Flask trả JSON/error message bằng nhiều dạng khác nhau.
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const data = await res.json()
      message = data?.error ? data.error : message
    } catch {
      try {
        const text = await res.text()
        message = text || message
      } catch {
        // ignore
      }
    }
    const err = new Error(message)
    err.status = res.status
    throw err
  }

  // Một số endpoint có thể trả JSON hoặc không content.
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return res.json()
  }
  return res.text()
}

