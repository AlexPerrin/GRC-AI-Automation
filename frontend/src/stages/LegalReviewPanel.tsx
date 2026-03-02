import { useState } from 'react'
import { startLegalReview } from '../api/client'
import Badge from '../components/ui/Badge'
import type { Document, LegalAnalysisResult, LegalRegulationFinding, Review, Vendor } from '../types'
import ReviewPanel, { AnalysisSummaryHeader, type EditColumn } from './ReviewPanel'

interface LegalReviewPanelProps {
  review: Review | undefined
  documents: Document[]
  vendorId: number
  vendor: Vendor
}

// ── Row type ──────────────────────────────────────────────────────────────────

interface LegalRow {
  _id: number
  regulation: string
  article: string
  status: LegalRegulationFinding['status']
  finding: string
  evidence: string
}

// ── EvidenceCell (expand/collapse long text) ──────────────────────────────────

function EvidenceCell({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false)
  if (text.length <= 120) return <span>{text}</span>
  return (
    <span>
      {expanded ? text : `${text.slice(0, 120)}…`}
      <button
        onClick={() => setExpanded(e => !e)}
        className="ml-1 text-blue-500 hover:underline text-xs"
      >
        {expanded ? 'less' : 'more'}
      </button>
    </span>
  )
}

// ── Static config (module-level = stable references, no re-render churn) ─────

const STATUS_OPTIONS: LegalRegulationFinding['status'][] = [
  'compliant', 'partial', 'non_compliant', 'not_applicable',
]

function emptyRow(): Omit<LegalRow, '_id'> {
  return { regulation: '', article: '', status: 'compliant', finding: '', evidence: '' }
}

function seedRows(output: unknown): Omit<LegalRow, '_id'>[] {
  return (output as LegalAnalysisResult).regulation_findings.map(f => ({ ...f }))
}

const editColumns: EditColumn<LegalRow>[] = [
  {
    header: 'Regulation',
    render: (row, onChange) => (
      <input
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.regulation}
        onChange={e => onChange('regulation', e.target.value)}
      />
    ),
  },
  {
    header: 'Article',
    className: 'w-24',
    render: (row, onChange) => (
      <input
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.article}
        onChange={e => onChange('article', e.target.value)}
      />
    ),
  },
  {
    header: 'Status',
    className: 'w-40',
    render: (row, onChange) => (
      <select
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.status}
        onChange={e => onChange('status', e.target.value)}
      >
        {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
    ),
  },
  {
    header: 'Finding',
    className: 'max-w-xs',
    render: (row, onChange) => (
      <textarea
        rows={2}
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
        value={row.finding}
        onChange={e => onChange('finding', e.target.value)}
      />
    ),
  },
  {
    header: 'Evidence',
    className: 'max-w-xs',
    render: (row, onChange) => (
      <textarea
        rows={2}
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
        value={row.evidence}
        onChange={e => onChange('evidence', e.target.value)}
      />
    ),
  },
]

const statusRowColors: Record<LegalRegulationFinding['status'], string> = {
  compliant: 'bg-green-50',
  partial: 'bg-yellow-50',
  non_compliant: 'bg-red-50',
  not_applicable: '',
}

const riskToScore: Record<string, number> = { low: 2, medium: 5, high: 7.5, critical: 9.5 }

function renderViewBody(rows: LegalRow[]): React.ReactNode {
  return (
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
          {rows.map(row => (
            <tr key={row._id} className={statusRowColors[row.status] ?? ''}>
              <td className="px-3 py-2 font-medium text-gray-900">{row.regulation}</td>
              <td className="px-3 py-2 text-gray-600">{row.article}</td>
              <td className="px-3 py-2"><Badge label={row.status} /></td>
              <td className="px-3 py-2 text-gray-600 max-w-xs"><EvidenceCell text={row.finding} /></td>
              <td className="px-3 py-2 text-gray-500 max-w-xs"><EvidenceCell text={row.evidence} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function renderSummary(output: unknown): React.ReactNode {
  const o = output as LegalAnalysisResult
  const score = riskToScore[o.overall_risk] ?? 5
  return (
    <AnalysisSummaryHeader
      riskScore={`${score}/10`}
      riskRating={o.overall_risk}
      recommendation={o.recommendation}
      summary={o.summary}
      conditions={o.conditions}
    />
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function LegalReviewPanel({ review, documents, vendorId, vendor: _vendor }: LegalReviewPanelProps) {
  return (
    <ReviewPanel<LegalRow>
      review={review}
      documents={documents}
      vendorId={vendorId}
      stage="LEGAL"
      docType="privacy_policy"
      title="Legal Analysis"
      startReview={startLegalReview}
      emptyRow={emptyRow}
      seedRows={seedRows}
      editColumns={editColumns}
      renderViewBody={renderViewBody}
      renderSummary={renderSummary}
    />
  )
}
