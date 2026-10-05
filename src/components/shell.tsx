"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api/client";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/claims", label: "Claims" },
  { href: "/investigations", label: "Investigations" },
  { href: "/approvals", label: "Approvals" },
  { href: "/chat", label: "AI Chat" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 shrink-0 border-r bg-card p-4 space-y-1">
      <div className="px-2 py-4 text-sm font-semibold text-muted-foreground">Navigation</div>
      {NAV.map(n => (
        <Link key={n.href} href={n.href}
          className={cn("block rounded-md px-3 py-2 text-sm hover:bg-accent",
            (n.href === "/" ? pathname === "/" : pathname.startsWith(n.href))
              && "bg-primary text-primary-foreground")}>
          {n.label}
        </Link>
      ))}
      <div className="px-2 pt-8 text-xs text-muted-foreground">
        <div>Underwriting — roadmap</div>
        <div>Actuarial — roadmap</div>
        <div>Knowledge Base — roadmap</div>
      </div>
    </aside>
  );
}

export function HealthBadge() {
  const { data } = useQuery({ queryKey: ["health"], queryFn: getHealth, refetchInterval: 15_000 });
  if (!data) return <span className="text-xs text-muted-foreground">checking…</span>;
  const ok = data.status === "ok";
  return (
    <span className="flex items-center gap-2 text-xs">
      <span className={cn("h-2 w-2 rounded-full", ok ? "bg-emerald-500" : "bg-red-500")} />
      {ok ? "AI System Online" : `Degraded (db:${data.checks.db} kafka:${data.checks.kafka})`}
    </span>
  );
}