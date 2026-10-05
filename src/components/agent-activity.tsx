"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getAgentActivity } from "@/lib/api/client";
import { agentLabel, agentTone, eventMeta } from "@/lib/events";
import { timeAgo } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function AgentActivity({ limit = 12 }: { limit?: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["agent-activity", limit],
    queryFn: () => getAgentActivity(limit),
    refetchInterval: 5_000,   // SSE upgrade later — same component shape
  });

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          AI Agent Activity
          <span className="flex h-2 w-2"><span className="animate-ping absolute h-2 w-2 rounded-full bg-emerald-400 opacity-75" /><span className="relative h-2 w-2 rounded-full bg-emerald-500" /></span>
          <span className="ml-auto text-xs font-normal text-muted-foreground">live · 5s</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 max-h-96 overflow-y-auto">
        {isLoading && <p className="text-xs text-muted-foreground">loading…</p>}
        {data?.items.length === 0 && <p className="text-xs text-muted-foreground">No agent traffic yet — trigger an investigation.</p>}
        {data?.items.map((e, i) => {
          const meta = eventMeta(e.event);
          return (
            <Link key={i} href={`/investigations/${e.correlation_id}`}
              className="flex items-center gap-2 rounded-md border p-2 text-xs hover:bg-accent/50">
              <span className={cn("h-2 w-2 shrink-0 rounded-full", agentTone(e.from_agent))} />
              <span className="font-medium">{agentLabel(e.from_agent)}</span>
              <span className="text-muted-foreground">→ {meta.label}</span>
              {e.claim_id && <span className="font-mono text-[10px] text-muted-foreground">{e.claim_id}</span>}
              {e.priority === "HIGH" && <span className="ml-auto rounded bg-red-500/15 px-1 text-[10px] text-red-400">HIGH</span>}
              <span className={cn("ml-auto text-[10px] text-muted-foreground", e.priority === "HIGH" && "ml-1")}>{timeAgo(e.created_at)}</span>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}