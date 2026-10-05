"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bell, Bot, FileWarning, Home, MessageSquare, Search, Settings, ShieldAlert, ShieldCheck } from "lucide-react";
import { getHealth, getSummary } from "@/lib/api/client";
import { getToken } from "@/lib/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/claims", label: "Claims", icon: FileWarning },
  { href: "/investigations", label: "Investigations", icon: ShieldAlert },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
];

function useIdentity() {
  const [name, setName] = useState("…");
  useEffect(() => {
    const t = getToken();
    if (!t) return;
    try {
      const payload = JSON.parse(atob(t.split(".")[1]));
      const raw = String(payload.sub ?? "user").replace(/[-_]/g, " ");
      setName(raw.replace(/\b\w/g, c => c.toUpperCase()));
    } catch { /* keep placeholder */ }
  }, []);
  return name;
}

function useGreeting(name: string) {
  const [greeting, setGreeting] = useState("");
  useEffect(() => {
    const h = new Date().getHours();
    setGreeting(h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening");
  }, []);
  return `${greeting}, ${name.split(" ")[0]}`;
}

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-card">
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 shadow-lg shadow-blue-500/20">
          <Bot className="h-6 w-6 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold tracking-wide text-foreground">INSUREAI</p>
          <p className="text-[10px] leading-tight text-muted-foreground">Multi-Agent Insurance<br />Intelligence Platform</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {NAV.map(n => {
          const active = n.href === "/" ? pathname === "/" : pathname.startsWith(n.href);
          return (
            <Link key={n.href} href={n.href}
              className={cn("flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                active ? "bg-primary text-primary-foreground shadow-md shadow-blue-500/10"
                       : "text-muted-foreground hover:bg-accent hover:text-foreground")}>
              <n.icon className="h-4 w-4" />
              {n.label}
            </Link>
          );
        })}
        <div className="px-3 pt-6 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">Roadmap</div>
        {["Underwriting", "Actuarial Analysis", "Risk Intelligence", "Knowledge Base"].map(x => (
          <div key={x} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground/40">
            <span className="h-4 w-4 rounded border border-border" />{x}
          </div>
        ))}
      </nav>
      <div className="m-4 rounded-xl border border-border bg-background/50 p-4 text-center">
        <Bot className="mx-auto h-5 w-5 text-primary" />
        <p className="mt-2 text-xs font-semibold">Powered by</p>
        <p className="text-xs font-bold text-primary">Multi-Agent AI</p>
        <p className="mt-1 text-[10px] text-muted-foreground">Smarter decisions. Safer tomorrow.</p>
      </div>
    </aside>
  );
}

export function Header() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const name = useIdentity();
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth, refetchInterval: 15_000 });
  const summary = useQuery({ queryKey: ["summary"], queryFn: getSummary, refetchInterval: 15_000 });
  const pending = summary.data?.awaiting_approval ?? 0;
  const ok = health.data?.status === "ok";

  return (
    <header className="flex items-center gap-4">
      <div className="relative w-full max-w-xl">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && q.trim()) router.push(`/chat?q=${encodeURIComponent(q)}`); }}
          placeholder='Ask anything… e.g. "Investigate suspicious claims"'
          className="h-10 w-full rounded-xl border border-border bg-card pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
      </div>
      <div className="ml-auto flex items-center gap-4">
        <span className="flex items-center gap-2 text-xs">
          <span className={cn("h-2 w-2 rounded-full", ok ? "bg-emerald-500" : "bg-red-500")} />
          {ok ? "AI System Online" : "Degraded"}
        </span>
        <Link href="/approvals" className="relative rounded-lg border border-border bg-card p-2 hover:bg-accent">
          <Bell className="h-4 w-4" />
          {pending > 0 && (
            <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {pending}
            </span>
          )}
        </Link>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
            {name.slice(0, 1)}
          </div>
          <div className="text-xs leading-tight">
            <p className="font-semibold">{name}</p>
            <p className="text-muted-foreground">Actuary</p>
          </div>
        </div>
      </div>
    </header>
  );
}
