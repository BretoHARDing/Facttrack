import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { registerUser } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useToast } from '../hooks/useToast'

type RegisterForm = {
  display_name: string
  email: string
  password: string
}

export function RegisterPage() {
  const navigate = useNavigate()
  const { pushToast } = useToast()
  const setAuth = useAuthStore((state) => state.setAuth)
  const token = useAuthStore((state) => state.token)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>()

  useEffect(() => {
    if (token) {
      navigate('/cases', { replace: true })
    }
  }, [navigate, token])

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl items-center justify-center px-4 py-10">
      <div className="grid w-full overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 shadow-2xl shadow-violet-950/20 backdrop-blur-xl lg:grid-cols-[0.9fr_1.1fr]">
        <div className="p-6 sm:p-10">
          <p className="text-sm uppercase tracking-[0.3em] text-violet-300">Investigator onboarding</p>
          <h1 className="mt-3 text-3xl font-semibold text-white">Register a new FACTTRACK account</h1>
          <p className="mt-3 text-sm text-slate-400">Provision access for secure case analysis and evidence ingestion.</p>

          <form
            className="mt-8 space-y-5"
            onSubmit={handleSubmit(async (values) => {
              try {
                const response = await registerUser(values)
                setAuth(response.access_token, values.email)
                navigate('/cases', { replace: true })
              } catch (error) {
                const message = error instanceof Error ? error.message : 'Unable to register.'
                setError('email', { message })
                pushToast({ title: 'Registration failed', description: message })
              }
            })}
          >
            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-200">Display name</span>
              <input
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white placeholder:text-slate-500 focus:border-violet-400 focus:outline-none"
                placeholder="Detective Ada Lovelace"
                {...register('display_name', { required: 'Display name is required' })}
              />
              {errors.display_name ? <span className="text-sm text-rose-300">{errors.display_name.message}</span> : null}
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-200">Email</span>
              <input
                type="email"
                autoComplete="email"
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white placeholder:text-slate-500 focus:border-violet-400 focus:outline-none"
                placeholder="investigator@agency.gov"
                {...register('email', { required: 'Email is required' })}
              />
              {errors.email ? <span className="text-sm text-rose-300">{errors.email.message}</span> : null}
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-200">Password</span>
              <input
                type="password"
                autoComplete="new-password"
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white placeholder:text-slate-500 focus:border-violet-400 focus:outline-none"
                placeholder="Minimum 8 characters"
                {...register('password', {
                  required: 'Password is required',
                  minLength: { value: 8, message: 'Password must be at least 8 characters' },
                })}
              />
              {errors.password ? <span className="text-sm text-rose-300">{errors.password.message}</span> : null}
            </label>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-2xl bg-violet-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-violet-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Provisioning…' : 'Create account'}
            </button>
          </form>

          <p className="mt-6 text-sm text-slate-400">
            Already registered?{' '}
            <Link className="font-medium text-violet-300 hover:text-violet-200" to="/login">
              Sign in
            </Link>
          </p>
        </div>

        <div className="hidden bg-[radial-gradient(circle_at_bottom,_rgba(167,139,250,0.18),_transparent_45%),linear-gradient(135deg,#111827,#020617)] p-10 lg:flex lg:flex-col lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.4em] text-violet-300">Zero trust</p>
            <h2 className="mt-6 max-w-md text-5xl font-semibold leading-tight text-white">
              Prepare a premium forensic dashboard for high-stakes evidence review.
            </h2>
          </div>
          <div className="grid gap-4 text-sm text-slate-300">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">Dark-mode-first interface with glassmorphism overlays.</div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">Matrix outputs are cached offline via IndexedDB for court-ready recall.</div>
          </div>
        </div>
      </div>
    </div>
  )
}
