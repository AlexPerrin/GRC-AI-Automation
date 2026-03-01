import type { VendorStatus } from '../types'

const STEPS = [
  'Use Case',
  'Legal Review',
  'NDA Confirmed',
  'Security Review',
  'Financial Review',
  'Onboarded',
]

function statusToStep(status: VendorStatus): number {
  switch (status) {
    case 'INTAKE':
    case 'USE_CASE_REVIEW':
    case 'USE_CASE_APPROVED':
      return 0
    case 'LEGAL_REVIEW':
    case 'LEGAL_APPROVED':
    case 'NDA_PENDING':
      return 1
    case 'SECURITY_REVIEW':
    case 'SECURITY_APPROVED':
      return 3
    case 'FINANCIAL_REVIEW':
    case 'FINANCIAL_APPROVED':
      return 4
    case 'ONBOARDED':
      return 5
    case 'REJECTED':
      return -1
    default:
      return 0
  }
}

interface StatusStepperProps {
  status: VendorStatus
}

export default function StatusStepper({ status }: StatusStepperProps) {
  if (status === 'REJECTED') {
    return (
      <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-red-800 font-medium">
        Vendor Rejected
      </div>
    )
  }

  const active = statusToStep(status)

  return (
    <nav aria-label="Progress">
      <ol className="flex items-center">
        {STEPS.map((step, idx) => {
          const completed = idx < active
          const current = idx === active
          const isLast = idx === STEPS.length - 1

          return (
            <li key={step} className={`flex items-center ${isLast ? '' : 'flex-1'}`}>
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors ${
                    completed
                      ? 'bg-blue-600 text-white'
                      : current
                        ? 'border-2 border-blue-600 bg-white text-blue-600'
                        : 'border-2 border-gray-300 bg-white text-gray-400'
                  }`}
                >
                  {completed ? (
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    idx + 1
                  )}
                </div>
                <span
                  className={`mt-1 text-xs font-medium whitespace-nowrap ${
                    current ? 'text-blue-600' : completed ? 'text-gray-700' : 'text-gray-400'
                  }`}
                >
                  {step}
                </span>
              </div>
              {!isLast && (
                <div
                  className={`h-0.5 flex-1 mx-2 mb-4 ${completed || (current && idx < active) ? 'bg-blue-600' : 'bg-gray-200'}`}
                />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
