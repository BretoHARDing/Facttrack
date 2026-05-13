import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { loginUser } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useToast } from '../hooks/useToast'

type LoginForm = {
  email: string
  password: string
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { pushToast } = useToast()
  const setAuth = useAuthStore((state) => state.setAuth)
  const token = useAuthStore((state) => state.token)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>()

  useEffect(() => {
    if (token) {
      navigate('/cases', { replace: true })
    }
  }, [navigate, token])

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl items-center justify-center px-4 py-10">
      <div className="grid w-full overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 shadow-2xl shadow-cyan-950/20 backdrop-blur-xl lg:grid-cols-[1.1fr_0.9fr]">
        <div className="hidden bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.18),_transparent_45%),linear-gradient(135deg,#020617,#0f172a)] p-10 lg:flex lg:flex-col lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.4em] text-cyan-300">FACTTRACK</p>
            <h1 className="mt-6 max-w-md text-5xl font-semibold leading-tight text-white">
              Investigative-grade evidence review in one dark-mode workspace.
            </h1>
          </div>
          <div className="grid gap-4 text-sm text-slate-300">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">JWT protected access with automatic auth redirect handling.</div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">Offline matrix recall for courtrooms and low-connectivity fieldwork.</div>
          </div>
        </div>

        <div className="p-6 sm:p-10">
          <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">Secure access</p>
          <h2 className="mt-3 text-3xl font-semibold text-white">Log in to FACTTRACK</h2>
          <p className="mt-3 text-sm text-slate-400">Authenticate to continue to your forensic workspace.</p>

          <form
            className="mt-8 space-y-5"
            onSubmit={handleSubmit(async (values) => {
              try {
                const response = await loginUser(values)
                setAuth(response.access_token, values.email)
                navigate(location.state?.from || '/cases', { replace: true })
              } catch (error) {
                const message = error instanceof Error ? error.message : 'Unable to sign in.'
                setError('password', { message })
                pushToast({ title: 'Authentication failed', description: message })
              }
            })}
          >
            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-200">Email</span>
              <input
                type="email"
                autoComplete="email"
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                placeholder="investigator@agency.gov"
                {...register('email', { required: 'Email is required' })}
              />
              {errors.email ? <span className="text-sm text-rose-300">{errors.email.message}</span> : null}
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-200">Password</span>
              <input
                type="password"
                autoComplete="current-password"
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                placeholder="••••••••"
                {...register('password', { required: 'Password is required' })}
              />
              {errors.password ? <span className="text-sm text-rose-300">{errors.password.message}</span> : null}
            </label>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Authenticating…' : 'Log in'}
            </button>
          </form>

          <p className="mt-6 text-sm text-slate-400">
            Need an account?{' '}
            <Link className="font-medium text-cyan-300 hover:text-cyan-200" to="/register">
              Register now
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
