import axios, { type InternalAxiosRequestConfig } from 'axios';

const BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // send refresh_token cookie
});

// Attach access token from localStorage to every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token!);
  });
  failedQueue = [];
}

// Automatic token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`;
          return api(originalRequest);
        });
      }
      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const { data } = await api.post<{ access_token: string }>('/auth/refresh');
        localStorage.setItem('access_token', data.access_token);
        processQueue(null, data.access_token);
        originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
  login: (email: string, password: string, totp_code?: string) =>
    api.post<{ access_token: string | null; token_type: string; mfa_required: boolean }>(
      '/auth/login',
      { email, password, totp_code }
    ),
  setupMfa: () =>
    api.post<{ totp_uri: string; qr_code_base64: string }>('/auth/mfa/setup'),
  verifyMfa: (totp_code: string) =>
    api.post('/auth/mfa/verify', { totp_code }),
  refresh: () =>
    api.post<{ access_token: string }>('/auth/refresh'),
  logout: () =>
    api.post('/auth/logout'),
};

// ─── Cases ────────────────────────────────────────────────────────────────────
export const casesApi = {
  list: () => api.get('/cases'),
  get: (id: string) => api.get(`/cases/${id}`),
  create: (name: string, description?: string) =>
    api.post('/cases', { name, description }),
  update: (id: string, data: { name?: string; description?: string }) =>
    api.patch(`/cases/${id}`, data),
  archive: (id: string) =>
    api.post(`/cases/${id}/archive`),
  listMembers: (id: string) =>
    api.get(`/cases/${id}/members`),
  addMember: (id: string, user_id: string, case_role: string) =>
    api.post(`/cases/${id}/members`, { user_id, case_role }),
  removeMember: (id: string, userId: string) =>
    api.delete(`/cases/${id}/members/${userId}`),
};

// ─── Evidence ─────────────────────────────────────────────────────────────────
export const evidenceApi = {
  list: (caseId: string, page = 1, pageSize = 50) =>
    api.get(`/cases/${caseId}/evidence`, { params: { page, page_size: pageSize } }),
  get: (caseId: string, evidenceId: string) =>
    api.get(`/cases/${caseId}/evidence/${evidenceId}`),
  upload: (caseId: string, file: File, description?: string) => {
    const form = new FormData();
    form.append('file', file);
    if (description) form.append('description', description);
    return api.post(`/cases/${caseId}/evidence`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  downloadUrl: (caseId: string, evidenceId: string) =>
    `${BASE_URL}/cases/${caseId}/evidence/${evidenceId}/download`,
  getArtifacts: (caseId: string, evidenceId: string) =>
    api.get(`/cases/${caseId}/evidence/${evidenceId}/artifacts`),
};

// ─── Audit ────────────────────────────────────────────────────────────────────
export const auditApi = {
  listForCase: (caseId: string, page = 1, pageSize = 50) =>
    api.get(`/audit/cases/${caseId}`, { params: { page, page_size: pageSize } }),
  verifyCase: (caseId: string) =>
    api.get(`/audit/verify/cases/${caseId}`),
  verify: () =>
    api.get('/audit/verify'),
};
