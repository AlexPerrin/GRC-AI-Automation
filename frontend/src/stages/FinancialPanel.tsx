import { useMutation, useQueryClient } from '@tanstack/react-query'
import { completeOnboarding, startFinancialReview } from '../api/client'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import type { Document, FinancialAnalysisResult, FinancialFinding, Review, Vendor } from '../types'
import ReviewPanel, { type EditColumn } from './ReviewPanel'

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
  LOW: 'border-green-200 bg-green-50',
  MEDIUM: 'border-yellow-200 bg-yellow-50',
  HIGH: 'border-orange-200 bg-orange-50',
  CRITICAL: 'border-red-200 bg-red-50',
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
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wide">Risk Score</span>
          <p className="text-2xl font-bold text-gray-900">{o.overall_risk_score}/10</p>
        </div>
        {o.recommendation && (
          <div className="flex-1">
            <span className="text-xs text-gray-500 uppercase tracking-wide">Recommendation</span>
            <p className="text-sm text-gray-800 mt-0.5">{o.recommendation}</p>
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

// ── Complete Onboarding card ───────────────────────────────────────────────────

function CompleteOnboardingCard({ vendor }: { vendor: Vendor }) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: () => completeOnboarding(vendor.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['vendor', String(vendor.id)] })
      void queryClient.invalidateQueries({ queryKey: ['audit-logs', String(vendor.id)] })
    },
  })

  if (vendor.status !== 'FINANCIAL_APPROVED') return null

  return (
    <Card>
      <h3 className="text-base font-semibold text-gray-900 mb-3">Complete Onboarding</h3>
      <p className="text-sm text-gray-600 mb-4">
        Financial review has been approved. Complete onboarding to finalise vendor status.
      </p>
      {mutation.isError && (
        <p className="text-sm text-red-600 mb-2">{(mutation.error as Error).message}</p>
      )}
      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
        {mutation.isPending ? 'Completing…' : 'Complete Onboarding'}
      </Button>
    </Card>
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
    <div className="space-y-6">
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
      <CompleteOnboardingCard vendor={vendor} />
    </div>
  )
}
