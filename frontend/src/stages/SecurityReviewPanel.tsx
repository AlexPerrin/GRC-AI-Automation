import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { confirmNda, startSecurityReview } from '../api/client'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import type { ControlFinding, Document, Review, SecurityAnalysisResult, Vendor } from '../types'
import ReviewPanel, { type EditColumn } from './ReviewPanel'

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
    risk_score: String(f.risk_score ?? 3),
  }))
}

const editColumns: EditColumn<SecurityFindingRow>[] = [
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
    className: 'w-16',
    render: (row, onChange) => (
      <input
        type="number"
        min={1}
        max={5}
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.risk_score}
        onChange={e => onChange('risk_score', e.target.value)}
      />
    ),
  },
]

function renderViewBody(rows: SecurityFindingRow[]): React.ReactNode {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
            <th className="px-3 py-2">Domain</th>
            <th className="px-3 py-2">Framework</th>
            <th className="px-3 py-2">Control</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Finding</th>
            <th className="px-3 py-2">Evidence</th>
            <th className="px-3 py-2">Score</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map(row => (
            <tr key={row._id}>
              <td className="px-3 py-2 font-medium text-gray-900">{row.domain}</td>
              <td className="px-3 py-2 text-gray-600">{row.framework}</td>
              <td className="px-3 py-2 text-gray-600">{row.control_id}</td>
              <td className="px-3 py-2"><Badge label={row.status} /></td>
              <td className="px-3 py-2 text-gray-600 max-w-xs"><EvidenceCell text={row.finding} /></td>
              <td className="px-3 py-2 text-gray-500 max-w-xs"><EvidenceCell text={row.evidence} /></td>
              <td className="px-3 py-2 text-center text-gray-700 font-medium">{row.risk_score}/5</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function renderSummary(output: unknown): React.ReactNode {
  const o = output as SecurityAnalysisResult
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 flex-wrap">
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wide">Overall Risk</span>
          <div className="mt-0.5"><Badge label={o.overall_risk} /></div>
        </div>
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wide">Recommendation</span>
          <div className="mt-0.5"><Badge label={o.recommendation} /></div>
        </div>
        {o.risk_score != null && (
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wide">Mean Control Score</span>
            <p className="text-sm font-semibold text-gray-900 mt-0.5">{o.risk_score}/5</p>
          </div>
        )}
      </div>
      {o.summary && (
        <p className="text-sm text-gray-700 bg-gray-50 rounded-md p-3">{o.summary}</p>
      )}
      {o.conditions && o.conditions.length > 0 && (
        <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3">
          <p className="text-sm font-medium text-yellow-800 mb-1">Conditions</p>
          <ul className="space-y-1">
            {o.conditions.map((c, i) => (
              <li key={i} className="text-sm text-yellow-700 flex gap-1">
                <span>•</span><span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function SecurityReviewPanel({ review, documents, vendor }: SecurityReviewPanelProps) {
  const queryClient = useQueryClient()

  const ndaMutation = useMutation({
    mutationFn: () => confirmNda(vendor.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendor.id)] })
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
  if (['INTAKE', 'USE_CASE_REVIEW', 'USE_CASE_APPROVED', 'LEGAL_REVIEW'].includes(vendor.status)) {
    return (
      <Card>
        <p className="text-sm text-gray-500">Security review will be available after legal approval and NDA confirmation.</p>
      </Card>
    )
  }

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
      renderSummary={renderSummary}
    />
  )
}
