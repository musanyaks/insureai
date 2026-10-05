"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getInvestigations } from "@/lib/api/client";
import { kes } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export default function InvestigationsPage() {
  const { data } = useQuery({ queryKey: ["investigations"],
                              queryFn: () => getInvestigations(), refetchInterval: 10_000 });
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Investigations</h1>
      <Card><CardContent className="p-0">
        <table className="w-full text-xs">
          <thead className="text-muted-foreground border-b"><tr className="text-left">
            <th className="p-3 font-medium">ID</th><th className="font-medium">Claim</th>
            <th className="font-medium">Amount</th><th className="font-medium">Status</th>
            <th className="font-medium">Started</th>
          </tr></thead>
          <tbody>
            {data?.items.map(i => (
              <tr key={i.investigation_id} className="border-b last:border-0 hover:bg-accent/40">
                <td className="p-3 font-mono">
                  <Link href={`/investigations/${i.investigation_id}`} className="hover:underline">
                    {i.investigation_id}
                  </Link>
                </td>
                <td className="font-mono">{i.claim_id}</td>
                <td>{kes(i.claim_amount)}</td>
                <td><Badge variant={i.status === "COMPLETED" ? "secondary"
                      : i.status === "AWAITING_APPROVAL" ? "destructive" : "default"}>{i.status}</Badge></td>
                <td className="text-muted-foreground">{i.started_at.slice(0, 16).replace("T", " ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent></Card>
    </div>
  );
}
