import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export type CaseSummary = {
  id: string
  title: string
  jurisdiction: string
  createdAt: string
}

export type EvidenceSummary = {
  id: string
  caseId: string
  title: string
  description: string
  filename: string
  status: string
  casHash: string
  progress: number
  matrixOutput?: string
  matrixCachedAt?: string
  createdAt: string
}

type WorkspaceState = {
  cases: CaseSummary[]
  activeCaseId: string | null
  evidence: EvidenceSummary[]
  addCase: (nextCase: CaseSummary) => void
  setActiveCaseId: (caseId: string | null) => void
  addEvidence: (nextEvidence: EvidenceSummary) => void
  updateEvidence: (evidenceId: string, patch: Partial<EvidenceSummary>) => void
  clearWorkspace: () => void
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      cases: [],
      activeCaseId: null,
      evidence: [],
      addCase: (nextCase) =>
        set((state) => ({
          cases: [nextCase, ...state.cases.filter((item) => item.id !== nextCase.id)],
          activeCaseId: nextCase.id,
        })),
      setActiveCaseId: (caseId) => set({ activeCaseId: caseId }),
      addEvidence: (nextEvidence) =>
        set((state) => ({
          evidence: [nextEvidence, ...state.evidence.filter((item) => item.id !== nextEvidence.id)],
        })),
      updateEvidence: (evidenceId, patch) =>
        set((state) => ({
          evidence: state.evidence.map((item) => (item.id === evidenceId ? { ...item, ...patch } : item)),
        })),
      clearWorkspace: () => set({ cases: [], activeCaseId: null, evidence: [] }),
    }),
    {
      name: 'facttrack-workspace',
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
)
