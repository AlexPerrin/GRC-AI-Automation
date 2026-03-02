import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { submitForm } from '../api/client'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import type { Review, UseCaseFormInput } from '../types'

const DATA_TYPES = [
  'Personal Data',
  'Financial Data',
  'Health Data',
  'Employee Data',
  'Public Data',
]

const EMPTY_FORM: UseCaseFormInput = {
  use_case_description: '',
  business_justification: '',
  data_types_involved: [],
  estimated_users: 0,
  alternatives_considered: '',
  reviewer_name: '',
  recommendation: 'PROCEED',
  notes: '',
}

interface UseCasePanelProps {
  review: Review | undefined
  vendorId: number
}

export default function UseCasePanel({ review, vendorId }: UseCasePanelProps) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<UseCaseFormInput>(EMPTY_FORM)

  const mutation = useMutation({
    mutationFn: (data: UseCaseFormInput) => submitForm(review!.id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendorId)] })
      void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendorId)] })
      void queryClient.invalidateQueries({ queryKey: ['audit-logs', String(vendorId)] })
    },
  })

  const toggleDataType = (type: string) => {
    setForm((f) => ({
      ...f,
      data_types_involved: f.data_types_involved.includes(type)
        ? f.data_types_involved.filter((t) => t !== type)
        : [...f.data_types_involved, type],
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(form)
  }

  // Show read-only view when complete
  if (review?.status === 'COMPLETE' && review.form_input) {
    const fi = review.form_input as Record<string, unknown>
    return (
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">Use Case Review — Complete</h3>
        <dl className="space-y-3">
          {Object.entries(fi).map(([key, val]) => (
            <div key={key}>
              <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                {key.replace(/_/g, ' ')}
              </dt>
              <dd className="mt-0.5 text-sm text-gray-900">
                {key === 'recommendation' ? (
                  <Badge label={String(val)} />
                ) : Array.isArray(val) ? (
                  val.join(', ') || '—'
                ) : val !== null && val !== undefined && val !== '' ? (
                  String(val)
                ) : (
                  '—'
                )}
              </dd>
            </div>
          ))}
        </dl>
      </Card>
    )
  }

  // Show spinner if in progress
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

  // No review yet or PENDING — show form
  if (!review) {
    return (
      <Card>
        <p className="text-sm text-gray-500">
          The Use Case review has not been created yet. It will appear once intake is started.
        </p>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-base font-semibold text-gray-900 mb-6">Use Case Review Form</h3>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Use Case Description <span className="text-red-500">*</span>
          </label>
          <textarea
            value={form.use_case_description}
            onChange={(e) => setForm((f) => ({ ...f, use_case_description: e.target.value }))}
            rows={3}
            required
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Business Justification <span className="text-red-500">*</span>
          </label>
          <textarea
            value={form.business_justification}
            onChange={(e) => setForm((f) => ({ ...f, business_justification: e.target.value }))}
            rows={3}
            required
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-2">
            Data Types Involved
          </span>
          <div className="flex flex-wrap gap-3">
            {DATA_TYPES.map((type) => (
              <label key={type} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.data_types_involved.includes(type)}
                  onChange={() => toggleDataType(type)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                {type}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Estimated Users <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            min={0}
            value={form.estimated_users}
            onChange={(e) => setForm((f) => ({ ...f, estimated_users: Number(e.target.value) }))}
            required
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Alternatives Considered <span className="text-red-500">*</span>
          </label>
          <textarea
            value={form.alternatives_considered}
            onChange={(e) => setForm((f) => ({ ...f, alternatives_considered: e.target.value }))}
            rows={2}
            required
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
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

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-2">Recommendation</span>
          <div className="flex gap-4">
            {(['PROCEED', 'DO_NOT_PROCEED'] as const).map((opt) => (
              <label key={opt} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="radio"
                  name="recommendation"
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

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
          <textarea
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            rows={2}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {mutation.isError && (
          <p className="text-sm text-red-600">{(mutation.error as Error).message}</p>
        )}

        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Submitting…' : 'Submit Use Case Review'}
        </Button>
      </form>
    </Card>
  )
}
