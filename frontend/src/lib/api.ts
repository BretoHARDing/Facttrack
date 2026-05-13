import axios from 'axios'
import { useAuthStore } from '../store/auth'

export type RegisterInput = {
  email: string
  password: string
  display_name: string
}

export type RegisterResponse = {
  user_id: string
  access_token: string
}

export type LoginInput = {
  email: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

export type CreateCaseInput = {
  title: string
  jurisdiction: string
}

export type CreateCaseResponse = {
  case_id: string
  title: string
}

export type UploadEvidenceInput = {
  file: File
  caseId: string
  title: string
  description: string
  onProgress?: (progress: number) => void
}

export type UploadEvidenceResponse = {
  evidence_id: string
  cas_hash: string
  status: string
}

export type ExtractMatrixInput = {
  evidence_id: string
}

export type ExtractMatrixResponse = {
  evidence_id: string
  matrix_output: string
}

export class ApiError extends Error {
  status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status as number | undefined
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string' ? detail : error.message || 'Request failed'

    if (status === 401) {
      useAuthStore.getState().clearAuth()
      window.dispatchEvent(new CustomEvent('facttrack:unauthorized'))
    }

    if (status && status >= 500) {
      window.dispatchEvent(
        new CustomEvent('facttrack:server-error', {
          detail: { message },
        }),
      )
    }

    return Promise.reject(new ApiError(message, status))
  },
)

export async function registerUser(input: RegisterInput) {
  const { data } = await api.post<RegisterResponse>('/api/v1/auth/register', input)
  return data
}

export async function loginUser(input: LoginInput) {
  const { data } = await api.post<LoginResponse>('/api/v1/auth/login', input)
  return data
}

export async function createCase(input: CreateCaseInput) {
  const { data } = await api.post<CreateCaseResponse>('/api/v1/cases/', input)
  return data
}

export async function uploadEvidence(input: UploadEvidenceInput) {
  const formData = new FormData()
  formData.append('file', input.file)
  formData.append('case_id', input.caseId)
  formData.append('title', input.title)
  formData.append('description', input.description)

  const { data } = await api.post<UploadEvidenceResponse>('/api/v1/evidence/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (event) => {
      if (!input.onProgress || !event.total) {
        return
      }

      input.onProgress(Math.round((event.loaded / event.total) * 100))
    },
  })

  return data
}

export async function extractMatrix(input: ExtractMatrixInput) {
  const { data } = await api.post<ExtractMatrixResponse>('/api/v1/ai/extract-matrix', input)
  return data
}
