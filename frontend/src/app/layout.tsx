import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Header, Sidebar } from "@/components/shell";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "INSUREAI",
  description: "Multi-Agent Insurance Intelligence Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 space-y-6 p-6">
              <Header />
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
