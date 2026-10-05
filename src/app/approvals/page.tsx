"use client";
import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { decideApproval, getApprovals } from "@/lib/api/client";
import { kes, pct } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

export default function ApprovalsPage() {
  const [filter, setFilter] = useState("PENDING");
  const qc = useQueryClient();
  const approvals = useQuery({ queryKey: ["approvals", filter], queryFn: () => getApprovals(filter), refetchInterval: 10_000 });
  const mutation = useMutation({
    mutationFn: (v: { id: number; decision: "APPROVED" | "REJECTED" }) => decideApproval(v.id, v.decision),
    onSuccess: () => qc.invalidateQueries(),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Human-in-the-Loop Queue</h1>
          <p className="text-sm text-muted-foreground">HIGH-risk investigations stop here by design — every decision is audit-recorded with your identity and timestamp.</p>
        </div>
        <Tabs value={filter} onValueChange={setFilter}>
          <TabsList><TabsTrigger value="PENDING">Pending</TabsTrigger><TabsTrigger value="">All</TabsTrigger></TabsList>
        </Tabs>
      </div>

      <div className="grid gap-3">
        {approvals.data?.items.length === 0 && <p className="text-sm text-muted-foreground">Queue clear.</p>}
        {approvals.data?.items.map(a => (
          <Card key={a.approval_id} className={cn(a.decision === "PENDING" && "border-red-500/30")}>
            <CardHeader className="pb-1 flex-row items-center justify-between space-y-0">
              <CardTitle className="text-sm font-mono">
                <Link href={`/investigations/${a.investigation_id}`} className="hover:underline">{a.investigation_id}</Link>
              </CardTitle>
              <Badge variant={a.decision === "PENDING" ? "destructive" : a.decision === "APPROVED" ? "secondary" : "outline"}>{a.decision}</Badge>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-muted-foreground">
                <span>claim <span className="font-mono text-foreground">{a.claim_id}</span></span>
                <span>{kes(a.claim_amount ?? 0)}</span>
                <span>score <span className="font-bold text-red-400">{a.fraud_probability != null ? pct(a.fraud_probability) : "—"}</span></span>
                <span>{a.loss_description}</span>
              </div>
              <p className="text-muted-foreground">{a.recommendation}</p>
              {a.decision === "PENDING" ? (
                <div className="flex gap-2 pt-1">
                  <Button size="sm" variant="destructive" disabled={mutation.isPending}
                    onClick={() => mutation.mutate({ id: a.approval_id, decision: "REJECTED" })}>Reject</Button>
                  <Button size="sm" variant="outline" disabled={mutation.isPending}
                    onClick={() => mutation.mutate({ id: a.approval_id, decision: "APPROVED" })}>Approve</Button>
                </div>
              ) : (
                <p className="text-[10px] text-muted-foreground">by {a.decided_by} · {a.decided_at?.slice(0, 16).replace("T", " ")}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}