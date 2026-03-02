import type { VendorStatus } from '../types'

export type StageTab = 'use_case' | 'nda' | 'legal' | 'security' | 'financial' | 'onboarding'

const STEPS: { label: string; tab: StageTab | null }[] = [
  { label: 'Use Case',            tab: 'use_case' },
  { label: 'NDA',                 tab: 'nda' },
  { label: 'Legal Review',        tab: 'legal' },
  { label: 'Security Review',     tab: 'security' },
  { label: 'Financial Review',    tab: 'financial' },
  { label: 'Onboarding Decision', tab: 'onboarding' },
]

// Which step circle gets the "active tab" ring
const TAB_PRIMARY_STEP: Record<StageTab, number> = {
  use_case: 0,
  nda: 1,
  legal: 2,
  security: 3,
  financial: 4,
  onboarding: 5,
}

function statusToStep(status: VendorStatus): number {
  switch (status) {
    case 'INTAKE':
    case 'USE_CASE_REVIEW':
      return 0
    case 'USE_CASE_APPROVED':
      return 1
    case 'NDA_PENDING':
    case 'LEGAL_REVIEW':
      return 2
    case 'LEGAL_APPROVED':
      return 3
    case 'SECURITY_REVIEW':
      return 3
    case 'SECURITY_APPROVED':
      return 4
    case 'FINANCIAL_REVIEW':
      return 4
    case 'FINANCIAL_APPROVED':
      return 5
    case 'ONBOARDED':
      return 6  // all 6 steps complete
    case 'REJECTED':
      return 5  // steps 0-4 complete, step 5 shows red X
    default:
      return 0
  }
}

interface StatusStepperProps {
  status: VendorStatus
  activeTab: StageTab
  onTabChange: (tab: StageTab) => void
}

export default function StatusStepper({ status, activeTab, onTabChange }: StatusStepperProps) {
  const isRejected  = status === 'REJECTED'
  const isOnboarded = status === 'ONBOARDED'
  const progressStep = statusToStep(status)
  const ringStep = TAB_PRIMARY_STEP[activeTab]

  return (
    <nav aria-label="Progress">
      <ol className="flex items-center">
        {STEPS.map((step, idx) => {
          const completed           = idx < progressStep
          const current             = idx === progressStep
          const isLast              = idx === STEPS.length - 1
          const hasRing             = idx === ringStep
          const clickable           = step.tab !== null
          const isOnboardingCircle  = idx === STEPS.length - 1
          const showGreen           = isOnboardingCircle && isOnboarded
          const showRed             = isOnboardingCircle && isRejected

          const circleClass = showGreen
            ? 'bg-green-600 text-white'
            : showRed
              ? 'bg-red-600 text-white'
              : completed
                ? 'bg-blue-600 text-white'
                : current
                  ? 'border-2 border-blue-600 bg-white text-blue-600'
                  : 'border-2 border-gray-300 bg-white text-gray-400'

          const labelClass = isOnboardingCircle && isOnboarded
            ? 'text-green-700 font-semibold'
            : isOnboardingCircle && isRejected
              ? 'text-red-700 font-semibold'
              : hasRing
                ? 'text-blue-600 font-semibold'
                : current
                  ? 'text-blue-600'
                  : completed
                    ? 'text-gray-700'
                    : 'text-gray-400'

          return (
            <li key={step.label} className={`flex items-center ${isLast ? '' : 'flex-1'}`}>
              <div className="flex flex-col items-center">
                <button
                  type="button"
                  onClick={() => step.tab && onTabChange(step.tab)}
                  disabled={!clickable}
                  className={[
                    'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors',
                    circleClass,
                    hasRing ? 'ring-2 ring-offset-2 ring-blue-400' : '',
                    clickable ? 'cursor-pointer hover:opacity-75' : 'cursor-default',
                  ].join(' ')}
                >
                  {showGreen ? (
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : showRed ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  ) : completed ? (
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    idx + 1
                  )}
                </button>
                <span className={`mt-1 text-xs font-medium whitespace-nowrap ${labelClass}`}>
                  {step.label}
                </span>
              </div>
              {!isLast && (
                <div className={`h-0.5 flex-1 mx-2 mb-4 ${idx < progressStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
