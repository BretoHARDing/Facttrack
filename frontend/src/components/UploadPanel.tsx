import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { uploadEvidence } from '../lib/api'
import type { EvidenceSummary } from '../store/workspace'

type UploadForm = {
  title: string
  description: string
}

type UploadPanelProps = {
  activeCaseId: string
  onUploaded: (evidence: EvidenceSummary) => void
  onError: (message: string) => void
}

export function UploadPanel({ activeCaseId, onUploaded, onError }: UploadPanelProps) {
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [progress, setProgress] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UploadForm>()

  const fileLabel = useMemo(() => {
    if (!selectedFile) {
      return 'Drag exhibits here or click to select a source file.'
    }

    return `${selectedFile.name} · ${(selectedFile.size / 1024).toFixed(1)} KB`
  }, [selectedFile])

  const onDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setDragging(false)
    const file = event.dataTransfer.files[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  return (
    <form
      className="space-y-4 rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-slate-950/30"
      onSubmit={handleSubmit(async (values) => {
        if (!selectedFile) {
          onError('Select a file before uploading evidence.')
          return
        }

        setSubmitting(true)
        setProgress(0)

        try {
          const response = await uploadEvidence({
            file: selectedFile,
            caseId: activeCaseId,
            title: values.title,
            description: values.description,
            onProgress: setProgress,
          })

          onUploaded({
            id: response.evidence_id,
            caseId: activeCaseId,
            title: values.title,
            description: values.description,
            filename: selectedFile.name,
            status: response.status,
            casHash: response.cas_hash,
            progress: 100,
            createdAt: new Date().toISOString(),
          })
          reset()
          setSelectedFile(null)
          setProgress(0)
        } catch (error) {
          onError(error instanceof Error ? error.message : 'Evidence upload failed.')
        } finally {
          setSubmitting(false)
        }
      })}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Evidence ingestion</p>
          <h3 className="mt-2 text-lg font-semibold text-white">Chain-of-custody upload zone</h3>
        </div>
        <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">
          Live CAS hashing
        </div>
      </div>

      <label
        className={`block rounded-3xl border border-dashed p-6 text-center transition ${
          dragging ? 'border-cyan-300 bg-cyan-400/10' : 'border-white/15 bg-slate-950/60 hover:border-cyan-400/60'
        }`}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          type="file"
          className="hidden"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
        />
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400/10 text-cyan-300">
          ⬆
        </div>
        <p className="mt-4 text-sm font-medium text-white">Premium drag-and-drop intake</p>
        <p className="mt-2 text-sm text-slate-400">{fileLabel}</p>
      </label>

      <div className="grid gap-4 lg:grid-cols-2">
        <label className="space-y-2">
          <span className="text-sm text-slate-300">Evidence title</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
            placeholder="CCTV stills"
            {...register('title', { required: 'Evidence title is required' })}
          />
          {errors.title ? <span className="text-sm text-rose-300">{errors.title.message}</span> : null}
        </label>

        <label className="space-y-2">
          <span className="text-sm text-slate-300">Description</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
            placeholder="Original device export"
            {...register('description')}
          />
        </label>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs uppercase tracking-[0.2em] text-slate-400">
          <span>Upload progress</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-900">
          <div
            className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-violet-400 to-emerald-400 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-400 px-4 py-3 font-semibold text-slate-950 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? 'Ingesting evidence…' : 'Upload evidence'}
      </button>
    </form>
  )
}
