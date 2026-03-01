import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { listDocuments, listReviews, getVendor } from '../api/client'
import AuditTrail from '../components/AuditTrail'
import StatusStepper from '../components/StatusStepper'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import FinancialPanel from '../stages/FinancialPanel'
import LegalReviewPanel from '../stages/LegalReviewPanel'
import SecurityReviewPanel from '../stages/SecurityReviewPanel'
import UseCasePanel from '../stages/UseCasePanel'
import type { DocumentStage } from '../types'

type Tab = 'use_case' | 'legal' | 'security' | 'financial' | 'audit'

const TABS: { key: Tab; label: string }[] = [
  { key: 'use_case', label: 'Use Case' },
  { key: 'legal', label: 'Legal' },
  { key: 'security', label: 'Security' },
  { key: 'financial', label: 'Financial' },
  { key: 'audit', label: 'Audit Trail' },
]

export default function VendorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState<Tab>('use_case')

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

  // Re-fetch vendor when reviews change (status advances)
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
        <Button variant="ghost" disabled title="Coming soon">
          Export Report
        </Button>
      </div>

      <Card>
        <StatusStepper status={vendor.status} />
      </Card>

      <div>
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          {activeTab === 'use_case' && (
            <UseCasePanel review={reviewFor('USE_CASE')} vendorId={vendor.id} />
          )}
          {activeTab === 'legal' && (
            <LegalReviewPanel
              review={reviewFor('LEGAL')}
              documents={docsFor('LEGAL')}
              vendorId={vendor.id}
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
            <FinancialPanel review={reviewFor('FINANCIAL')} vendor={vendor} />
          )}
          {activeTab === 'audit' && <AuditTrail vendorId={vendor.id} />}
        </div>
      </div>
    </div>
  )
}
