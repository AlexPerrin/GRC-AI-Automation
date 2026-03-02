import { useQueryClient } from '@tanstack/react-query'
import { startFinancialReview } from '../api/client'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import type { Document, FinancialAnalysisResult, FinancialFinding, Review, Vendor } from '../types'
import ReviewPanel, { AnalysisSummaryHeader, type EditColumn } from './ReviewPanel'

interface FinancialPanelProps {
  review: Review | undefined
  documents: Document[]
  vendor: Vendor
}

// ── Row type ──────────────────────────────────────────────────────────────────

type RiskLevel = FinancialFinding['risk_level']

interface FinancialRow {
  _id: number
  category: string
  value: string
  risk_level: RiskLevel
  notes: string
}

// ── Static config ─────────────────────────────────────────────────────────────

const RISK_LEVELS: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

function emptyRow(): Omit<FinancialRow, '_id'> {
  return { category: '', value: '', risk_level: 'LOW', notes: '' }
}

function seedRows(output: unknown): Omit<FinancialRow, '_id'>[] {
  return (output as FinancialAnalysisResult).findings.map(f => ({
    category: f.category,
    value: f.value,
    risk_level: f.risk_level,
    notes: f.notes,
  }))
}

const editColumns: EditColumn<FinancialRow>[] = [
  {
    header: 'Category',
    className: 'w-36',
    render: (row, onChange) => (
      <input
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.category}
        onChange={e => onChange('category', e.target.value)}
      />
    ),
  },
  {
    header: 'Value',
    className: 'w-32',
    render: (row, onChange) => (
      <input
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.value}
        onChange={e => onChange('value', e.target.value)}
      />
    ),
  },
  {
    header: 'Risk Level',
    className: 'w-32',
    render: (row, onChange) => (
      <select
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        value={row.risk_level}
        onChange={e => onChange('risk_level', e.target.value)}
      >
        {RISK_LEVELS.map(r => <option key={r} value={r}>{r}</option>)}
      </select>
    ),
  },
  {
    header: 'Notes',
    className: 'max-w-sm',
    render: (row, onChange) => (
      <textarea
        rows={2}
        className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
        value={row.notes}
        onChange={e => onChange('notes', e.target.value)}
      />
    ),
  },
]

const riskColors: Record<RiskLevel, string> = {
  LOW: 'bg-green-50',
  MEDIUM: 'bg-yellow-50',
  HIGH: 'bg-orange-50',
  CRITICAL: 'bg-red-50',
}

const riskRatingFromScore = (score: number): string => {
  if (score < 3) return 'low'
  if (score < 6) return 'medium'
  if (score < 8) return 'high'
  return 'critical'
}

function renderViewBody(rows: FinancialRow[]): React.ReactNode {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
            <th className="px-3 py-2">Category</th>
            <th className="px-3 py-2">Value</th>
            <th className="px-3 py-2">Risk Level</th>
            <th className="px-3 py-2">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map(row => (
            <tr key={row._id} className={riskColors[row.risk_level] ?? ''}>
              <td className="px-3 py-2 font-medium text-gray-900">{row.category}</td>
              <td className="px-3 py-2 text-gray-600">{row.value}</td>
              <td className="px-3 py-2"><Badge label={row.risk_level} /></td>
              <td className="px-3 py-2 text-gray-600 max-w-sm">{row.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function renderSummary(output: unknown): React.ReactNode {
  const o = output as FinancialAnalysisResult
  return (
    <AnalysisSummaryHeader
      riskScore={`${o.overall_risk_score?.toFixed(1) ?? '—'}/10`}
      riskRating={riskRatingFromScore(o.overall_risk_score ?? 5)}
      recommendation={o.recommendation}
      summary={o.summary}
      conditions={o.conditions}
    />
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function FinancialPanel({ review, documents, vendor }: FinancialPanelProps) {
  const queryClient = useQueryClient()

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['reviews', String(vendor.id)] })
    void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendor.id)] })
    void queryClient.invalidateQueries({ queryKey: ['audit-logs', String(vendor.id)] })
  }

  // Gate: not yet eligible
  if (
    ['INTAKE', 'USE_CASE_REVIEW', 'USE_CASE_APPROVED', 'LEGAL_REVIEW', 'LEGAL_APPROVED',
      'NDA_PENDING', 'SECURITY_REVIEW'].includes(vendor.status)
  ) {
    return (
      <Card>
        <p className="text-sm text-gray-500">
          Financial review becomes available after security approval.
        </p>
      </Card>
    )
  }

  // Gate: start review (idempotent — startFinancialReview returns existing if present)
  const startReview = async (vendorId: number) => {
    const r = await startFinancialReview(vendorId)
    invalidate()
    return r
  }

  return (
    <ReviewPanel<FinancialRow>
      review={review}
      documents={documents}
      vendorId={vendor.id}
      stage="FINANCIAL"
      docType="financial_statement"
      title="Financial Analysis"
      startReview={startReview}
      emptyRow={emptyRow}
      seedRows={seedRows}
      editColumns={editColumns}
      renderViewBody={renderViewBody}
      renderSummary={renderSummary}
    />
  )
}
