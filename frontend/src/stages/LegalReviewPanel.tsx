import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { startLegalReview, triggerReview } from '../api/client'
import DecisionPanel from '../components/DecisionPanel'
import DocumentUpload from '../components/DocumentUpload'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import type { Document, LegalAnalysisResult, LegalRegulationFinding, Review } from '../types'

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

  // When no review exists yet: create it then immediately trigger analysis
  const analyzeMutation = useMutation({
    mutationFn: async (docId: number) => {
      const created = await startLegalReview(vendorId)
      return triggerReview(created.id, docId)
    },
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

        {!review && (
          <div className="space-y-3">
            {documents.length === 0 ? (
              <p className="text-sm text-gray-500">Upload a legal document above to begin analysis.</p>
            ) : (
              <>
                {analyzeMutation.isError && (
                  <p className="text-sm text-red-600">{(analyzeMutation.error as Error).message}</p>
                )}
                <Button
                  onClick={() => {
                    const doc = documents[0]
                    if (doc) analyzeMutation.mutate(doc.id)
                  }}
                  disabled={analyzeMutation.isPending}
                >
                  {analyzeMutation.isPending ? 'Starting…' : 'Analyze'}
                </Button>
              </>
            )}
          </div>
        )}

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
              <div className="flex items-center gap-4 flex-wrap">
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Overall Risk</span>
                  <div className="mt-0.5"><Badge label={output.overall_risk} /></div>
                </div>
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Recommendation</span>
                  <div className="mt-0.5"><Badge label={output.recommendation} /></div>
                </div>
              </div>
              {output.summary && (
                <p className="text-sm text-gray-700 bg-gray-50 rounded-md p-3">{output.summary}</p>
              )}
              {output.conditions && output.conditions.length > 0 && (
                <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3">
                  <p className="text-sm font-medium text-yellow-800 mb-1">Conditions</p>
                  <ul className="space-y-1">
                    {output.conditions.map((c, i) => (
                      <li key={i} className="text-sm text-yellow-700 flex gap-1">
                        <span>•</span><span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      <th className="px-3 py-2">Regulation</th>
                      <th className="px-3 py-2">Article</th>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2">Finding</th>
                      <th className="px-3 py-2">Evidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {output.regulation_findings.map((f: LegalRegulationFinding, i: number) => (
                      <tr key={i}>
                        <td className="px-3 py-2 font-medium text-gray-900">{f.regulation}</td>
                        <td className="px-3 py-2 text-gray-600">{f.article}</td>
                        <td className="px-3 py-2">
                          <Badge label={f.status} />
                        </td>
                        <td className="px-3 py-2 text-gray-600 max-w-xs">
                          <EvidenceCell text={f.finding} />
                        </td>
                        <td className="px-3 py-2 text-gray-500 max-w-xs">
                          <EvidenceCell text={f.evidence} />
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
