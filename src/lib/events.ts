export const AGENT_TONE: Record<string, string> = {
  orchestrator: "bg-violet-500", claims: "bg-blue-500", fraud: "bg-red-500",
  actuarial: "bg-emerald-500", sql: "bg-amber-500", api: "bg-slate-500",
};

export function agentTone(agent: string): string {
  return AGENT_TONE[agent] ?? (agent.startsWith("human:") ? "bg-pink-500" : "bg-slate-500");
}

export function agentLabel(agent: string): string {
  return agent.startsWith("human:") ? `Human (${agent.slice(6)})` : agent;
}

export const EVENT_META: Record<string, { label: string; ok: boolean }> = {
  "claim.registered":              { label: "Claim registered", ok: true },
  "claim.review_requested":        { label: "Review requested", ok: true },
  "claim.context_requested":       { label: "Context requested", ok: true },
  "claim.context":                 { label: "Context assembled", ok: true },
  "fraud.score_requested":         { label: "Scoring requested", ok: true },
  "fraud.score_completed":         { label: "Scored", ok: true },
  "investigation.awaiting_approval": { label: "Awaiting human approval", ok: false },
  "approval.decided":              { label: "Human decided", ok: true },
  "investigation.completed":       { label: "Investigation completed", ok: true },
  "agent.error":                   { label: "Agent error", ok: false },
};
export const eventMeta = (e: string) => EVENT_META[e] ?? { label: e, ok: true };