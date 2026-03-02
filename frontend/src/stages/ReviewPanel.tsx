/**
 * Generic AI review panel.
 * Handles all shared structure and logic — Documents card, Analysis card header,
 * generate/regenerate button, edit/view toggle, seeding rows from AI output,
 * edit table, error notice, and DecisionPanel.
 *
 * Callers supply stage-specific config: column definitions, view renderer,
 * summary extractor, and API call.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { triggerReview } from '../api/client'
import DecisionPanel from '../components/DecisionPanel'
import DocumentUpload from '../components/DocumentUpload'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import type { Document, DocumentStage, Review } from '../types'

// ── Shared icons (exported so specific panels can reuse if needed) ────────────

export function SparkleIcon() {
  return (
    <svg className="h-3.5 w-3.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
      <path fillRule="evenodd" d="M9 4.5a.75.75 0 01.721.544l.813 2.846a3.75 3.75 0 002.576 2.576l2.846.813a.75.75 0 010 1.442l-2.846.813a3.75 3.75 0 00-2.576 2.576l-.813 2.846a.75.75 0 01-1.442 0l-.813-2.846a3.75 3.75 0 00-2.576-2.576l-2.846-.813a.75.75 0 010-1.442l2.846-.813A3.75 3.75 0 007.466 7.89l.813-2.846A.75.75 0 019 4.5zM18 1.5a.75.75 0 01.728.568l.258 1.036c.236.94.97 1.674 1.91 1.91l1.036.258a.75.75 0 010 1.456l-1.036.258c-.94.236-1.674.97-1.91 1.91l-.258 1.036a.75.75 0 01-1.456 0l-.258-1.036a3.375 3.375 0 00-2.455-2.456l-1.036-.258a.75.75 0 010-1.456l1.036-.258a3.375 3.375 0 002.455-2.456l.258-1.036A.75.75 0 0118 1.5zM16.5 15a.75.75 0 01.712.513l.394 1.183c.15.447.5.799.948.948l1.183.395a.75.75 0 010 1.422l-1.183.395c-.447.15-.799.5-.948.948l-.395 1.183a.75.75 0 01-1.422 0l-.395-1.183a1.5 1.5 0 00-.948-.948l-1.183-.395a.75.75 0 010-1.422l1.183-.395c.447-.15.799-.5.948-.948l.395-1.183A.75.75 0 0116.5 15z" clipRule="evenodd" />
    </svg>
  )
}

export function PencilIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 112.828 2.828L11.828 15.828a2 2 0 01-1.414.586H9v-2a2 2 0 01.586-1.414z" />
    </svg>
  )
}

export function CheckIcon({ className = 'h-4 w-4' }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  )
}

// ── Types ─────────────────────────────────────────────────────────────────────

/** Structured summary fields — always editable by the human reviewer. */
export interface SummaryFields {
  riskScore: string
  riskRating: string
  recommendation: string
  summary?: string
  conditions?: string[]
}

const EMPTY_SUMMARY: SummaryFields = { riskScore: '', riskRating: '', recommendation: '' }

/** A column definition for the edit-mode table. */
export interface EditColumn<TRow extends { _id: number }> {
  header: string
  /** Tailwind classes added to both <th> and <td> (e.g. "w-24 max-w-xs") */
  className?: string
  render(row: TRow, onChange: (field: string, value: string) => void): React.ReactNode
}

export interface ReviewPanelProps<TRow extends { _id: number }> {
  review: Review | undefined
  documents: Document[]
  vendorId: number

  /** Used for the DocumentUpload component and to derive the card title */
  stage: Extract<DocumentStage, 'LEGAL' | 'SECURITY' | 'FINANCIAL'>
  docType: string

  /** Title for the Analysis card (e.g. "Legal Analysis") */
  title: string

  /** Creates a new review record for this stage (idempotent — returns existing if present) */
  startReview(vendorId: number): Promise<{ id: number }>

  /** Returns a blank row (without _id) for the + Add Row action */
  emptyRow(): Omit<TRow, '_id'>

  /** Maps raw AI output to an array of rows (without _id) */
  seedRows(output: unknown): Omit<TRow, '_id'>[]

  /** Column definitions for the edit-mode table */
  editColumns: EditColumn<TRow>[]

  /** Renders the view-mode body (table, cards, etc.) given the current rows */
  renderViewBody(rows: TRow[]): React.ReactNode

  /**
   * Extracts structured summary fields from AI output.
   * When provided, a summary section is always shown above the findings table
   * with editable inputs pre-populated from AI output.
   */
  extractSummary?(output: unknown): SummaryFields
}

// ── Editable summary header ───────────────────────────────────────────────────

function EditableSummaryHeader({
  fields,
  onChange,
  isEditing,
}: {
  fields: SummaryFields
  onChange: (field: keyof Pick<SummaryFields, 'riskScore' | 'riskRating' | 'recommendation'>, value: string) => void
  isEditing: boolean
}) {
  const summaryBlock = (
    <>
      {fields.summary && (
        <p className="text-sm text-gray-700 bg-gray-50 rounded-md p-3">{fields.summary}</p>
      )}
      {fields.conditions && fields.conditions.length > 0 && (
        <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3">
          <p className="text-sm font-medium text-yellow-800 mb-1">Conditions</p>
          <ul className="space-y-1">
            {fields.conditions.map((c, i) => (
              <li key={i} className="text-sm text-yellow-700 flex gap-1">
                <span>•</span><span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-6 flex-wrap">
        {/* Risk Score */}
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wide">Risk Score</span>
          <div className="flex items-center gap-1 mt-0.5">
            {isEditing ? (
              <>
                <input
                  type="number"
                  min={0}
                  max={10}
                  step={0.1}
                  className="w-16 border border-gray-200 rounded px-2 py-0.5 text-xl font-bold text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  value={fields.riskScore}
                  onChange={e => onChange('riskScore', e.target.value.match(/^\d*\.?\d?/)?.[0] ?? '')}
                  placeholder="0.0"
                />
                <span className="text-xl font-bold text-gray-400">/10</span>
              </>
            ) : (
              <span className="text-xl font-bold text-gray-900">
                {fields.riskScore || '—'}<span className="text-xl font-bold text-gray-400">/10</span>
              </span>
            )}
          </div>
        </div>

        {/* Risk Rating */}
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wide">Risk Rating</span>
          <div className="mt-0.5">
            {isEditing ? (
              <select
                className="border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 bg-white"
                value={fields.riskRating}
                onChange={e => onChange('riskRating', e.target.value)}
              >
                <option value="">— select —</option>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="critical">critical</option>
              </select>
            ) : (
              fields.riskRating ? <Badge label={fields.riskRating} /> : <span className="text-sm text-gray-400">—</span>
            )}
          </div>
        </div>

        {/* Recommendation */}
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wide">Recommendation</span>
          <div className="mt-0.5">
            {isEditing ? (
              <select
                className="border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 bg-white"
                value={fields.recommendation}
                onChange={e => onChange('recommendation', e.target.value)}
              >
                <option value="">— select —</option>
                <option value="approve">approve</option>
                <option value="approve_with_conditions">approve_with_conditions</option>
                <option value="reject">reject</option>
              </select>
            ) : (
              fields.recommendation ? <Badge label={fields.recommendation} /> : <span className="text-sm text-gray-400">—</span>
            )}
          </div>
        </div>
      </div>
      {summaryBlock}
    </div>
  )
}

// ── Legacy read-only summary header (kept for reference / external use) ───────

export interface AnalysisSummaryHeaderProps {
  riskScore: string
  riskRating: string
  recommendation: string
  summary?: string
  conditions?: string[]
}

/** @deprecated Use extractSummary prop on ReviewPanel instead. */
export function AnalysisSummaryHeader(_props: AnalysisSummaryHeaderProps) {
  return null
}

// ── Stable uid counter shared across all ReviewPanel instances ────────────────
let _uid = 0
const uid = () => ++_uid

// ── Generic component ─────────────────────────────────────────────────────────

export default function ReviewPanel<TRow extends { _id: number }>({
  review,
  documents,
  vendorId,
  stage,
  docType,
  title,
  startReview,
  emptyRow,
  seedRows,
  editColumns,
  renderViewBody,
  extractSummary,
}: ReviewPanelProps<TRow>) {
  const queryClient = useQueryClient()
  const [rows, setRows] = useState<TRow[]>([])
  const [isEditing, setIsEditing] = useState(false)
  const [summaryFields, setSummaryFields] = useState<SummaryFields>(EMPTY_SUMMARY)

  // Refs — don't cause re-renders, safe to read inside effects/callbacks
  const seededIdRef = useRef<number | null>(null)  // which review.id has been seeded
  const loadedRef = useRef(false)                  // whether localStorage was attempted
  const userModifiedRef = useRef(false)            // whether user has changed rows/summary

  // Seed rows/summary: try localStorage first, fall back to AI output
  useEffect(() => {
    if (!review?.id) return
    if (seededIdRef.current === review.id) return

    // Try localStorage once per review.id
    if (!loadedRef.current) {
      loadedRef.current = true

      const savedRows = localStorage.getItem(`review-rows-${review.id}`)
      if (savedRows) {
        try {
          const parsed = JSON.parse(savedRows) as Array<Record<string, unknown>>
          if (Array.isArray(parsed) && parsed.length > 0) {
            setRows(parsed.map(r => ({ ...r, _id: uid() } as unknown as TRow)))
            seededIdRef.current = review.id
          }
        } catch { /* ignore malformed */ }
      }

      if (extractSummary) {
        const savedSummary = localStorage.getItem(`review-summary-${review.id}`)
        if (savedSummary) {
          try { setSummaryFields(JSON.parse(savedSummary) as SummaryFields) } catch { /* ignore */ }
        }
      }

      // If we loaded rows from localStorage, skip AI seeding
      if (seededIdRef.current === review.id) return
    }

    // Seed from AI output if the review is complete
    if (review.status === 'COMPLETE' && review.ai_output) {
      setRows(seedRows(review.ai_output).map(r => ({ ...r, _id: uid() } as TRow)))
      if (extractSummary) setSummaryFields(extractSummary(review.ai_output))
      seededIdRef.current = review.id
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [review?.id, review?.status, review?.ai_output])

  // Persist rows to localStorage whenever they change.
  // Guard: skip the transient empty-rows state on mount before seeding completes,
  // so we never overwrite non-empty saved data with [].
  useEffect(() => {
    if (!review?.id) return
    if (rows.length === 0 && !userModifiedRef.current) return
    localStorage.setItem(`review-rows-${review.id}`, JSON.stringify(rows))
  }, [rows, review?.id])

  // Persist summary to localStorage whenever it changes.
  // Same guard: only write when the user has actually changed something or there
  // is real content — don't overwrite saved values with the blank initial state.
  useEffect(() => {
    if (!review?.id || !extractSummary) return
    const hasContent = summaryFields.riskScore || summaryFields.riskRating || summaryFields.recommendation
    if (!hasContent && !userModifiedRef.current) return
    localStorage.setItem(`review-summary-${review.id}`, JSON.stringify(summaryFields))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summaryFields, review?.id])

  // Idempotent: re-uses existing review for PENDING / ERROR / COMPLETE,
  // creates a new one only when none exists yet.
  const analyzeMutation = useMutation({
    mutationFn: async (docId: number) => {
      if (review && ['PENDING', 'ERROR', 'COMPLETE'].includes(review.status)) {
        return triggerReview(review.id, docId)
      }
      const created = await startReview(vendorId)
      return triggerReview(created.id, docId)
    },
    onSuccess: () => {
      // Reset so new AI output is picked up after regeneration
      userModifiedRef.current = false
      seededIdRef.current = null
      loadedRef.current = false
      setRows([])
      setSummaryFields(EMPTY_SUMMARY)
      if (review?.id) {
        localStorage.removeItem(`review-rows-${review.id}`)
        localStorage.removeItem(`review-summary-${review.id}`)
      }
      void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendorId)] })
    },
  })

  function updateRow(id: number, field: string, value: string) {
    userModifiedRef.current = true
    setRows(prev => prev.map(r => r._id === id ? { ...r, [field]: value } : r))
  }

  function deleteRow(id: number) {
    userModifiedRef.current = true
    setRows(prev => prev.filter(r => r._id !== id))
  }

  function addRow() {
    userModifiedRef.current = true
    setRows(prev => [...prev, { ...emptyRow(), _id: uid() } as TRow])
  }

  function handleTrigger() {
    const doc = documents[0]
    if (doc) analyzeMutation.mutate(doc.id)
  }

  const isComplete = review?.status === 'COMPLETE'
  const isRunning = analyzeMutation.isPending || review?.status === 'IN_PROGRESS'
  const generateDisabled = documents.length === 0 || isRunning
  const stageLabel = stage === 'LEGAL' ? 'Legal' : stage === 'SECURITY' ? 'Security' : 'Financial'

  return (
    <div className="space-y-6">
      {/* Card 1: Documents */}
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">{stageLabel} Documents</h3>
        <DocumentUpload
          vendorId={vendorId}
          stage={stage}
          docType={docType}
          documents={documents}
        />
      </Card>

      {/* Card 2: Analysis */}
      <Card>
        {/* Header row */}
        <div className="flex items-center justify-between mb-4">
          {/* Left: title + generate button + complete badge */}
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className="text-base font-semibold text-gray-900">{title}</h3>

            <button
              onClick={handleTrigger}
              disabled={generateDisabled}
              title={documents.length === 0 ? 'Upload a document first' : undefined}
              className="flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1 text-xs font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isRunning ? <Spinner /> : <SparkleIcon />}
              {isComplete ? 'Regenerate Analysis' : 'Generate Analysis'}
            </button>

            {isComplete && !analyzeMutation.isPending && (
              <span className="flex items-center gap-1.5 rounded-full bg-green-50 border border-green-200 px-2.5 py-1 text-xs font-medium text-green-700">
                <CheckIcon className="h-3.5 w-3.5 flex-shrink-0" />
                Analysis Complete
              </span>
            )}
          </div>

          {/* Right: edit toggle */}
          <button
            onClick={() => setIsEditing(e => !e)}
            title={isEditing ? 'Done editing' : 'Edit findings'}
            aria-label={isEditing ? 'Done editing' : 'Edit findings'}
            className={`flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium transition-colors ${
              isEditing
                ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
            }`}
          >
            {isEditing ? <><CheckIcon /> Done</> : <><PencilIcon /> Edit</>}
          </button>
        </div>

        {/* Error notice */}
        {review?.status === 'ERROR' && !analyzeMutation.isPending && (
          <div className="mb-4 rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-sm text-red-700">Analysis failed. Use the Generate button above to retry.</p>
          </div>
        )}

        {/* Summary — always visible when extractSummary is provided */}
        {extractSummary && (
          <div className="mb-6">
            <EditableSummaryHeader
              fields={summaryFields}
              onChange={(field, value) => {
                userModifiedRef.current = true
                setSummaryFields(prev => ({ ...prev, [field]: value }))
              }}
              isEditing={isEditing}
            />
          </div>
        )}

        {/* Findings — editable table or view-mode body */}
        {isEditing ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    {editColumns.map((col, i) => (
                      <th key={i} className={`px-3 py-2 ${col.className ?? ''}`}>{col.header}</th>
                    ))}
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rows.map(row => (
                    <tr key={row._id}>
                      {editColumns.map((col, i) => (
                        <td key={i} className={`px-3 py-2 ${col.className ?? ''}`}>
                          {col.render(row, (field, value) => updateRow(row._id, field, value))}
                        </td>
                      ))}
                      <td className="px-3 py-2">
                        <button
                          onClick={() => deleteRow(row._id)}
                          className="text-gray-400 hover:text-red-500 transition-colors text-lg leading-none"
                          title="Delete row"
                          aria-label="Delete row"
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              onClick={addRow}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800 border border-dashed border-blue-300 hover:border-blue-500 rounded px-3 py-1.5 transition-colors"
            >
              + Add Row
            </button>
          </>
        ) : (
          rows.length > 0
            ? renderViewBody(rows)
            : (
              <p className="text-sm text-gray-400 italic py-4 text-center">
                No findings yet. Run AI Analysis above or click Edit to add rows manually.
              </p>
            )
        )}

        {/* Decision panel — always present (review created at intake) */}
        {review?.id && (
          <div className="mt-6">
            <DecisionPanel reviewId={review.id} vendorId={vendorId} />
          </div>
        )}
      </Card>
    </div>
  )
}
