"use client";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getClaim, getClaimEntities, startInvestigation } from "@/lib/api/client";
import { kes } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function ClaimPage() {
  const { claimId } = useParams<{ claimId: string }>();
  const router = useRouter();
  const claim = useQuery({ queryKey: ["claim", claimId], queryFn: () => getClaim(claimId) });
  const entities = useQuery({ queryKey: ["claim-entities", claimId], queryFn: () => getClaimEntities(claimId) });
  const inv = useMutation({
    mutationFn: () => startInvestigation(claimId),
    onSuccess: r => router.push(`/investigations/${r.investigation_id}`),
  });
  const c = claim.data;
  if (claim.isLoading) return <p className="text-sm text-muted-foreground">loading…</p>;
  if (!c) return <p className="text-sm text-red-400">Claim not found.</p>;

  const facts: [string, string][] = [
    ["Loss date", c.loss_date], ["Reported", c.reported_date],
    ["Amount", kes(c.claim_amount)], ["Repair estimate", c.repair_estimate ? kes(c.repair_estimate) : "—"],
    ["Book cost", c.book_value_cost ? kes(c.book_value_cost) : "—"], ["Sum insured", kes(c.sum_insured)],
    ["Policy county", c.policy_county], ["Accident county", c.accident_county],
    ["Garage", c.garage_id ?? "—"], ["Night/weekend", c.nights_weekend ? "Yes" : "No"],
    ["Theft", c.theft_flag ? "Yes" : "No"], ["Policy status", c.policy_status],
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold font-mono">{claimId}</h1>
        <p className="text-sm text-muted-foreground">{c.vehicle_make} {c.vehicle_model}</p>
        <Button className="ml-auto" size="sm" disabled={inv.isPending} onClick={() => inv.mutate()}>
          {inv.isPending ? "starting…" : "Investigate →"}
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">{c.loss_description}</p>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">Claim facts</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-x-8 gap-y-2 text-xs md:grid-cols-4">
          {facts.map(([k, v]) => (
            <div key={k}><p className="text-muted-foreground">{k}</p><p className="font-semibold">{v}</p></div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">Shared-entity links (ring detection)</CardTitle></CardHeader>
        <CardContent>
          <table className="w-full text-xs">
            <thead className="text-muted-foreground"><tr className="text-left">
              <th className="py-1 font-medium">Type</th><th className="font-medium">Value</th>
              <th className="font-medium">Other-policy claims</th><th className="font-medium">Flagged fraud</th>
            </tr></thead>
            <tbody>
              {entities.data?.entities.map(e => (
                <tr key={`${e.entity_type}-${e.entity_value}`} className="border-t">
                  <td className="py-1.5 font-semibold">{e.entity_type}</td>
                  <td className="font-mono text-[10px]">{e.entity_value}</td>
                  <td className={cn(e.other_links > 0 && "text-yellow-400 font-semibold")}>{e.other_links}</td>
                  <td className={cn(e.other_fraud_links > 0 && "text-red-400 font-semibold")}>{e.other_fraud_links}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}