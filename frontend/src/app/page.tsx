"use client";
import Link from "next/link";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, ArrowDownRight, ArrowUpRight, BarChart3, Car, FileText, Lightbulb, MessageSquare, Search, ShieldCheck, ShieldAlert, Wallet, Zap } from "lucide-react";
import { getCountyRisk, getFraudAlerts, getSummary, getTrend, getTypologies } from "@/lib/api/client";
import { kes, pct } from "@/lib/format";
import { AgentActivity } from "@/components/agent-activity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { getToken } from "@/lib/auth";

const TYPO_TONE: Record<string, string> = {
  CLEAN: "#475569", RING: "#ef4444", INFLATION: "#f97316",
  EARLY_CLAIM: "#eab308", GEO_ANOMALY: "#8b5cf6",
};
const riskTone: Record<string, string> = {
  "VERY HIGH": "bg-red-500/15 text-red-400", HIGH: "bg-orange-500/15 text-orange-400",
  MEDIUM: "bg-yellow-500/15 text-yellow-400", LOW: "bg-emerald-500/15 text-emerald-400",
};

function Kpi({ icon: Icon, tone, label, value, sub, delta, alert }: {
  icon: typeof Car; tone: string; label: string; value: string;
  sub?: string; delta?: number | null; alert?: boolean;
}) {
  return (
    <Card className={cn(alert && "border-red-500/50 shadow-lg shadow-red-500/5")}>
      <CardContent className="flex items-start gap-3 p-4">
        <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg shadow-md", tone)}>
          <Icon className="h-5 w-5 text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xl font-bold leading-tight">{value}</p>
          {delta != null && (
            <p className={cn("text-[11px] font-medium", delta >= 0 ? "text-emerald-400" : "text-red-400")}>
              {delta >= 0 ? <ArrowUpRight className="inline h-3 w-3" /> : <ArrowDownRight className="inline h-3 w-3" />}
              {" "}{Math.abs(delta * 100).toFixed(1)}% vs last month
            </p>
          )}
          {delta == null && sub && <p className="text-[11px] text-muted-foreground">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const summary = useQuery({ queryKey: ["summary"], queryFn: getSummary, refetchInterval: 15_000 });
  const trend = useQuery({ queryKey: ["trend"], queryFn: () => getTrend(6) });
  const alerts = useQuery({ queryKey: ["fraud-alerts"], queryFn: () => getFraudAlerts(5) });
  const counties = useQuery({ queryKey: ["county-risk"], queryFn: getCountyRisk });
  const typ = useQuery({ queryKey: ["typologies"], queryFn: getTypologies });
  const s = summary.data;

  // Honest delta: only where the trend gives us two real months
  const tItems = trend.data?.items ?? [];
  const last = tItems[tItems.length - 1], prev = tItems[tItems.length - 2];
  const claimsDelta = last && prev && prev.claims > 0 ? (last.claims - prev.claims) / prev.claims : null;

  const insights = useMemo(() => {
    const cs = counties.data?.items ?? [];
    const worst = [...cs].sort((a, b) => (b.fraud_rate ?? 0) - (a.fraud_rate ?? 0))[0];
    const busiest = [...cs].sort((a, b) => b.claims - a.claims)[0];
    const out: { text: string; level: "High" | "Medium" }[] = [];
    if ((s?.awaiting_approval ?? 0) > 0)
      out.push({ text: `${s!.awaiting_approval} investigation(s) await human decision in the HITL queue.`, level: "High" });
    if (worst && (worst.fraud_rate ?? 0) > 0)
      out.push({ text: `${worst.county} has the highest fraud incidence at ${pct(worst.fraud_rate ?? 0)} of claims.`, level: "High" });
    if (busiest) out.push({ text: `${busiest.county} carries the largest claim volume (${busiest.claims} claims).`, level: "Medium" });
    if (s) out.push({ text: `${s.agent_events_24h} agent events recorded in the audit trail over the last 24 hours.`, level: "Medium" });
    return out;
  }, [counties.data, s]);

  const actions = [
    { label: "Investigate Suspicious Claims", href: "/claims?fraud=true", icon: Search, tone: "bg-red-600 hover:bg-red-500", enabled: true },
    { label: "Run Actuarial Analysis", href: null, icon: BarChart3, tone: "bg-violet-600", enabled: false },
    { label: "Generate Portfolio Report", href: null, icon: FileText, tone: "bg-blue-600", enabled: false },
    { label: "Ask AI Assistant", href: "/chat", icon: MessageSquare, tone: "bg-emerald-600 hover:bg-emerald-500", enabled: true },
  ];

  const totalClaims = typ.data?.items.reduce((a, b) => a + b.claims, 0) ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Portfolio Overview</h1>
          <p className="text-sm text-muted-foreground">Live aggregates from the platform database — every number is a real query.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Kpi icon={FileText} tone="bg-blue-600" label="Total Policies" value={s ? s.policies.toLocaleString() : "—"} sub="seeded portfolio" />
        <Kpi icon={Car} tone="bg-emerald-600" label="Total Claims" value={s ? s.claims.toLocaleString() : "—"} sub={s ? kes(s.claims_value) : undefined} delta={claimsDelta} />
        <Kpi icon={ShieldAlert} tone="bg-violet-600" label="Fraud Alerts" value={s ? s.fraud_alerts.toLocaleString() : "—"} sub="HIGH + MEDIUM scored" />
        <Kpi icon={AlertTriangle} tone="bg-amber-600" label="Awaiting Approval" value={s ? String(s.awaiting_approval) : "—"} alert={(s?.awaiting_approval ?? 0) > 0} />
        <Kpi icon={Wallet} tone="bg-cyan-700" label="Total Claims Value" value={s ? kes(s.claims_value) : "—"} sub="all claims" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-0"><CardTitle className="text-sm">Claims Trend</CardTitle></CardHeader>
          <CardContent className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={tItems}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d47" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#7c8db0" }} stroke="#1e2d47" />
                <YAxis tick={{ fontSize: 11, fill: "#7c8db0" }} stroke="#1e2d47" />
                <Tooltip contentStyle={{ background: "#0f1a2e", border: "1px solid #1e2d47", borderRadius: 8, fontSize: 12 }} />
                <Line type="monotone" dataKey="claims" name="Total" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="fraudulent" name="Fraudulent" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <AgentActivity />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2 flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm">Top Scored Investigations</CardTitle>
            <Link href="/investigations" className="text-xs text-primary hover:underline">View all</Link>
          </CardHeader>
          <CardContent>
            <table className="w-full text-xs">
              <thead className="text-muted-foreground"><tr className="text-left">
                <th className="py-1 font-medium">Claim</th><th className="font-medium">Amount</th>
                <th className="font-medium">Score</th><th className="font-medium">Status</th>
              </tr></thead>
              <tbody>
                {alerts.data?.items.map(a => (
                  <tr key={a.investigation_id} className="border-t border-border">
                    <td className="py-2 font-mono">
                      <Link href={`/investigations/${a.investigation_id}`} className="hover:text-primary">
                        {a.claim_id}
                      </Link>
                    </td>
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
          <CardHeader className="pb-0"><CardTitle className="text-sm">Claims by Typology</CardTitle></CardHeader>
          <CardContent className="relative h-60">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={typ.data?.items ?? []} dataKey="claims" nameKey="typology"
                     innerRadius={52} outerRadius={78} paddingAngle={2} strokeWidth={0}>
                  {(typ.data?.items ?? []).map((sl, i) => (
                    <Cell key={i} fill={TYPO_TONE[sl.typology] ?? "#64748b"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0f1a2e", border: "1px solid #1e2d47", borderRadius: 8, fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-lg font-bold">{totalClaims.toLocaleString()}</p>
              <p className="text-[10px] text-muted-foreground">Total Claims</p>
            </div>
            <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 pt-1 text-[10px] text-muted-foreground">
              {(typ.data?.items ?? []).map(sl => (
                <span key={sl.typology} className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full" style={{ background: TYPO_TONE[sl.typology] ?? "#64748b" }} />
                  {sl.typology} {pct(totalClaims ? sl.claims / totalClaims : 0)}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Risk by County</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {counties.data?.items.map(c => (
              <div key={c.county} className="flex items-center gap-2 text-xs">
                <span className="w-24 font-medium">{c.county}</span>
                <span className="text-muted-foreground">{c.claims} claims · {pct(c.fraud_rate ?? 0)}</span>
                <span className={cn("ml-auto rounded px-1.5 py-0.5 text-[10px] font-semibold", riskTone[c.risk_level])}>
                  {c.risk_level}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2 flex-row items-center gap-2 space-y-0">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            <CardTitle className="text-sm">Key Insights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {insights.map((ins, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg border border-border bg-background/40 p-2.5 text-xs">
                <Zap className="h-3.5 w-3.5 shrink-0 text-primary" />
                <span className="flex-1">{ins.text}</span>
                <Badge variant={ins.level === "High" ? "destructive" : "secondary"}>{ins.level}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2 flex-row items-center gap-2 space-y-0">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {actions.map(a => a.enabled && a.href ? (
              <Link key={a.label} href={a.href}
                className={cn("flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium text-white shadow-md transition-colors", a.tone)}>
                <a.icon className="h-4 w-4" />{a.label}
              </Link>
            ) : (
              <div key={a.label}
                className="flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium text-white/60 opacity-70">
                <a.icon className="h-4 w-4" />{a.label}
                <span className="ml-auto rounded bg-black/30 px-1.5 py-0.5 text-[10px]">roadmap</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
