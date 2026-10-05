import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar, HealthBadge } from "@/components/shell";

export const metadata: Metadata = { title: "INSUREAI", description: "Multi-Agent Insurance Intelligence Platform" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-6 space-y-6">
              <header className="flex items-center justify-between">
                <div className="text-lg font-semibold tracking-wide">INSUREAI</div>
                <HealthBadge />
              </header>
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}