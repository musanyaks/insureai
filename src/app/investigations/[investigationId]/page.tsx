"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { decideApproval, getInvestigation, getTrace, type FraudResult as FraudResultT } from "@/lib/api/client";
import { FraudResult, type TraceMessage } from "@/lib/api/types";
import { agentLabel, agentTone, eventMeta } from "@/lib/events";
import { kes, pct, timeAgo } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useState } from "react";

function extractFraudResult(trace?: TraceMessage[]): FraudResultT | null {
  const msg = trace?.find(m => m.event === "fraud.score_completed");
  if (!msg) return null;
  const parsed = FraudResult.safeParse(msg.payload.result);
  return parsed.success ? parsed.data : null;
}

function TraceTimeline({ messages }: { messages: TraceMessage[] }) {
  return (
    <ol className="space-y-0">
      {messages.map((m, i) => {
        const meta = eventMeta(m.event);
        return (
          <li key={i} className="relative flex gap-3 pb-4 last:pb-0">
            {i < messages.length - 1 && <span className="absolute left-[7px] top-4 h-full w-px bg-border" />}
            <span className={cn("mt-1 h-[15px] w-[15px] shrink-0 rounded-full border-2 border-background",
              meta.ok ? agentTone(m.from_agent) : "bg-red-600")} />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-x-2 text-xs">
                <span className="font-semibold">{meta.label}</span>
                <span className="text-muted-foreground">{agentLabel(m.from_agent)} → {agentLabel(m.to_agent)}</span>
                <span className="ml-auto text-[10px] text-muted-foreground">{timeAgo(m.created_at)}</span>
              </div>
              <details className="mt-1">
                <summary className="cursor-pointer text-[10px] text-muted-foreground">payload</summary>
                <pre className="mt-1 max-h-40 overflow-auto rounded bg-muted p-2 text-[10px] leading-relaxed">
                  {JSON.stringify(m.payload, null, 2)}
                </pre>
              </details>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function DecisionBox({ approvalId }: { approvalId: number }) {
  const qc = useQueryClient();
  const [note, setNote] = useState("");
  const mutation = useMutation({
    mutationFn: (decision: "APPROVED" | "REJECTED") => decideApproval(approvalId, decision, note || undefined),
    onSuccess: () => qc.invalidateQueries(),
  });
  return (
    <Card className="border-red-500/50">
      <CardHeader className="pb-2"><CardTitle className="text-sm text-red-400">Human decision required</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Textarea placeholder="Decision note (recorded in the audit trail)…" value={note} onChange={e => setNote(e.target.value)} />
        <div className="flex gap-2">
          <Button variant="destructive" size="sm" disabled={mutation.isPending}
            onClick={() => mutation.mutate("REJECTED")}>Reject claim</Button>
          <Button size="sm" variant="outline" disabled={mutation.isPending}
            onClick={() => mutation.mutate("APPROVED")}>Approve — proceed to settlement</Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function InvestigationPage() {
  const { investigationId } = useParams<{ investigationId: string }>();
  const inv = useQuery({ queryKey: ["investigation", investigationId], queryFn: () => getInvestigation(investigationId), refetchInterval: 5_000 });
  const trace = useQuery({ queryKey: ["trace", investigationId], queryFn: () => getTrace(investigationId), refetchInterval: 5_000 });
  const fr = extractFraudResult(trace.data?.messages);
  const report = inv.data?.report;
  const status = inv.data?.status;

  if (inv.isLoading) return <p className="text-sm text-muted-foreground">loading…</p>;
  if (inv.isError) return <p className="text-sm text-red-400">Investigation not found.</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold font-mono">{inv.data!.investigation_id}</h1>
        <Badge variant={status === "COMPLETED" ? "secondary" : status === "AWAITING_APPROVAL" ? "destructive" : "default"}>{status}</Badge>
        {fr && <span className={cn("text-lg font-bold", fr.risk_level === "HIGH" ? "text-red-400" : fr.risk_level === "MEDIUM" ? "text-yellow-400" : "text-emerald-400")}>
          {pct(fr.fraud_probability)} fraud risk
        </span>}
        <Link href={`/claims/${inv.data!.claim_id}`} className="ml-auto text-xs text-muted-foreground hover:underline">claim {inv.data!.claim_id} →</Link>
      </div>

      {status === "AWAITING_APPROVAL" && inv.data!.approval_id != null && <DecisionBox approvalId={inv.data!.approval_id} />}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Agent Trace</CardTitle></CardHeader>
          <CardContent>{trace.data && <TraceTimeline messages={trace.data.messages} />}</CardContent>
        </Card>

        <div className="space-y-4">
          {fr && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Score Evidence <span className="ml-2 font-normal text-[10px] text-muted-foreground">{fr.model_version}</span></CardTitle></CardHeader>
              <CardContent className="space-y-1.5">
                {fr.reason_codes.length === 0 && <p className="text-xs text-muted-foreground">No adverse indicators.</p>}
                {fr.reason_codes.map(rc => (
                  <div key={rc.code} className="flex items-start gap-2 text-xs">
                    <span className={cn("rounded px-1 text-[10px] font-bold", rc.contribution >= 0.3 ? "bg-red-500/15 text-red-400" : "bg-yellow-500/15 text-yellow-400")}>+{rc.contribution.toFixed(2)}</span>
                    <span>{rc.description}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {report && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Investigation Report</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-xs">
                <p className="rounded-md bg-muted p-3 leading-relaxed">{report.narrative}</p>
                {report.evidence.length > 0 && (
                  <div><p className="mb-1 font-semibold">Evidence</p>
                    <ul className="list-disc space-y-1 pl-4 text-muted-foreground">{report.evidence.map((e, i) => <li key={i}>{e}</li>)}</ul></div>
                )}
                <div><p className="mb-1 font-semibold">Recommended actions</p>
                  <ul className="list-decimal space-y-1 pl-4 text-muted-foreground">{report.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}</ul></div>
                {report.human_decision && (
                  <p className="font-semibold">Human decision: <span className={report.human_decision === "REJECTED" ? "text-red-400" : "text-emerald-400"}>{report.human_decision}</span></p>
                )}
                <p className="text-[10px] text-muted-foreground">confidence {pct(report.confidence)} · assembled from typed agent outputs</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}