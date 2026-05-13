import { useEffect, useMemo, useState } from 'react'
import { createCase, extractMatrix } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useWorkspaceStore } from '../store/workspace'
import { useToast } from '../hooks/useToast'
import { CreateCaseModal } from '../components/CreateCaseModal'
import { UploadPanel } from '../components/UploadPanel'
import { MatrixRenderer } from '../components/MatrixRenderer'
import { useOfflineSync } from '../hooks/useOfflineSync'

export function CasesPage() {
  const userEmail = useAuthStore((state) => state.userEmail)
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const cases = useWorkspaceStore((state) => state.cases)
  const activeCaseId = useWorkspaceStore((state) => state.activeCaseId)
  const evidence = useWorkspaceStore((state) => state.evidence)
  const addCase = useWorkspaceStore((state) => state.addCase)
  const setActiveCaseId = useWorkspaceStore((state) => state.setActiveCaseId)
  const addEvidence = useWorkspaceStore((state) => state.addEvidence)
  const updateEvidence = useWorkspaceStore((state) => state.updateEvidence)
  const { pushToast } = useToast()
  const { online, saveMatrixResult, getMatrixResult } = useOfflineSync()
  const [createOpen, setCreateOpen] = useState(false)
  const [creatingCase, setCreatingCase] = useState(false)
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null)
  const [analysisPending, setAnalysisPending] = useState(false)

  const activeCase = useMemo(
    () => cases.find((item) => item.id === activeCaseId) ?? null,
    [activeCaseId, cases],
  )

  const caseEvidence = useMemo(
    () => evidence.filter((item) => item.caseId === activeCaseId),
    [activeCaseId, evidence],
  )

  const selectedEvidence = useMemo(
    () => caseEvidence.find((item) => item.id === selectedEvidenceId) ?? caseEvidence[0] ?? null,
    [caseEvidence, selectedEvidenceId],
  )

  useEffect(() => {
    if (!activeCaseId && cases.length) {
      setActiveCaseId(cases[0].id)
    }
  }, [activeCaseId, cases, setActiveCaseId])


  useEffect(() => {
    if (!selectedEvidence || selectedEvidence.matrixOutput) {
      return
    }

    void getMatrixResult(selectedEvidence.id).then((cached) => {
      if (cached) {
        updateEvidence(selectedEvidence.id, {
          matrixOutput: cached.matrixOutput,
          matrixCachedAt: cached.cachedAt,
        })
      }
    })
  }, [getMatrixResult, selectedEvidence, updateEvidence])

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_28%),radial-gradient(circle_at_right,_rgba(167,139,250,0.14),_transparent_30%),linear-gradient(180deg,#020617,#020617_36%,#020617)] px-4 py-6 text-slate-100 lg:px-6">
      <CreateCaseModal
        open={createOpen}
        submitting={creatingCase}
        onClose={() => setCreateOpen(false)}
        onSubmit={async (values) => {
          setCreatingCase(true)
          try {
            const response = await createCase(values)
            addCase({
              id: response.case_id,
              title: response.title,
              jurisdiction: values.jurisdiction,
              createdAt: new Date().toISOString(),
            })
            pushToast({ title: 'Case created', description: `${response.title} is ready for evidence intake.` })
            setCreateOpen(false)
          } catch (error) {
            pushToast({
              title: 'Case creation failed',
              description: error instanceof Error ? error.message : 'Unable to create case.',
            })
          } finally {
            setCreatingCase(false)
          }
        }}
      />

      <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 xl:h-[calc(100vh-3rem)] xl:flex-row">
        <aside className="flex w-full flex-col rounded-[2rem] border border-white/10 bg-white/5 p-5 backdrop-blur-xl xl:w-80">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-cyan-300">FACTTRACK</p>
              <h1 className="mt-2 text-2xl font-semibold text-white">Case workspace</h1>
            </div>
            <div className={`rounded-full px-3 py-1 text-xs font-medium ${online ? 'bg-emerald-400/10 text-emerald-200' : 'bg-amber-400/10 text-amber-200'}`}>
              {online ? 'Online' : 'Offline'}
            </div>
          </div>

          <div className="mt-6 rounded-3xl border border-white/10 bg-slate-950/50 p-4 text-sm text-slate-300">
            <p className="font-medium text-white">{userEmail ?? 'Authenticated user'}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">JWT kept in memory</p>
          </div>

          <button
            type="button"
            className="mt-5 rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300"
            onClick={() => setCreateOpen(true)}
          >
            Create case
          </button>

          <div className="mt-6 flex-1 space-y-3 overflow-y-auto pr-1">
            {cases.length ? (
              cases.map((item) => {
                const evidenceCount = evidence.filter((entry) => entry.caseId === item.id).length
                const active = item.id === activeCaseId
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`w-full rounded-3xl border px-4 py-4 text-left transition ${
                      active
                        ? 'border-cyan-400/60 bg-cyan-400/10 shadow-lg shadow-cyan-950/30'
                        : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
                    }`}
                    onClick={() => setActiveCaseId(item.id)}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-white">{item.title}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">{item.jurisdiction}</p>
                      </div>
                      <span className="rounded-full bg-slate-950/80 px-3 py-1 text-xs text-slate-300">{evidenceCount}</span>
                    </div>
                    <p className="mt-3 text-xs text-slate-500">Opened {new Date(item.createdAt).toLocaleString()}</p>
                  </button>
                )
              })
            ) : (
              <div className="rounded-3xl border border-dashed border-white/10 bg-slate-950/40 p-5 text-sm text-slate-400">
                Create your first case to start reviewing evidence.
              </div>
            )}
          </div>

          <button
            type="button"
            className="mt-4 rounded-2xl border border-white/10 px-4 py-3 text-sm text-slate-300 transition hover:border-white/20 hover:text-white"
            onClick={() => {
              clearAuth()
              pushToast({ title: 'Signed out', description: 'Your secure session has been cleared.' })
            }}
          >
            Clear session
          </button>
        </aside>

        <main className="flex-1 rounded-[2rem] border border-white/10 bg-white/5 p-4 shadow-2xl shadow-black/20 backdrop-blur-xl md:p-6">
          <div className="flex flex-col gap-4 xl:h-full">
            <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-cyan-300">Forensic dashboard</p>
                <h2 className="mt-2 text-3xl font-semibold text-white">
                  {activeCase ? activeCase.title : 'Open or create a case'}
                </h2>
                <p className="mt-3 max-w-2xl text-sm text-slate-400">
                  Review uploaded evidence, verify content-addressed storage hashes, and run NSW Evidence Matrix extraction.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  className="rounded-2xl border border-white/10 px-4 py-3 text-sm text-slate-300 transition hover:border-white/20 hover:text-white xl:hidden"
                  onClick={() => setCreateOpen(true)}
                >
                  Create case
                </button>
                <div className={`rounded-full px-3 py-1 text-xs font-medium ${online ? 'bg-emerald-400/10 text-emerald-200' : 'bg-amber-400/10 text-amber-200'}`}>
                  {online ? 'Realtime sync available' : 'Offline cache only'}
                </div>
              </div>
            </header>

            {activeCase ? (
              <div className="grid gap-6 xl:h-full xl:grid-cols-[1.25fr_1fr] xl:grid-rows-[auto_1fr]">
                <UploadPanel
                  activeCaseId={activeCase.id}
                  onUploaded={(nextEvidence) => {
                    addEvidence(nextEvidence)
                    setSelectedEvidenceId(nextEvidence.id)
                    pushToast({ title: 'Evidence uploaded', description: `CAS hash ${nextEvidence.casHash.slice(0, 12)}… recorded.` })
                  }}
                  onError={(message) => pushToast({ title: 'Upload failed', description: message })}
                />

                <section className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-slate-950/20 xl:row-span-2">
                  <div className="flex flex-col gap-3 border-b border-white/10 pb-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Evidence matrix</p>
                      <h3 className="mt-2 text-xl font-semibold text-white">NSW Evidence Matrix v2</h3>
                    </div>
                    <button
                      type="button"
                      disabled={!selectedEvidence || analysisPending || !online}
                      className="rounded-2xl bg-gradient-to-r from-violet-400 to-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                      onClick={async () => {
                        if (!selectedEvidence) {
                          return
                        }

                        setAnalysisPending(true)
                        try {
                          const response = await extractMatrix({ evidence_id: selectedEvidence.id })
                          const cachedAt = new Date().toISOString()
                          updateEvidence(selectedEvidence.id, { matrixOutput: response.matrix_output, matrixCachedAt: cachedAt })
                          await saveMatrixResult({
                            evidenceId: selectedEvidence.id,
                            caseId: selectedEvidence.caseId,
                            title: selectedEvidence.title,
                            matrixOutput: response.matrix_output,
                            cachedAt,
                          })
                          pushToast({ title: 'Analysis complete', description: 'Matrix cached for offline access.' })
                        } catch (error) {
                          pushToast({
                            title: 'Analysis failed',
                            description: error instanceof Error ? error.message : 'Unable to extract matrix.',
                          })
                        } finally {
                          setAnalysisPending(false)
                        }
                      }}
                    >
                      {analysisPending ? 'Running analysis…' : online ? 'Run analysis' : 'Reconnect to run analysis'}
                    </button>
                  </div>

                  <div className="mt-5 h-full overflow-y-auto pr-1">
                    {selectedEvidence ? (
                      <div className="space-y-4">
                        <div className="rounded-3xl border border-cyan-400/20 bg-cyan-400/5 p-4">
                          <div className="flex flex-wrap items-center gap-3">
                            <span className="rounded-full bg-slate-950/80 px-3 py-1 text-xs font-medium uppercase tracking-[0.15em] text-cyan-200">
                              {selectedEvidence.status}
                            </span>
                            <span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">
                              CAS {selectedEvidence.casHash}
                            </span>
                            {selectedEvidence.matrixCachedAt ? (
                              <span className="rounded-full bg-violet-400/10 px-3 py-1 text-xs font-medium text-violet-200">
                                Cached {new Date(selectedEvidence.matrixCachedAt).toLocaleString()}
                              </span>
                            ) : null}
                          </div>
                          <p className="mt-3 text-lg font-semibold text-white">{selectedEvidence.title}</p>
                          <p className="mt-1 text-sm text-slate-400">{selectedEvidence.description || selectedEvidence.filename}</p>
                        </div>

                        {analysisPending ? (
                          <div className="space-y-4">
                            {Array.from({ length: 3 }).map((_, index) => (
                              <div key={index} className="animate-pulse rounded-3xl border border-white/10 bg-slate-950/70 p-5">
                                <div className="h-4 w-32 rounded bg-slate-800" />
                                <div className="mt-4 h-3 w-full rounded bg-slate-900" />
                                <div className="mt-2 h-3 w-5/6 rounded bg-slate-900" />
                                <div className="mt-2 h-24 rounded-2xl bg-slate-900" />
                              </div>
                            ))}
                          </div>
                        ) : selectedEvidence.matrixOutput ? (
                          <MatrixRenderer output={selectedEvidence.matrixOutput} />
                        ) : (
                          <div className="rounded-3xl border border-dashed border-white/10 bg-slate-950/50 p-8 text-center text-sm text-slate-400">
                            {online
                              ? 'Run AI analysis to generate the NSW Evidence Matrix and cache it for offline access.'
                              : 'No cached matrix available for this exhibit yet. Reconnect and run analysis once.'}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="rounded-3xl border border-dashed border-white/10 bg-slate-950/50 p-8 text-center text-sm text-slate-400">
                        Upload evidence to inspect extracted matrices in this split-pane view.
                      </div>
                    )}
                  </div>
                </section>

                <section className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-slate-950/20">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Uploaded evidence</p>
                      <h3 className="mt-2 text-xl font-semibold text-white">Case exhibits</h3>
                    </div>
                    <span className="rounded-full bg-slate-950/70 px-3 py-1 text-xs font-medium text-slate-300">
                      {caseEvidence.length} items
                    </span>
                  </div>

                  <div className="mt-5 max-h-[28rem] space-y-3 overflow-y-auto pr-1">
                    {caseEvidence.length ? (
                      caseEvidence.map((item) => {
                        const active = item.id === selectedEvidence?.id
                        return (
                          <button
                            key={item.id}
                            type="button"
                            className={`w-full rounded-3xl border p-4 text-left transition ${
                              active
                                ? 'border-violet-400/40 bg-violet-400/10 shadow-lg shadow-violet-950/20'
                                : 'border-white/10 bg-slate-950/40 hover:border-white/20 hover:bg-slate-950/70'
                            }`}
                            onClick={() => setSelectedEvidenceId(item.id)}
                          >
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <div>
                                <p className="font-semibold text-white">{item.title}</p>
                                <p className="mt-1 text-sm text-slate-400">{item.filename}</p>
                              </div>
                              <div className="flex flex-wrap items-center gap-2 text-xs">
                                <span className="rounded-full bg-slate-900 px-3 py-1 text-slate-300">{item.status}</span>
                                {item.matrixOutput ? (
                                  <span className="rounded-full bg-emerald-400/10 px-3 py-1 text-emerald-200">Offline ready</span>
                                ) : null}
                              </div>
                            </div>
                            <div className="mt-4 flex items-center gap-3">
                              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-900">
                                <div
                                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-400 transition-all duration-500"
                                  style={{ width: `${item.progress}%` }}
                                />
                              </div>
                              <span className="text-xs uppercase tracking-[0.2em] text-slate-500">{item.progress}%</span>
                            </div>
                            <p className="mt-3 break-all text-xs text-slate-500">CAS hash · {item.casHash}</p>
                          </button>
                        )
                      })
                    ) : (
                      <div className="rounded-3xl border border-dashed border-white/10 bg-slate-950/50 p-8 text-center text-sm text-slate-400">
                        No exhibits uploaded for this case yet.
                      </div>
                    )}
                  </div>
                </section>
              </div>
            ) : (
              <div className="flex flex-1 items-center justify-center rounded-[2rem] border border-dashed border-white/10 bg-slate-950/40 p-10 text-center">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">Ready to begin</p>
                  <h3 className="mt-4 text-3xl font-semibold text-white">Open a case to start evidence tracking</h3>
                  <p className="mt-4 max-w-xl text-sm text-slate-400">
                    Create a case workspace, ingest evidence with drag-and-drop upload, and run AI-powered matrix analysis with offline recall.
                  </p>
                  <button
                    type="button"
                    className="mt-6 rounded-2xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300"
                    onClick={() => setCreateOpen(true)}
                  >
                    Create your first case
                  </button>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
