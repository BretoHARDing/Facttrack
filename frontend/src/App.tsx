import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { ToastProvider } from './components/ToastProvider'
import { useToast } from './hooks/useToast'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { CasesPage } from './pages/CasesPage'
import { useAuthStore } from './store/auth'

function AppRoutes() {
  const navigate = useNavigate()
  const { pushToast } = useToast()
  const clearAuth = useAuthStore((state) => state.clearAuth)

  useEffect(() => {
    const onUnauthorized = () => {
      clearAuth()
      pushToast({ title: 'Session expired', description: 'Please sign in again to continue.' })
      navigate('/login', { replace: true })
    }

    const onServerError = (event: Event) => {
      const detail = (event as CustomEvent<{ message?: string }>).detail
      pushToast({ title: 'Server error', description: detail?.message || 'The backend reported an internal error.' })
    }

    window.addEventListener('facttrack:unauthorized', onUnauthorized)
    window.addEventListener('facttrack:server-error', onServerError)

    return () => {
      window.removeEventListener('facttrack:unauthorized', onUnauthorized)
      window.removeEventListener('facttrack:server-error', onServerError)
    }
  }, [clearAuth, navigate, pushToast])

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/cases" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/cases" element={<CasesPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/cases" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ToastProvider>
  )
}
