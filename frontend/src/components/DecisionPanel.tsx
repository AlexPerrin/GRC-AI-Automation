import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createDecision } from '../api/client'
import type { DecisionAction } from '../types'
import Button from './ui/Button'

interface DecisionPanelProps {
  reviewId: number
  vendorId: number
}

export default function DecisionPanel({ reviewId, vendorId }: DecisionPanelProps) {
  const queryClient = useQueryClient()
  const [rationale, setRationale] = useState('')
  const [conditions, setConditions] = useState<string[]>([''])
  const [expanded, setExpanded] = useState<DecisionAction | null>(null)

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendorId)] })
    void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendorId)] })
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
