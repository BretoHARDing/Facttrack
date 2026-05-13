import { useForm } from 'react-hook-form'

type CreateCaseForm = {
  title: string
  jurisdiction: string
}

type CreateCaseModalProps = {
  open: boolean
  submitting: boolean
  onClose: () => void
  onSubmit: (values: CreateCaseForm) => Promise<void>
}

const JURISDICTIONS = ['NSW', 'VIC', 'QLD', 'ACT', 'SA', 'WA', 'TAS', 'NT']

export function CreateCaseModal({ open, submitting, onClose, onSubmit }: CreateCaseModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateCaseForm>({
    defaultValues: {
      jurisdiction: 'NSW',
    },
  })

  if (!open) {
    return null
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-md">
      <div className="w-full max-w-xl rounded-3xl border border-white/10 bg-white/10 p-6 shadow-2xl shadow-cyan-950/30 backdrop-blur-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">Create case</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Open a new forensic workspace</h2>
          </div>
          <button
            type="button"
            className="rounded-full border border-white/10 px-3 py-1 text-sm text-slate-300 transition hover:border-white/20 hover:text-white"
            onClick={() => {
              reset()
              onClose()
            }}
          >
            Close
          </button>
        </div>

        <form
          className="mt-6 space-y-4"
          onSubmit={handleSubmit(async (values) => {
            await onSubmit(values)
            reset({ title: '', jurisdiction: values.jurisdiction })
          })}
        >
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-200">Case title</span>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none ring-0 placeholder:text-slate-500 focus:border-cyan-400"
              placeholder="Operation Harbour"
              {...register('title', { required: 'Title is required' })}
            />
            {errors.title ? <span className="text-sm text-rose-300">{errors.title.message}</span> : null}
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-200">Jurisdiction</span>
            <select
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none focus:border-cyan-400"
              {...register('jurisdiction', { required: true })}
            >
              {JURISDICTIONS.map((jurisdiction) => (
                <option key={jurisdiction} value={jurisdiction}>
                  {jurisdiction}
                </option>
              ))}
            </select>
          </label>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? 'Securing workspace…' : 'Create case'}
          </button>
        </form>
      </div>
    </div>
  )
}
