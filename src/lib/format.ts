export function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso + "Z").getTime()) / 1000);
  if (s < 60) return `${Math.floor(s)}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export const kes = (n: number) =>
  new Intl.NumberFormat("en-KE", { style: "currency", currency: "KES",
    maximumFractionDigits: 0, notation: n >= 1_000_000 ? "compact" : "standard" }).format(n);

export const pct = (n: number) => `${(n * 100).toFixed(0)}%`;