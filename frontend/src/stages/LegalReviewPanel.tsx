import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { triggerReview } from '../api/client'
import DecisionPanel from '../components/DecisionPanel'
import DocumentUpload from '../components/DocumentUpload'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import type { Document, LegalAnalysisResult, Review } from '../types'

interface LegalReviewPanelProps {
  review: Review | undefined
  documents: Document[]
  vendorId: number
}

function EvidenceCell({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false)
  if (text.length <= 120) return <span>{text}</span>
  return (
    <span>
      {expanded ? text : `${text.slice(0, 120)}…`}
      <button
        onClick={() => setExpanded((e) => !e)}
        className="ml-1 text-blue-500 hover:underline text-xs"
      >
        {expanded ? 'less' : 'more'}
      </button>
    </span>
  )
}

export default function LegalReviewPanel({ review, documents, vendorId }: LegalReviewPanelProps) {
  const queryClient = useQueryClient()

  const triggerMutation = useMutation({
    mutationFn: (docId: number) => triggerReview(review!.id, docId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendorId)] })
    },
  })

  const hasDecision = (review?.status === 'COMPLETE') // decisions checked via review's parent

  return (
    <div className="space-y-6">
      {/* Document Upload */}
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">Legal Documents</h3>
        <DocumentUpload
          vendorId={vendorId}
          stage="LEGAL"
          docType="privacy_policy"
          documents={documents}
        />
      </Card>

      {/* Analysis Section */}
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">AI Legal Analysis</h3>

        {!review && <p className="text-sm text-gray-500">No review available yet.</p>}

        {review && review.status === 'PENDING' && (
          <Button
            onClick={() => {
              const doc = documents[0]
              if (doc) triggerMutation.mutate(doc.id)
            }}
            disabled={documents.length === 0 || triggerMutation.isPending}
          >
            {triggerMutation.isPending ? 'Starting…' : 'Run AI Analysis'}
          </Button>
        )}

        {review?.status === 'IN_PROGRESS' && (
          <div className="flex items-center gap-2 text-gray-600">
            <Spinner />
            <span className="text-sm">Analysis in progress…</span>
          </div>
        )}

        {review?.status === 'ERROR' && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-sm text-red-700">Analysis failed. Please try again.</p>
            <Button
              variant="danger"
              className="mt-2"
              onClick={() => {
                const doc = documents[0]
                if (doc) triggerMutation.mutate(doc.id)
              }}
              disabled={documents.length === 0}
            >
              Retry
            </Button>
          </div>
        )}

        {review?.status === 'COMPLETE' && review.ai_output && (() => {
          const output = review.ai_output as LegalAnalysisResult
          return (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">Overall compliance:</span>
                <Badge label={output.overall_compliance} />
              </div>
              {output.summary && (
                <p className="text-sm text-gray-700 bg-gray-50 rounded-md p-3">{output.summary}</p>
              )}
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      <th className="px-3 py-2">Requirement</th>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2">Evidence</th>
                      <th className="px-3 py-2">Gap</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {output.findings.map((f, i) => (
                      <tr key={i}>
                        <td className="px-3 py-2 font-medium text-gray-900">{f.requirement}</td>
                        <td className="px-3 py-2">
                          <Badge label={f.status} />
                        </td>
                        <td className="px-3 py-2 text-gray-600 max-w-xs">
                          <EvidenceCell text={f.evidence} />
                        </td>
                        <td className="px-3 py-2 text-gray-500">
                          {f.gap_description ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
        })()}

        {review?.status === 'COMPLETE' && !hasDecision && (
          <div className="mt-6">
            <DecisionPanel reviewId={review.id} vendorId={vendorId} />
          </div>
        )}
      </Card>
    </div>
  )
}
