export type StageTab = 'use_case' | 'nda' | 'legal' | 'security' | 'financial' | 'onboarding'

const STEPS: { label: string; tab: StageTab }[] = [
  { label: 'Use Case',            tab: 'use_case'  },
  { label: 'NDA',                 tab: 'nda'       },
  { label: 'Legal Review',        tab: 'legal'     },
  { label: 'Security Review',     tab: 'security'  },
  { label: 'Financial Review',    tab: 'financial' },
  { label: 'Onboarding Decision', tab: 'onboarding' },
]

interface StatusStepperProps {
  /**
   * Per-step completion flags, one per step (indices 0–4 for Use Case through
   * Financial). The Onboarding step (index 5) is driven by isOnboarded / isRejected.
   */
  stepCompletion: boolean[]
  isOnboarded: boolean
  isRejected: boolean
  activeTab: StageTab
  onTabChange: (tab: StageTab) => void
}

export default function StatusStepper({
  stepCompletion,
  isOnboarded,
  isRejected,
  activeTab,
  onTabChange,
}: StatusStepperProps) {
  return (
    <nav aria-label="Progress">
      <ol className="flex items-center">
        {STEPS.map((step, idx) => {
          const isLast             = idx === STEPS.length - 1
          const isOnboardingStep   = isLast
          const hasRing            = step.tab === activeTab

          // Completion is tracked independently per step
          const completed = isOnboardingStep
            ? isOnboarded
            : (stepCompletion[idx] ?? false)

          const showRed = isOnboardingStep && isRejected

          const circleClass = isOnboardingStep && isOnboarded
            ? 'bg-green-600 text-white'
            : showRed
              ? 'bg-red-600 text-white'
              : completed
                ? 'bg-blue-600 text-white'
                : hasRing
                  ? 'border-2 border-blue-600 bg-white text-blue-600'
                  : 'border-2 border-gray-300 bg-white text-gray-400'

          const labelClass = isOnboardingStep && isOnboarded
            ? 'text-green-700 font-semibold'
            : isOnboardingStep && isRejected
              ? 'text-red-700 font-semibold'
              : hasRing
                ? 'text-blue-600 font-semibold'
                : completed
                  ? 'text-gray-700'
                  : 'text-gray-400'

          return (
            <li key={step.label} className={`flex items-center ${isLast ? '' : 'flex-1'}`}>
              <div className="flex flex-col items-center">
                <button
                  type="button"
                  onClick={() => onTabChange(step.tab)}
                  className={[
                    'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors cursor-pointer hover:opacity-75',
                    circleClass,
                    hasRing ? 'ring-2 ring-offset-2 ring-blue-400' : '',
                  ].join(' ')}
                >
                  {isOnboardingStep && isOnboarded ? (
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
                <div className={`h-0.5 flex-1 mx-2 mb-4 ${(stepCompletion[idx] ?? false) ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
