import { useState } from 'react'
import { startSecurityReview } from '../api/client'
import Badge from '../components/ui/Badge'
import type { ControlFinding, Document, Review, SecurityAnalysisResult, Vendor } from '../types'
import ReviewPanel, { type EditColumn, type SummaryFields } from './ReviewPanel'

interface SecurityReviewPanelProps {
  review: Review | undefined
  documents: Document[]
  vendor: Vendor
}

// ── Row type ──────────────────────────────────────────────────────────────────

type ControlStatus = ControlFinding['status']

interface SecurityFindingRow {
  _id: number
  domain: string
  framework: string
  control_id: string
  status: ControlStatus
  finding: string
  evidence: string
  risk_score: string
}

// ── EvidenceCell (expand/collapse) ────────────────────────────────────────────

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

// ── Static config ─────────────────────────────────────────────────────────────

const STATUS_OPTIONS: ControlStatus[] = ['met', 'partial', 'not_met', 'not_applicable']

function emptyRow(): Omit<SecurityFindingRow, '_id'> {
  return { domain: '', framework: '', control_id: '', status: 'partial', finding: '', evidence: '', risk_score: '3' }
}

function seedRows(output: unknown): Omit<SecurityFindingRow, '_id'>[] {
  return ((output as SecurityAnalysisResult).control_findings ?? []).map(f => ({
    domain: f.domain ?? '',
    framework: f.framework ?? '',
    control_id: f.control_id ?? '',
    status: f.status ?? 'partial',
    finding: f.finding ?? '',
    evidence: f.evidence ?? '',
    risk_score: String(Math.round((f.risk_score ?? 3) * 2)),
  }))
}

const statusRowColors: Record<ControlStatus, string> = {
  met: 'bg-green-50',
  partial: 'bg-yellow-50',
  not_met: 'bg-red-50',
  not_applicable: '',
}

const editColumns: EditColumn<SecurityFindingRow>[] = [
  {
    header: 'Framework',
    className: 'w-28',
    render: (row, onChange) => (
      <input
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.framework}
        onChange={e => onChange('framework', e.target.value)}
      />
    ),
  },
  {
    header: 'Domain',
    render: (row, onChange) => (
      <input
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.domain}
        onChange={e => onChange('domain', e.target.value)}
      />
    ),
  },
  {
    header: 'Control',
    className: 'w-24',
    render: (row, onChange) => (
      <input
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.control_id}
        onChange={e => onChange('control_id', e.target.value)}
      />
    ),
  },
  {
    header: 'Status',
    className: 'w-36',
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
  {
    header: 'Score',
    className: 'w-20',
    render: (row, onChange) => (
      <input
        type="number"
        min={1}
        max={10}
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.risk_score}
        onChange={e => onChange('risk_score', e.target.value)}
      />
    ),
  },
]

function extractSummary(output: unknown): SummaryFields {
  const o = output as SecurityAnalysisResult
  const score = o.risk_score != null ? (o.risk_score * 2) : 0
  return {
    riskScore: score.toFixed(1),
    riskRating: o.overall_risk ?? '',
    recommendation: o.recommendation ?? '',
    summary: o.summary,
    conditions: o.conditions,
  }
}

function renderViewBody(rows: SecurityFindingRow[]): React.ReactNode {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
            <th className="px-3 py-2">Framework</th>
            <th className="px-3 py-2">Domain</th>
            <th className="px-3 py-2">Control</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Finding</th>
            <th className="px-3 py-2">Evidence</th>
            <th className="px-3 py-2">Score</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map(row => (
            <tr key={row._id} className={statusRowColors[row.status] ?? ''}>
              <td className="px-3 py-2 text-gray-600">{row.framework}</td>
              <td className="px-3 py-2 font-medium text-gray-900">{row.domain}</td>
              <td className="px-3 py-2 text-gray-600">{row.control_id}</td>
              <td className="px-3 py-2"><Badge label={row.status} /></td>
              <td className="px-3 py-2 text-gray-600 max-w-xs"><EvidenceCell text={row.finding} /></td>
              <td className="px-3 py-2 text-gray-500 max-w-xs"><EvidenceCell text={row.evidence} /></td>
              <td className="px-3 py-2 text-center text-gray-700 font-medium">{row.risk_score}/10</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function SecurityReviewPanel({ review, documents, vendor }: SecurityReviewPanelProps) {
  return (
    <ReviewPanel<SecurityFindingRow>
      review={review}
      documents={documents}
      vendorId={vendor.id}
      stage="SECURITY"
      docType="soc2"
      title="Security Analysis"
      startReview={startSecurityReview}
      emptyRow={emptyRow}
      seedRows={seedRows}
      editColumns={editColumns}
      renderViewBody={renderViewBody}
      extractSummary={extractSummary}
    />
  )
}
