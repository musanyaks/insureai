import { z } from "zod";

export const Health = z.object({
  status: z.string(),
  environment: z.string(),
  checks: z.object({ db: z.boolean(), kafka: z.boolean() }),
  agents: z.array(z.string()),
});

export const ClaimListItem = z.object({
  claim_id: z.string(), policy_id: z.string(),
  loss_date: z.string(), reported_date: z.string(),
  claim_amount: z.number(), status: z.string(),
  is_fraud_label: z.boolean().nullable(), typology: z.string().nullable(),
  county: z.string(), vehicle_make: z.string(), vehicle_model: z.string(),
});
export const ClaimPage = z.object({
  total: z.number(), limit: z.number(), offset: z.number(),
  items: z.array(ClaimListItem),
});

// GET /claims/{id} returns claim + policy fields — a different shape from the list.
export const ClaimDetail = z.object({
  claim_id: z.string(), policy_id: z.string(),
  loss_date: z.string(), reported_date: z.string(),
  claim_amount: z.number(),
  repair_estimate: z.number().nullable(),
  book_value_cost: z.number().nullable(),
  garage_id: z.string().nullable(),
  accident_county: z.string(),
  loss_description: z.string().nullable(),
  theft_flag: z.boolean(), nights_weekend: z.boolean(),
  status: z.string(),
  vehicle_make: z.string(), vehicle_model: z.string(),
  sum_insured: z.number(), policy_county: z.string(),
  inception_date: z.string(), policy_status: z.string(),
});

export const ClaimEntity = z.object({
  entity_type: z.string(), entity_value: z.string(),
  other_links: z.number(), other_fraud_links: z.number(),
});

export const ReasonCode = z.object({
  code: z.string(), description: z.string(), contribution: z.number(),
});
export const FraudResult = z.object({
  claim_id: z.string(), fraud_probability: z.number(), risk_level: z.string(),
  reason_codes: z.array(ReasonCode), model_version: z.string(), scored_at: z.string(),
});
export type FraudResultData = z.infer<typeof FraudResult>;

export const AgentContribution = z.object({
  agent: z.string(), summary: z.string(), data: z.record(z.string(), z.unknown()),
});
export const Report = z.object({
  investigation_id: z.string(), claim_id: z.string(),
  fraud_probability: z.number(), risk_level: z.string(),
  evidence: z.array(z.string()),
  agents_consulted: z.array(AgentContribution),
  recommended_actions: z.array(z.string()),
  confidence: z.number(), narrative: z.string(),
  human_decision: z.string().nullable().optional(),
  audit_id: z.string().optional(),
});

export const InvestigationStart = z.object({
  investigation_id: z.string(), claim_id: z.string(), status: z.string(),
  priority: z.string().nullable(), already_running: z.boolean(),
});

export const Investigation = z.object({
  investigation_id: z.string(), claim_id: z.string(), status: z.string(),
  report: Report.nullable(), started_at: z.string(),
  completed_at: z.string().nullable(),
  approval_id: z.number().nullable(), approval_decision: z.string().nullable(),
  fraud_probability: z.number().nullable(), recommendation: z.string().nullable(),
});

export const TraceMessage = z.object({
  task_id: z.string(), from_agent: z.string(), to_agent: z.string(),
  event: z.string(), priority: z.string(),
  payload: z.record(z.string(), z.unknown()),
  model_version: z.string().nullable(), created_at: z.string(),
});
export const Trace = z.object({ investigation_id: z.string(), messages: z.array(TraceMessage) });

export const Approval = z.object({
  approval_id: z.number(), investigation_id: z.string().nullable(),
  fraud_probability: z.number().nullable(), recommendation: z.string().nullable(),
  decision: z.string(), decided_by: z.string().nullable(),
  decided_at: z.string().nullable(), created_at: z.string(),
  note: z.string().nullable(), claim_id: z.string().nullable(),
  claim_amount: z.number().nullable(), loss_description: z.string().nullable(),
});
export const ApprovalPage = z.object({ items: z.array(Approval) });
export const DecisionResult = z.object({
  approval_id: z.number(), decision: z.string(),
  decided_by: z.string(), claim_status: z.string(),
});

export const ChatResponse = z.object({
  intent: z.string(), text: z.string(), investigation_id: z.string().nullable(),
});

export const Summary = z.object({
  policies: z.number(), claims: z.number(), claims_value: z.number(),
  investigations_running: z.number(), awaiting_approval: z.number(),
  high_risk: z.number(), fraud_alerts: z.number(), agent_events_24h: z.number(),
});

export const AgentEvent = z.object({
  from_agent: z.string(), to_agent: z.string(), event: z.string(),
  priority: z.string(), correlation_id: z.string(),
  claim_id: z.string().nullable(), created_at: z.string(),
});

export const FraudAlert = z.object({
  investigation_id: z.string(), claim_id: z.string(),
  claim_amount: z.number(), status: z.string(), started_at: z.string(),
  fraud_probability: z.number().nullable(), risk_level: z.string().nullable(),
});

export const TrendPoint = z.object({
  month: z.string(), claims: z.number(), fraudulent: z.number(),
});

export const CountyRisk = z.object({
  county: z.string(), claims: z.number(), fraud_claims: z.number(),
  fraud_rate: z.number().nullable(), claims_value: z.number(), risk_level: z.string(),
});

export const TypologySlice = z.object({ typology: z.string(), claims: z.number() });

export const TypologySlice = z.object({ typology: z.string(), claims: z.number() });

export const TypologySlice = z.object({ typology: z.string(), claims: z.number() });
