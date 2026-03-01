import type {
  AuditLog,
  Decision,
  DecisionAction,
  Document,
  DocumentStage,
  Review,
  Vendor,
} from '../types'

const BASE = import.meta.env.VITE_API_URL ?? '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json() as Promise<T>
}

function json(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

// Vendors — backend wraps list in { vendors: [], total: N }
export const listVendors = () =>
  request<{ vendors: Vendor[]; total: number }>('/vendors/').then((r) => r.vendors)
export const getVendor = (id: number | string) => request<Vendor>(`/vendors/${id}`)
export const createVendor = (data: { name: string; website?: string; description?: string }) =>
  request<Vendor>('/vendors/', json('POST', data))
export const startIntake = (id: number) =>
  request<Vendor>(`/vendors/${id}/start-intake`, { method: 'POST' })
export const confirmNda = (id: number) =>
  request<Vendor>(`/vendors/${id}/confirm-nda`, { method: 'POST' })
export const startFinancialReview = (id: number) =>
  request<Vendor>(`/vendors/${id}/start-financial-review`, { method: 'POST' })
export const completeOnboarding = (id: number) =>
  request<Vendor>(`/vendors/${id}/complete-onboarding`, { method: 'POST' })
export const rejectVendor = (id: number, rationale: string) =>
  request<Vendor>(`/vendors/${id}/reject`, json('POST', { rationale }))

// Reviews
export const listReviews = (vendorId: number | string) =>
  request<Review[]>(`/vendors/${vendorId}/reviews`)
export const getReview = (reviewId: number) => request<Review>(`/reviews/${reviewId}`)
export const triggerReview = (reviewId: number, docId: number) =>
  request<Review>(`/reviews/${reviewId}/trigger?doc_id=${docId}`, { method: 'POST' })
export const submitForm = (reviewId: number, body: unknown) =>
  request<Review>(`/reviews/${reviewId}/submit-form`, json('POST', body))

// Decisions
export const createDecision = (
  reviewId: number,
  data: { actor: string; action: DecisionAction; rationale: string; conditions?: string[] },
) => request<Decision>(`/reviews/${reviewId}/decisions`, json('POST', data))

// Documents
export const listDocuments = (vendorId: number | string) =>
  request<Document[]>(`/vendors/${vendorId}/documents`)
export const uploadDocument = (
  vendorId: number,
  stage: DocumentStage,
  docType: string,
  file: File,
) => {
  const form = new FormData()
  form.append('file', file)
  return request<Document>(
    `/vendors/${vendorId}/documents?stage=${stage}&doc_type=${docType}`,
    { method: 'POST', body: form },
  )
}

// Audit logs
export const getAuditLogs = (vendorId: number | string) =>
  request<AuditLog[]>(`/vendors/${vendorId}/audit-logs`)
