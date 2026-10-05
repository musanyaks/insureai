import { z, type ZodType } from "zod";
import { clearToken, ensureToken } from "@/lib/auth";
import * as t from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function request<T>(path: string, schema: ZodType<T>, init?: RequestInit): Promise<T> {
  const token = await ensureToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...init?.headers,
    },
  });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.reload(); // re-mints dev token
    throw new ApiError(401, "session expired");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* non-JSON error body */ }
    throw new ApiError(res.status, String(detail));
  }
  return schema.parse(await res.json());
}

const get = <T>(path: string, schema: ZodType<T>) => request(path, schema);
const post = <T>(path: string, schema: ZodType<T>, body?: unknown) =>
  request(path, schema, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

// system
export const getHealth = () => get("/health", t.Health);
export const getSummary = () => get("/analytics/summary", t.Summary);
export const getAgentActivity = (limit = 30) => get(`/analytics/agent-activity?limit=${limit}`, z.object({ items: z.array(t.AgentEvent) }));
export const getFraudAlerts = (limit = 8) => get(`/analytics/fraud-alerts?limit=${limit}`, z.object({ items: z.array(t.FraudAlert) }));
export const getTrend = (months = 6) => get(`/analytics/claims-trend?months=${months}`, z.object({ items: z.array(t.TrendPoint) }));
export const getCountyRisk = () => get("/analytics/county-risk", z.object({ items: z.array(t.CountyRisk) }));

// claims
export const getClaims = (q: { status?: string; county?: string; fraud?: boolean; limit?: number; offset?: number } = {}) => {
  const p = new URLSearchParams();
  if (q.status) p.set("status", q.status);
  if (q.county) p.set("county", q.county);
  if (q.fraud !== undefined) p.set("fraud", String(q.fraud));
  p.set("limit", String(q.limit ?? 25));
  p.set("offset", String(q.offset ?? 0));
  return get(`/claims?${p}`, t.ClaimPage);
};
export const getClaim = (id: string) => get(`/claims/${id}`, t.ClaimListItem.extend({
  accident_county: z.string(), loss_description: z.string().nullable(),
  theft_flag: z.boolean(), nights_weekend: z.boolean(),
  garage_id: z.string().nullable(), repair_estimate: z.number().nullable(),
  book_value_cost: z.number().nullable(), sum_insured: z.number(),
  policy_county: z.string(), inception_date: z.string(), policy_status: z.string(),
}));
export const getClaimEntities = (id: string) =>
  get(`/claims/${id}/entities`, z.object({ claim_id: z.string(), items: z.array(t.ClaimEntity) }).transform(r => ({ claim_id: r.claim_id, entities: r.items })));

// investigations
export const startInvestigation = (claimId: string) =>
  post("/investigations", t.InvestigationStart, { claim_id: claimId });
export const getInvestigations = (status?: string) =>
  get(`/investigations${status ? `?status=${status}` : ""}`, z.object({ items: z.array(z.object({
    investigation_id: z.string(), claim_id: z.string(), status: z.string(),
    started_at: z.string(), completed_at: z.string().nullable(), claim_amount: z.number(),
  })) }));
export const getInvestigation = (id: string) => get(`/investigations/${id}`, t.Investigation);
export const getTrace = (id: string) => get(`/investigations/${id}/trace`, t.Trace);

// approvals (HITL)
export const getApprovals = (decision?: string) =>
  get(`/approvals${decision ? `?decision=${decision}` : ""}`, t.ApprovalPage);
export const decideApproval = (id: number, decision: "APPROVED" | "REJECTED", note?: string) =>
  post(`/approvals/${id}/decision`, t.DecisionResult, { decision, note });

// chat
export const sendChat = (message: string) => post("/chat", t.ChatResponse, { message });