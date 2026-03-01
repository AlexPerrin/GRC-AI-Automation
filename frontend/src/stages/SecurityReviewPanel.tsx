import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { confirmNda, triggerReview } from '../api/client'
import DecisionPanel from '../components/DecisionPanel'
import DocumentUpload from '../components/DocumentUpload'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import type { Document, Review, SecurityAnalysisResult, Vendor } from '../types'

interface SecurityReviewPanelProps {
  review: Review | undefined
  documents: Document[]
  vendor: Vendor
}

const riskColors: Record<string, string> = {
  LOW: 'border-green-200 bg-green-50',
  MEDIUM: 'border-yellow-200 bg-yellow-50',
  HIGH: 'border-orange-200 bg-orange-50',
  CRITICAL: 'border-red-200 bg-red-50',
}

function DomainCard({ domain }: { domain: SecurityAnalysisResult['domains'][number] }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)
  return (
    <div className={`rounded-lg border p-4 ${riskColors[domain.risk_level] ?? 'border-gray-200 bg-white'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-900 text-sm">{domain.domain}</span>
        <Badge label={domain.risk_level} />
      </div>
      {domain.findings.length > 0 && (
        <ul className="text-xs text-gray-700 space-y-1 mb-2">
          {domain.findings.map((f, i) => (
            <li key={i} className="flex gap-1">
              <span className="mt-0.5">•</span>
              <span>{f}</span>
            </li>
          ))}
        </ul>
      )}
      {domain.evidence.length > 0 && (
        <div>
          {domain.evidence.map((e, i) => (
            <div key={i} className="text-xs text-gray-500">
              <button
                onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                className="text-blue-500 hover:underline"
              >
                {expandedIdx === i ? 'hide evidence' : 'show evidence'}
              </button>
              {expandedIdx === i && (
                <p className="mt-1 rounded bg-white/60 p-1">{e}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function SecurityReviewPanel({ review, documents, vendor }: SecurityReviewPanelProps) {
  const queryClient = useQueryClient()

  const ndaMutation = useMutation({
    mutationFn: () => confirmNda(vendor.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendor.id)] })
    },
  })

  const triggerMutation = useMutation({
    mutationFn: (docId: number) => triggerReview(review!.id, docId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendor.id)] })
    },
  })

  // NDA gate
  if (vendor.status === 'LEGAL_APPROVED') {
    return (
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-2">NDA Required</h3>
        <p className="text-sm text-gray-600 mb-4">
          NDA execution must be confirmed before the security review can begin.
        </p>
        {ndaMutation.isError && (
          <p className="text-sm text-red-600 mb-2">{(ndaMutation.error as Error).message}</p>
        )}
        <Button onClick={() => ndaMutation.mutate()} disabled={ndaMutation.isPending}>
          {ndaMutation.isPending ? 'Confirming…' : 'Confirm NDA Executed'}
        </Button>
      </Card>
    )
  }

  // Not yet at NDA stage
  if (
    ['INTAKE', 'USE_CASE_REVIEW', 'USE_CASE_APPROVED', 'LEGAL_REVIEW'].includes(vendor.status)
  ) {
    return (
      <Card>
        <p className="text-sm text-gray-500">Security review will be available after legal approval and NDA confirmation.</p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">Security Documents</h3>
        <DocumentUpload
          vendorId={vendor.id}
          stage="SECURITY"
          docType="soc2"
          documents={documents}
        />
      </Card>

      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">AI Security Analysis</h3>

        {!review && <p className="text-sm text-gray-500">No review available yet.</p>}

        {review?.status === 'PENDING' && (
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
          const output = review.ai_output as SecurityAnalysisResult
          return (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Risk Score</span>
                  <p className="text-2xl font-bold text-gray-900">{output.overall_risk_score}/10</p>
                </div>
                {output.recommendation && (
                  <div className="flex-1">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Recommendation</span>
                    <p className="text-sm text-gray-800 mt-0.5">{output.recommendation}</p>
                  </div>
                )}
              </div>

              {output.critical_gaps.length > 0 && (
                <div className="rounded-md bg-red-50 border border-red-200 p-3">
                  <p className="text-sm font-medium text-red-800 mb-1">Critical Gaps</p>
                  <ul className="space-y-1">
                    {output.critical_gaps.map((g, i) => (
                      <li key={i} className="text-sm text-red-700 flex gap-1">
                        <span>•</span>
                        <span>{g}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {output.domains.map((d, i) => (
                  <DomainCard key={i} domain={d} />
                ))}
              </div>
            </div>
          )
        })()}

        {review?.status === 'COMPLETE' && (
          <div className="mt-6">
            <DecisionPanel reviewId={review.id} vendorId={vendor.id} />
          </div>
        )}
      </Card>
    </div>
  )
}
