"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getFraudAlerts, getSummary, getTrend, getCountyRisk } from "@/lib/api/client";
import { kes, pct } from "@/lib/format";
import { AgentActivity } from "@/components/agent-activity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const riskTone: Record<string, string> = {
  "VERY HIGH": "bg-red-500/15 text-red-400", HIGH: "bg-orange-500/15 text-orange-400",
  MEDIUM: "bg-yellow-500/15 text-yellow-400", LOW: "bg-emerald-500/15 text-emerald-400",
};

function Kpi({ label, value, sub, alert }: { label: string; value: string; sub?: string; alert?: boolean }) {
  return (
    <Card className={cn(alert && "border-red-500/40")}>
      <CardHeader className="pb-1"><CardTitle className="text-xs font-medium text-muted-foreground">{label}</CardTitle></CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const summary = useQuery({ queryKey: ["summary"], queryFn: getSummary, refetchInterval: 15_000 });
  const trend = useQuery({ queryKey: ["trend"], queryFn: () => getTrend(6) });
  const alerts = useQuery({ queryKey: ["fraud-alerts"], queryFn: () => getFraudAlerts(8) });
  const counties = useQuery({ queryKey: ["county-risk"], queryFn: getCountyRisk });
  const s = summary.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Portfolio Overview</h1>
        <p className="text-sm text-muted-foreground">Live aggregates from the platform database.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Kpi label="Total Policies" value={s ? s.policies.toLocaleString() : "—"} />
        <Kpi label="Total Claims" value={s ? s.claims.toLocaleString() : "—"} sub={s ? kes(s.claims_value) : undefined} />
        <Kpi label="Fraud Alerts" value={s ? s.fraud_alerts.toLocaleString() : "—"} sub="HIGH + MEDIUM scored" />
        <Kpi label="Awaiting Approval" value={s ? String(s.awaiting_approval) : "—"} sub="HITL gate queue" alert={(s?.awaiting_approval ?? 0) > 0} />
        <Kpi label="Agent Events (24h)" value={s ? s.agent_events_24h.toLocaleString() : "—"} sub="audit trail" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-0"><CardTitle className="text-sm">Claims Trend</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend.data?.items ?? []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #27272a", fontSize: 12 }} />
                <Line type="monotone" dataKey="claims" name="Total" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="fraudulent" name="Fraudulent" stroke="#f97316" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <AgentActivity />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2 flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm">Top Scored Investigations</CardTitle>
            <Link href="/investigations" className="text-xs text-muted-foreground hover:underline">View all</Link>
          </CardHeader>
          <CardContent>
            <table className="w-full text-xs">
              <thead className="text-muted-foreground"><tr className="text-left">
                <th className="py-1 font-medium">Investigation</th><th className="font-medium">Claim</th>
                <th className="font-medium">Amount</th><th className="font-medium">Score</th><th className="font-medium">Status</th>
              </tr></thead>
              <tbody>
                {alerts.data?.items.map(a => (
                  <tr key={a.investigation_id} className="border-t">
                    <td className="py-2 font-mono">
                      <Link href={`/investigations/${a.investigation_id}`} className="hover:underline">{a.investigation_id.slice(0, 12)}</Link>
                    </td>
                    <td className="font-mono">{a.claim_id}</td>
                    <td>{kes(a.claim_amount)}</td>
                    <td className={cn("font-semibold", (a.fraud_probability ?? 0) >= 0.7 ? "text-red-400" : "text-yellow-400")}>
                      {a.fraud_probability != null ? pct(a.fraud_probability) : "—"}
                    </td>
                    <td><Badge variant="outline">{a.status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Risk by County</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {counties.data?.items.map(c => (
              <div key={c.county} className="flex items-center gap-2 text-xs">
                <span className="w-24 font-medium">{c.county}</span>
                <span className="text-muted-foreground">{c.claims} claims · {pct(c.fraud_rate ?? 0)} fraud</span>
                <span className={cn("ml-auto rounded px-1.5 py-0.5 text-[10px] font-semibold", riskTone[c.risk_level])}>{c.risk_level}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}