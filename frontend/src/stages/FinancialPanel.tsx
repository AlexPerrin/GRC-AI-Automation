import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { completeOnboarding, startFinancialReview, submitForm } from '../api/client'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import type { FinancialRiskFormInput, Review, Vendor } from '../types'

const FIN_DOCS = [
  'Financial Statements',
  'Credit Report',
  'Insurance Certificates',
  'Audited Accounts',
  'Bank References',
]

const EMPTY_FORM: FinancialRiskFormInput = {
  vendor_annual_revenue: '',
  years_in_operation: undefined,
  financial_documents_reviewed: [],
  concentration_risk_flag: false,
  financial_stability_assessment: 'STABLE',
  contract_value: '',
  reviewer_name: '',
  recommendation: 'ACCEPTABLE',
  conditions: [],
  notes: '',
}

interface FinancialPanelProps {
  review: Review | undefined
  vendor: Vendor
}

export default function FinancialPanel({ review, vendor }: FinancialPanelProps) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<FinancialRiskFormInput>(EMPTY_FORM)

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendor.id)] })
    void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendor.id)] })
    void queryClient.invalidateQueries({ queryKey: ['audit-logs', String(vendor.id)] })
  }

  const startMutation = useMutation({
    mutationFn: () => startFinancialReview(vendor.id),
    onSuccess: invalidate,
  })

  const submitMutation = useMutation({
    mutationFn: (data: FinancialRiskFormInput) => submitForm(review!.id, data),
    onSuccess: invalidate,
  })

  const completeMutation = useMutation({
    mutationFn: () => completeOnboarding(vendor.id),
    onSuccess: invalidate,
  })

  const toggleDoc = (doc: string) => {
    setForm((f) => ({
      ...f,
      financial_documents_reviewed: f.financial_documents_reviewed.includes(doc)
        ? f.financial_documents_reviewed.filter((d) => d !== doc)
        : [...f.financial_documents_reviewed, doc],
    }))
  }

  const addCondition = () => setForm((f) => ({ ...f, conditions: [...(f.conditions ?? []), ''] }))
  const removeCondition = (i: number) =>
    setForm((f) => ({ ...f, conditions: (f.conditions ?? []).filter((_, idx) => idx !== i) }))
  const updateCondition = (i: number, val: string) =>
    setForm((f) => ({
      ...f,
      conditions: (f.conditions ?? []).map((v, idx) => (idx === i ? val : v)),
    }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      ...form,
      vendor_annual_revenue: form.vendor_annual_revenue || undefined,
      contract_value: form.contract_value || undefined,
      notes: form.notes || undefined,
      conditions:
        form.recommendation === 'ACCEPTABLE_WITH_CONDITIONS'
          ? form.conditions?.filter(Boolean)
          : undefined,
    }
    submitMutation.mutate(payload)
  }

  // Not yet eligible
  if (
    ['INTAKE', 'USE_CASE_REVIEW', 'USE_CASE_APPROVED', 'LEGAL_REVIEW', 'LEGAL_APPROVED',
      'NDA_PENDING', 'SECURITY_REVIEW'].includes(vendor.status)
  ) {
    return (
      <Card>
        <p className="text-sm text-gray-500">
          Financial review becomes available after security approval.
        </p>
      </Card>
    )
  }

  // Show "Start" button
  if (vendor.status === 'SECURITY_APPROVED' && !review) {
    return (
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-3">Financial Risk Review</h3>
        {startMutation.isError && (
          <p className="text-sm text-red-600 mb-2">{(startMutation.error as Error).message}</p>
        )}
        <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
          {startMutation.isPending ? 'Starting…' : 'Start Financial Review'}
        </Button>
      </Card>
    )
  }

  // Spinner
  if (review?.status === 'IN_PROGRESS') {
    return (
      <Card>
        <div className="flex items-center gap-2 text-gray-600">
          <Spinner />
          <span className="text-sm">Processing…</span>
        </div>
      </Card>
    )
  }

  // Complete — read-only
  if (review?.status === 'COMPLETE' && review.form_input) {
    const fi = review.form_input as Record<string, unknown>
    return (
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          Financial Risk Review — Complete
        </h3>
        <dl className="space-y-3 mb-6">
          {Object.entries(fi).map(([key, val]) => (
            <div key={key}>
              <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                {key.replace(/_/g, ' ')}
              </dt>
              <dd className="mt-0.5 text-sm text-gray-900">
                {key === 'recommendation' || key === 'financial_stability_assessment' ? (
                  <Badge label={String(val)} />
                ) : Array.isArray(val) ? (
                  val.join(', ') || '—'
                ) : typeof val === 'boolean' ? (
                  val ? 'Yes' : 'No'
                ) : val !== null && val !== undefined && val !== '' ? (
                  String(val)
                ) : (
                  '—'
                )}
              </dd>
            </div>
          ))}
        </dl>
        {vendor.status === 'FINANCIAL_APPROVED' && (
          <div className="border-t border-gray-200 pt-4">
            {completeMutation.isError && (
              <p className="text-sm text-red-600 mb-2">
                {(completeMutation.error as Error).message}
              </p>
            )}
            <Button
              onClick={() => completeMutation.mutate()}
              disabled={completeMutation.isPending}
            >
              {completeMutation.isPending ? 'Completing…' : 'Complete Onboarding'}
            </Button>
          </div>
        )}
      </Card>
    )
  }

  // PENDING form
  if (!review) {
    return (
      <Card>
        <p className="text-sm text-gray-500">No financial review available yet.</p>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-base font-semibold text-gray-900 mb-6">Financial Risk Assessment Form</h3>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Annual Revenue (optional)
            </label>
            <input
              type="text"
              value={form.vendor_annual_revenue ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, vendor_annual_revenue: e.target.value }))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="e.g. $10M"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Years in Operation (optional)
            </label>
            <input
              type="number"
              min={0}
              value={form.years_in_operation ?? ''}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  years_in_operation: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-2">
            Financial Documents Reviewed
          </span>
          <div className="flex flex-wrap gap-3">
            {FIN_DOCS.map((doc) => (
              <label key={doc} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.financial_documents_reviewed.includes(doc)}
                  onChange={() => toggleDoc(doc)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                {doc}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={form.concentration_risk_flag}
              onChange={(e) => setForm((f) => ({ ...f, concentration_risk_flag: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Concentration risk flagged
          </label>
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-2">
            Financial Stability Assessment
          </span>
          <div className="flex gap-4">
            {(['STABLE', 'CONCERN', 'HIGH_RISK'] as const).map((opt) => (
              <label key={opt} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="radio"
                  name="stability"
                  value={opt}
                  checked={form.financial_stability_assessment === opt}
                  onChange={() =>
                    setForm((f) => ({ ...f, financial_stability_assessment: opt }))
                  }
                  className="text-blue-600 focus:ring-blue-500"
                />
                {opt.replace(/_/g, ' ')}
              </label>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contract Value (optional)
            </label>
            <input
              type="text"
              value={form.contract_value ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, contract_value: e.target.value }))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="e.g. $50,000/yr"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reviewer Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.reviewer_name}
              onChange={(e) => setForm((f) => ({ ...f, reviewer_name: e.target.value }))}
              required
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-2">Recommendation</span>
          <div className="flex flex-wrap gap-4">
            {(['ACCEPTABLE', 'ACCEPTABLE_WITH_CONDITIONS', 'UNACCEPTABLE'] as const).map((opt) => (
              <label key={opt} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="radio"
                  name="rec"
                  value={opt}
                  checked={form.recommendation === opt}
                  onChange={() => setForm((f) => ({ ...f, recommendation: opt }))}
                  className="text-blue-600 focus:ring-blue-500"
                />
                {opt.replace(/_/g, ' ')}
              </label>
            ))}
          </div>
        </div>

        {form.recommendation === 'ACCEPTABLE_WITH_CONDITIONS' && (
          <div className="space-y-2">
            <span className="block text-sm font-medium text-gray-700">Conditions</span>
            {(form.conditions ?? []).map((c, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={c}
                  onChange={(e) => updateCondition(i, e.target.value)}
                  className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder={`Condition ${i + 1}`}
                />
                <Button variant="ghost" onClick={() => removeCondition(i)} className="px-2 py-1">
                  ×
                </Button>
              </div>
            ))}
            <Button variant="ghost" onClick={addCondition} className="text-xs">
              + Add condition
            </Button>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
          <textarea
            value={form.notes ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            rows={2}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {submitMutation.isError && (
          <p className="text-sm text-red-600">{(submitMutation.error as Error).message}</p>
        )}

        <Button type="submit" disabled={submitMutation.isPending}>
          {submitMutation.isPending ? 'Submitting…' : 'Submit Financial Assessment'}
        </Button>
      </form>
    </Card>
  )
}
