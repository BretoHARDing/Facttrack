import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { ToastContext } from '../hooks/useToast'

type Toast = {
  id: number
  title: string
  description: string
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const pushToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const nextToast = { ...toast, id: Date.now() + Math.floor(Math.random() * 1000) }
    setToasts((current) => [...current, nextToast])
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== nextToast.id))
    }, 4200)
  }, [])

  const value = useMemo(() => ({ pushToast }), [pushToast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="rounded-2xl border border-rose-400/30 bg-slate-950/90 p-4 text-left shadow-2xl shadow-black/40 backdrop-blur-xl"
          >
            <p className="text-sm font-semibold text-rose-200">{toast.title}</p>
            <p className="mt-1 text-sm text-slate-300">{toast.description}</p>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

