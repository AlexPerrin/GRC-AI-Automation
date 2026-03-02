import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createDecision, listReviewDecisions } from '../api/client'
import type { DecisionAction } from '../types'
import Button from './ui/Button'

interface DecisionPanelProps {
  reviewId: number
  vendorId: number
}

const ACTION_LABEL: Record<string, string> = {
  APPROVE: 'Approved',
  APPROVE_WITH_CONDITIONS: 'Approved with Conditions',
  REJECT: 'Rejected',
}

export default function DecisionPanel({ reviewId, vendorId }: DecisionPanelProps) {
  const queryClient = useQueryClient()
  const [rationale, setRationale] = useState('')
  const [conditions, setConditions] = useState<string[]>([''])
  const [expanded, setExpanded] = useState<DecisionAction | null>(null)

  const { data: decisions } = useQuery({
    queryKey: ['review-decisions', reviewId],
    queryFn: () => listReviewDecisions(reviewId),
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['review-decisions', reviewId] })
    void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendorId)] })
    void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendorId)] })
    void queryClient.invalidateQueries({ queryKey: ['vendor-decisions', String(vendorId)] })
    void queryClient.invalidateQueries({ queryKey: ['audit-logs', String(vendorId)] })
  }

  const mutation = useMutation({
    mutationFn: (action: DecisionAction) =>
      createDecision(reviewId, {
        actor: 'Dev User',
        action,
        rationale,
        conditions: action === 'APPROVE_WITH_CONDITIONS' ? conditions.filter(Boolean) : undefined,
      }),
    onSuccess: invalidate,
  })

  const handleAction = (action: DecisionAction) => {
    if (action === 'REJECT') {
      if (!confirm('Are you sure you want to reject?')) return
    }
    mutation.mutate(action)
  }

  const addCondition = () => setConditions((c) => [...c, ''])
  const removeCondition = (i: number) => setConditions((c) => c.filter((_, idx) => idx !== i))
  const updateCondition = (i: number, val: string) =>
    setConditions((c) => c.map((v, idx) => (idx === i ? val : v)))

  // Show banner if a decision has already been recorded
  const existingDecision = decisions?.[decisions.length - 1]
  if (existingDecision) {
    const isApproved = existingDecision.action === 'APPROVE' || existingDecision.action === 'APPROVE_WITH_CONDITIONS'
    const isRejected = existingDecision.action === 'REJECT'
    return (
      <div className={`rounded-md border p-4 space-y-2 ${
        isApproved ? 'bg-green-50 border-green-200' :
        isRejected ? 'bg-red-50 border-red-200' :
        'bg-gray-50 border-gray-200'
      }`}>
        <div className="flex items-center gap-2">
          {isApproved && (
            <svg className="h-4 w-4 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          )}
          {isRejected && (
            <svg className="h-4 w-4 text-red-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          )}
          <span className={`text-sm font-semibold ${isApproved ? 'text-green-800' : isRejected ? 'text-red-800' : 'text-gray-800'}`}>
            {ACTION_LABEL[existingDecision.action] ?? existingDecision.action}
          </span>
          <span className="text-xs text-gray-500 ml-auto">by {existingDecision.actor}</span>
        </div>
        {existingDecision.rationale && (
          <p className="text-xs text-gray-600">{existingDecision.rationale}</p>
        )}
        {existingDecision.conditions && existingDecision.conditions.length > 0 && (
          <ul className="space-y-0.5 list-disc list-inside">
            {existingDecision.conditions.map((c, i) => (
              <li key={i} className="text-xs text-gray-600">{c}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4 rounded-md border border-gray-200 bg-gray-50 p-4">
      <h4 className="text-sm font-semibold text-gray-900">Decision</h4>
      {mutation.isError && (
        <p className="text-sm text-red-600">{(mutation.error as Error).message}</p>
      )}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Rationale</label>
        <textarea
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="Enter rationale…"
        />
      </div>

      {expanded === 'APPROVE_WITH_CONDITIONS' && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Conditions</label>
          {conditions.map((c, i) => (
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

      <div className="flex flex-wrap gap-2">
        <Button
          onClick={() => handleAction('APPROVE')}
          disabled={!rationale || mutation.isPending}
        >
          Approve
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            setExpanded((e) => (e === 'APPROVE_WITH_CONDITIONS' ? null : 'APPROVE_WITH_CONDITIONS'))
          }}
        >
          Approve with Conditions
        </Button>
        {expanded === 'APPROVE_WITH_CONDITIONS' && (
          <Button
            onClick={() => handleAction('APPROVE_WITH_CONDITIONS')}
            disabled={!rationale || mutation.isPending}
          >
            Confirm Conditional Approval
          </Button>
        )}
        <Button
          variant="danger"
          onClick={() => handleAction('REJECT')}
          disabled={!rationale || mutation.isPending}
        >
          Reject
        </Button>
      </div>
    </div>
  )
}
