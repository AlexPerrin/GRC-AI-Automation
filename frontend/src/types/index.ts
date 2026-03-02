export type VendorStatus =
  | 'INTAKE'
  | 'USE_CASE_REVIEW'
  | 'USE_CASE_APPROVED'
  | 'LEGAL_REVIEW'
  | 'LEGAL_APPROVED'
  | 'NDA_PENDING'
  | 'SECURITY_REVIEW'
  | 'SECURITY_APPROVED'
  | 'FINANCIAL_REVIEW'
  | 'FINANCIAL_APPROVED'
  | 'ONBOARDED'
  | 'REJECTED'

export type DocumentStage = 'USE_CASE' | 'LEGAL' | 'SECURITY' | 'FINANCIAL'
export type ReviewStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETE' | 'ERROR'
export type ReviewType = 'AI_ANALYSIS' | 'HUMAN_FORM'
export type DecisionAction = 'APPROVE' | 'REJECT' | 'APPROVE_WITH_CONDITIONS'

export interface Vendor {
  id: number
  name: string
  website: string | null
  description: string | null
  status: VendorStatus
  created_at: string
}

export interface Review {
  id: number
  vendor_id: number
  stage: DocumentStage
  review_type: ReviewType
  status: ReviewStatus
  ai_output: LegalAnalysisResult | SecurityAnalysisResult | FinancialAnalysisResult | null
  form_input: Record<string, unknown> | null
  triggered_at: string
  completed_at: string | null
}

export interface Decision {
  id: number
  review_id: number
  actor: string
  action: DecisionAction
  rationale: string
  conditions: string[] | null
  decided_at: string
}

export interface Document {
  id: number
  vendor_id: number
  stage: DocumentStage
  doc_type: string
  filename: string
  chroma_collection_id: string | null
  uploaded_at: string
}

export interface AuditLog {
  id: number
  vendor_id: number
  event_type: string
  actor: string
  payload: Record<string, unknown> | null
  timestamp: string
}

// AI output shapes — Legal
export interface LegalRegulationFinding {
  regulation: string
  article: string
  status: 'compliant' | 'partial' | 'non_compliant' | 'not_applicable'
  finding: string
  evidence: string
}

export interface LegalAnalysisResult {
  regulation_findings: LegalRegulationFinding[]
  overall_risk: 'low' | 'medium' | 'high' | 'critical'
  recommendation: 'approve' | 'approve_with_conditions' | 'reject'
  summary: string
  conditions: string[]
}

export interface ControlFinding {
  domain: string
  framework: string
  control_id: string
  status: 'met' | 'partial' | 'not_met' | 'not_applicable'
  finding: string
  evidence: string
  risk_score: number
}

export interface SecurityAnalysisResult {
  control_findings: ControlFinding[]
  overall_risk: 'low' | 'medium' | 'high' | 'critical'
  recommendation: 'approve' | 'approve_with_conditions' | 'reject'
  summary: string
  conditions: string[]
  risk_score: number
}

// AI output shapes — Financial
export interface FinancialFinding {
  category: string
  value: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  notes: string
}

export interface FinancialAnalysisResult {
  findings: FinancialFinding[]
  overall_risk_score: number
  recommendation: 'approve' | 'approve_with_conditions' | 'reject'
  summary: string
  conditions: string[]
}

// Form input types
export interface UseCaseFormInput {
  use_case_description: string
  business_justification: string
  data_types_involved: string[]
  estimated_users: number
  alternatives_considered: string
  reviewer_name: string
  recommendation: 'PROCEED' | 'DO_NOT_PROCEED'
  notes?: string
}

export interface FinancialRiskFormInput {
  vendor_annual_revenue?: string
  years_in_operation?: number
  financial_documents_reviewed: string[]
  concentration_risk_flag: boolean
  financial_stability_assessment: 'STABLE' | 'CONCERN' | 'HIGH_RISK'
  contract_value?: string
  reviewer_name: string
  recommendation: 'ACCEPTABLE' | 'ACCEPTABLE_WITH_CONDITIONS' | 'UNACCEPTABLE'
  conditions?: string[]
  notes?: string
}
