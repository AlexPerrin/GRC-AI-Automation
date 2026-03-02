import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { completeOnboarding, confirmNda, getVendor, listDocuments, listReviews, listVendorDecisions, rejectVendor } from '../api/client'
import AuditTrail from '../components/AuditTrail'
import StatusStepper, { type StageTab } from '../components/StatusStepper'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import FinancialPanel from '../stages/FinancialPanel'
import LegalReviewPanel from '../stages/LegalReviewPanel'
import SecurityReviewPanel from '../stages/SecurityReviewPanel'
import UseCasePanel from '../stages/UseCasePanel'
import type { Decision, DocumentStage, Review, Vendor } from '../types'

// ── NDA Panel ─────────────────────────────────────────────────────────────────

function NdaPanel({ vendor, onConfirmed }: { vendor: Vendor; onConfirmed: () => void }) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: () => confirmNda(vendor.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendor.id)] })
      void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendor.id)] })
      onConfirmed()
    },
  })

  if (['INTAKE', 'USE_CASE_REVIEW'].includes(vendor.status)) {
    return (
      <Card>
        <p className="text-sm text-gray-500">NDA confirmation will be available after use case approval.</p>
      </Card>
    )
  }

  if (vendor.status !== 'USE_CASE_APPROVED') {
    return (
      <Card>
        <div className="flex items-center gap-2 text-green-700">
          <svg className="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-sm font-medium">NDA Confirmed</span>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-base font-semibold text-gray-900 mb-2">NDA Confirmation</h3>
      <p className="text-sm text-gray-600 mb-4">
        NDA execution must be confirmed before the legal review can begin.
      </p>
      {mutation.isError && (
        <p className="text-sm text-red-600 mb-2">{(mutation.error as Error).message}</p>
      )}
      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
        {mutation.isPending ? 'Confirming…' : 'Confirm NDA Executed'}
      </Button>
    </Card>
  )
}

// ── Onboarding Decision Panel ──────────────────────────────────────────────────

interface ReviewMeta {
  label: string
  stage: DocumentStage
}

const REVIEW_STAGES: ReviewMeta[] = [
  { label: 'Use Case',  stage: 'USE_CASE'  },
  { label: 'Legal',     stage: 'LEGAL'     },
  { label: 'Security',  stage: 'SECURITY'  },
  { label: 'Financial', stage: 'FINANCIAL' },
]

const riskRatingFromScore = (score: number): string => {
  if (score < 3) return 'low'
  if (score < 6) return 'medium'
  if (score < 8) return 'high'
  return 'critical'
}

const riskToScore: Record<string, string> = { low: '2/10', medium: '5/10', high: '7.5/10', critical: '9.5/10' }

function reviewSummary(review: Review | undefined) {
  if (!review || review.status !== 'COMPLETE') return null
  if (review.ai_output) {
    const o = review.ai_output as unknown as Record<string, unknown>
    const overallRisk = o.overall_risk ? String(o.overall_risk) : null
    const overallScore = o.overall_risk_score != null ? (o.overall_risk_score as number) : null
    return {
      riskScore: overallRisk
        ? (riskToScore[overallRisk] ?? null)
        : overallScore != null
          ? `${overallScore.toFixed(1)}/10`
          : null,
      riskRating: overallRisk ?? (overallScore != null ? riskRatingFromScore(overallScore) : null),
    }
  }
  return null
}

const decisionLabel: Record<string, string> = {
  APPROVE: 'Approved',
  APPROVE_WITH_CONDITIONS: 'Approved with Conditions',
  REJECT: 'Rejected',
}

const statusLabel: Record<string, string> = {
  PENDING: 'Pending',
  IN_PROGRESS: 'In Progress',
  COMPLETE: 'Complete',
  ERROR: 'Error',
}

function OnboardingDecisionPanel({
  vendor,
  reviews,
}: {
  vendor: Vendor
  reviews: Review[] | undefined
}) {
  const queryClient = useQueryClient()
  const [rationale, setRationale] = useState('')
  const [showReject, setShowReject] = useState(false)

  const { data: decisions } = useQuery({
    queryKey: ['vendor-decisions', String(vendor.id)],
    queryFn: () => listVendorDecisions(vendor.id),
  })

  const invalidateAll = () => {
    void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendor.id)] })
    void queryClient.invalidateQueries({ queryKey: ['audit-logs', String(vendor.id)] })
    void queryClient.invalidateQueries({ queryKey: ['vendor-decisions', String(vendor.id)] })
  }

  const approveMutation = useMutation({
    mutationFn: () => completeOnboarding(vendor.id),
    onSuccess: invalidateAll,
  })

  const rejectMutation = useMutation({
    mutationFn: () => rejectVendor(vendor.id, rationale),
    onSuccess: invalidateAll,
  })

  const isOnboarded = vendor.status === 'ONBOARDED'
  const isRejected  = vendor.status === 'REJECTED'
  const canDecide   = vendor.status === 'FINANCIAL_APPROVED'

  return (
    <div className="space-y-4">
      {/* Status banner */}
      {isOnboarded && (
        <div className="flex items-center gap-2 rounded-md bg-green-50 border border-green-200 px-4 py-3 text-green-800 font-medium">
          <svg className="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Vendor Onboarded
        </div>
      )}
      {isRejected && (
        <div className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-red-800 font-medium">
          <svg className="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Vendor Rejected
        </div>
      )}

      {/* Review summaries */}
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-3">Review Summaries</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {REVIEW_STAGES.map(({ label, stage }) => {
            const review   = reviews?.find(r => r.stage === stage)
            const decision = decisions?.find((d: Decision) => d.review_id === review?.id)
            const meta     = reviewSummary(review)
            const ucForm   = stage === 'USE_CASE' && review?.form_input
              ? review.form_input as Record<string, unknown>
              : null

            const statusText  = decision ? (decisionLabel[decision.action] ?? decision.action) : (review ? statusLabel[review.status] ?? review.status : 'Not started')
            const statusColor = decision?.action === 'APPROVE'
              ? 'bg-green-100 text-green-700'
              : decision?.action === 'APPROVE_WITH_CONDITIONS'
                ? 'bg-yellow-100 text-yellow-700'
                : decision?.action === 'REJECT'
                  ? 'bg-red-100 text-red-700'
                  : review?.status === 'COMPLETE'
                    ? 'bg-gray-200 text-gray-500'
                    : review?.status === 'ERROR'
                      ? 'bg-red-100 text-red-700'
                      : review?.status === 'IN_PROGRESS'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-200 text-gray-500'

            return (
              <div key={stage} className="rounded-md border border-gray-100 bg-gray-50 px-4 py-3 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-gray-800">{label}</span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${statusColor}`}>
                    {statusText}
                  </span>
                </div>
                {(meta?.riskScore || meta?.riskRating) && (
                  <div className="flex items-center gap-3 flex-wrap mt-1">
                    {meta?.riskScore && (
                      <span className="text-xs text-gray-500">
                        Risk Score: <span className="font-bold text-gray-900">{meta.riskScore}</span>
                      </span>
                    )}
                    {meta?.riskRating && (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        Risk Rating: <Badge label={meta.riskRating} />
                      </span>
                    )}
                  </div>
                )}
                {ucForm && (
                  <div className="mt-2 space-y-1">
                    {!!ucForm.reviewer_name && (
                      <p className="text-xs text-gray-500">
                        Approver: <span className="font-bold text-gray-900">{String(ucForm.reviewer_name)}</span>
                      </p>
                    )}
                    {Array.isArray(ucForm.data_types_involved) && ucForm.data_types_involved.length > 0 && (
                      <div>
                        <p className="text-xs text-gray-500">Data Types:</p>
                        <ul className="mt-0.5 space-y-0.5 list-disc list-inside">
                          {(ucForm.data_types_involved as string[]).map((t, i) => (
                            <li key={i} className="text-xs font-bold text-gray-900">{t}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {!!ucForm.notes && (
                      <p className="text-xs text-gray-500">
                        Notes: <span className="font-bold text-gray-900">{String(ucForm.notes)}</span>
                      </p>
                    )}
                  </div>
                )}
                {decision && (
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-gray-500">
                      Approver: <span className="font-bold text-gray-900">{decision.actor}</span>
                    </p>
                    {decision.rationale && (
                      <p className="text-xs text-gray-500">
                        Rationale: <span className="font-bold text-gray-900">{decision.rationale}</span>
                      </p>
                    )}
                    {decision.conditions && decision.conditions.length > 0 && (
                      <div>
                        <p className="text-xs text-gray-500">Conditions:</p>
                        <ul className="mt-0.5 space-y-0.5 list-disc list-inside">
                          {decision.conditions.map((c, i) => (
                            <li key={i} className="text-xs font-bold text-gray-900">{c}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      {/* Decision card */}
      {canDecide && (
        <Card>
          <h3 className="text-base font-semibold text-gray-900 mb-2">Final Decision</h3>
          <p className="text-sm text-gray-600 mb-4">
            All reviews are approved. Approve the vendor to complete onboarding or reject to end the process.
          </p>
          {approveMutation.isError && (
            <p className="text-sm text-red-600 mb-2">{(approveMutation.error as Error).message}</p>
          )}
          {!showReject ? (
            <div className="flex items-center gap-3">
              <Button
                onClick={() => approveMutation.mutate()}
                disabled={approveMutation.isPending}
              >
                {approveMutation.isPending ? 'Approving…' : 'Approve'}
              </Button>
              <button
                type="button"
                onClick={() => setShowReject(true)}
                className="px-4 py-2 rounded-md border border-red-300 text-red-700 text-sm font-medium hover:bg-red-50 transition-colors"
              >
                Reject
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <textarea
                rows={3}
                placeholder="Reason for rejection…"
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-red-400 resize-none"
                value={rationale}
                onChange={e => setRationale(e.target.value)}
              />
              {rejectMutation.isError && (
                <p className="text-sm text-red-600">{(rejectMutation.error as Error).message}</p>
              )}
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => rejectMutation.mutate()}
                  disabled={rejectMutation.isPending || !rationale.trim()}
                  className="px-4 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {rejectMutation.isPending ? 'Rejecting…' : 'Confirm Reject'}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowReject(false); setRationale('') }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </Card>
      )}

      {!canDecide && !isOnboarded && !isRejected && (
        <Card>
          <p className="text-sm text-gray-500">
            Onboarding decision will be available after all reviews are approved.
          </p>
        </Card>
      )}
    </div>
  )
}

export default function VendorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState<StageTab>('use_case')
  const [menuOpen, setMenuOpen] = useState(false)
  const [showLogs, setShowLogs] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const anyInProgress = (reviews: { status: string }[] | undefined) =>
    reviews?.some((r) => r.status === 'IN_PROGRESS') ?? false

  const { data: vendor, isLoading: vendorLoading } = useQuery({
    queryKey: ['vendor', id],
    queryFn: () => getVendor(id!),
    refetchInterval: (query) => (anyInProgress(query.state.data ? undefined : undefined) ? 3000 : false),
  })

  const { data: reviews } = useQuery({
    queryKey: ['reviews', id],
    queryFn: () => listReviews(id!),
    refetchInterval: (query) => (anyInProgress(query.state.data ?? undefined) ? 3000 : false),
    enabled: !!vendor,
  })

  const { data: documents } = useQuery({
    queryKey: ['documents', id],
    queryFn: () => listDocuments(id!),
    enabled: !!vendor,
  })

  useQuery({
    queryKey: ['vendor', id],
    queryFn: () => getVendor(id!),
    refetchInterval: anyInProgress(reviews) ? 3000 : false,
  })

  if (vendorLoading) return <p className="text-gray-500">Loading…</p>
  if (!vendor) return <p className="text-red-600">Vendor not found.</p>

  const reviewFor = (stage: DocumentStage) => reviews?.find((r) => r.stage === stage)
  const docsFor = (stage: DocumentStage) => documents?.filter((d) => d.stage === stage) ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link to="/" className="text-sm text-blue-600 hover:underline">
            ← All vendors
          </Link>
          <h1 className="mt-1 text-2xl font-semibold text-gray-900">{vendor.name}</h1>
          {vendor.website && (
            <a
              href={vendor.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-500 hover:underline"
            >
              {vendor.website}
            </a>
          )}
        </div>

        {/* Hamburger menu */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen(o => !o)}
            aria-label="Open menu"
            className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-1 w-44 rounded-md shadow-lg bg-white ring-1 ring-black/5 z-10 py-1">
              <button
                className="w-full text-left px-4 py-2 text-sm text-gray-400 cursor-not-allowed"
                disabled
                title="Coming soon"
              >
                Settings
              </button>
              <button
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                onClick={() => { setShowLogs(true); setMenuOpen(false) }}
              >
                Logs
              </button>
              <button
                className="w-full text-left px-4 py-2 text-sm text-gray-400 cursor-not-allowed"
                disabled
                title="Coming soon"
              >
                Export Report
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Stepper — doubles as navigation */}
      <Card>
        <StatusStepper
          status={vendor.status}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      </Card>

      {/* Stage content */}
      <div>
        {activeTab === 'use_case' && (
          <UseCasePanel review={reviewFor('USE_CASE')} vendorId={vendor.id} />
        )}
        {activeTab === 'nda' && (
          <NdaPanel vendor={vendor} onConfirmed={() => setActiveTab('legal')} />
        )}
        {activeTab === 'legal' && (
          <LegalReviewPanel
            review={reviewFor('LEGAL')}
            documents={docsFor('LEGAL')}
            vendorId={vendor.id}
            vendor={vendor}
          />
        )}
        {activeTab === 'security' && (
          <SecurityReviewPanel
            review={reviewFor('SECURITY')}
            documents={docsFor('SECURITY')}
            vendor={vendor}
          />
        )}
        {activeTab === 'financial' && (
          <FinancialPanel
            review={reviewFor('FINANCIAL')}
            documents={docsFor('FINANCIAL')}
            vendor={vendor}
          />
        )}
        {activeTab === 'onboarding' && (
          <OnboardingDecisionPanel vendor={vendor} reviews={reviews} />
        )}
      </div>

      {/* Logs modal */}
      {showLogs && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-end bg-black/30 backdrop-blur-sm"
          onClick={() => setShowLogs(false)}
        >
          <div
            className="relative m-4 mt-16 w-full max-w-lg bg-white rounded-lg shadow-xl flex flex-col max-h-[80vh]"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h3 className="text-base font-semibold text-gray-900">Logs</h3>
              <button
                onClick={() => setShowLogs(false)}
                className="text-gray-400 hover:text-gray-600 text-xl leading-none"
                aria-label="Close logs"
              >
                ×
              </button>
            </div>
            <div className="overflow-y-auto p-5">
              <AuditTrail vendorId={vendor.id} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
