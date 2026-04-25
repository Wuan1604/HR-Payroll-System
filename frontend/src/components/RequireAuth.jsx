import { Navigate } from 'react-router-dom'
import { getCurrentUser, hasRole } from '../utils/auth'

export default function RequireAuth({ children, roles }) {
  const user = getCurrentUser()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (roles?.length && !hasRole(roles)) {
    return <Navigate to="/unauthorized" replace />
  }

  return children
}
