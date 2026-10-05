"use client";
import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getClaims } from "@/lib/api/client";
import { kes } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

function ClaimsTable() {
  const params = useSearchParams();
  const [fraud, setFraud] = useState<boolean | undefined>(
    params.get("fraud") === "true" ? true : undefined);
  const [county, setCounty] = useState("");
  const [offset, setOffset] = useState(0);
  const q = useQuery({ queryKey: ["claims", fraud, county, offset],
                       queryFn: () => getClaims({ fraud, county: county || undefined, offset }) });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-semibold">Claims</h1>
        <div className="ml-auto flex items-center gap-2">
          <Input placeholder="county…" className="h-8 w-36" value={county}
                 onChange={e => { setCounty(e.target.value); setOffset(0); }} />
          <Button size="sm" variant={fraud === undefined ? "default" : "outline"} onClick={() => setFraud(undefined)}>All</Button>
          <Button size="sm" variant={fraud === true ? "default" : "outline"} onClick={() => setFraud(true)}>Flagged</Button>
          <Button size="sm" variant={fraud === false ? "default" : "outline"} onClick={() => setFraud(false)}>Clean</Button>
        </div>
      </div>
      <Card><CardContent className="p-0">
        <table className="w-full text-xs">
          <thead className="text-muted-foreground border-b"><tr className="text-left">
            <th className="p-3 font-medium">Claim</th><th className="font-medium">Vehicle</th>
            <th className="font-medium">County</th><th className="font-medium">Amount</th>
            <th className="font-medium">Typology</th><th className="font-medium">Status</th><th />
          </tr></thead>
          <tbody>
            {q.data?.items.map(c => (
              <tr key={c.claim_id} className="border-b last:border-0 hover:bg-accent/40">
                <td className="p-3 font-mono">
                  <Link href={`/claims/${c.claim_id}`} className="hover:underline">{c.claim_id}</Link>
                </td>
                <td>{c.vehicle_make} {c.vehicle_model}</td>
                <td>{c.county}</td>
                <td>{kes(c.claim_amount)}</td>
                <td>{c.typology && <Badge variant="destructive">{c.typology}</Badge>}</td>
                <td><Badge variant="outline">{c.status}</Badge></td>
                <td className="text-muted-foreground">
                  {c.is_fraud_label === true && <span className="text-red-400">labeled fraud</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent></Card>
      <div className="flex gap-2 text-xs">
        <Button size="sm" variant="outline" disabled={offset === 0}
                onClick={() => setOffset(o => Math.max(0, o - 25))}>Prev</Button>
        <span className="self-center text-muted-foreground">
          {q.data ? `${offset + 1}–${Math.min(offset + 25, q.data.total)} of ${q.data.total}` : ""}
        </span>
        <Button size="sm" variant="outline" disabled={!!q.data && offset + 25 >= q.data.total}
                onClick={() => setOffset(o => o + 25)}>Next</Button>
      </div>
    </div>
  );
}

export default function ClaimsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">loading…</p>}>
      <ClaimsTable />
    </Suspense>
  );
}
