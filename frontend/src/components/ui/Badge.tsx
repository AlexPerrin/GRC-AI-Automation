import type { VendorStatus } from '../../types'

const statusColors: Record<VendorStatus, string> = {
  INTAKE: 'bg-gray-100 text-gray-700',
  USE_CASE_REVIEW: 'bg-yellow-100 text-yellow-800',
  USE_CASE_APPROVED: 'bg-green-100 text-green-800',
  LEGAL_REVIEW: 'bg-yellow-100 text-yellow-800',
  LEGAL_APPROVED: 'bg-green-100 text-green-800',
  NDA_PENDING: 'bg-blue-100 text-blue-800',
  SECURITY_REVIEW: 'bg-yellow-100 text-yellow-800',
  SECURITY_APPROVED: 'bg-green-100 text-green-800',
  FINANCIAL_REVIEW: 'bg-yellow-100 text-yellow-800',
  FINANCIAL_APPROVED: 'bg-green-100 text-green-800',
  ONBOARDED: 'bg-blue-600 text-white',
  REJECTED: 'bg-red-100 text-red-800',
}

const variantColors: Record<string, string> = {
  // Legal analyzer lowercase values
  compliant: 'bg-green-100 text-green-800',
  approve: 'bg-green-100 text-green-800',
  low: 'bg-green-100 text-green-800',
  partial: 'bg-yellow-100 text-yellow-800',
  approve_with_conditions: 'bg-yellow-100 text-yellow-800',
  medium: 'bg-yellow-100 text-yellow-800',
  non_compliant: 'bg-red-100 text-red-800',
  reject: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
  not_applicable: 'bg-gray-100 text-gray-500',
  // Uppercase variants
  MET: 'bg-green-100 text-green-800',
  APPROVE: 'bg-green-100 text-green-800',
  ONBOARDED: 'bg-blue-600 text-white',
  APPROVED: 'bg-green-100 text-green-800',
  ACCEPTABLE: 'bg-green-100 text-green-800',
  PROCEED: 'bg-green-100 text-green-800',
  STABLE: 'bg-green-100 text-green-800',
  LOW: 'bg-green-100 text-green-800',
  NOT_MET: 'bg-red-100 text-red-800',
  REJECT: 'bg-red-100 text-red-800',
  REJECTED: 'bg-red-100 text-red-800',
  UNACCEPTABLE: 'bg-red-100 text-red-800',
  DO_NOT_PROCEED: 'bg-red-100 text-red-800',
  HIGH_RISK: 'bg-red-100 text-red-800',
  CRITICAL: 'bg-red-100 text-red-800',
  HIGH: 'bg-orange-100 text-orange-800',
  PARTIAL: 'bg-yellow-100 text-yellow-800',
  CONCERN: 'bg-yellow-100 text-yellow-800',
  APPROVE_WITH_CONDITIONS: 'bg-yellow-100 text-yellow-800',
  ACCEPTABLE_WITH_CONDITIONS: 'bg-yellow-100 text-yellow-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800',
  IN_PROGRESS: 'bg-blue-100 text-blue-800',
  NDA_PENDING: 'bg-blue-100 text-blue-800',
  PENDING: 'bg-gray-100 text-gray-700',
  COMPLETE: 'bg-green-100 text-green-800',
  ERROR: 'bg-red-100 text-red-800',
}

interface BadgeProps {
  label: string
  className?: string
}

export default function Badge({ label, className = '' }: BadgeProps) {
  const color =
    (statusColors as Record<string, string>)[label] ??
    variantColors[label] ??
    'bg-gray-100 text-gray-700'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${color} ${className}`}
    >
      {label.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')}
    </span>
  )
}
