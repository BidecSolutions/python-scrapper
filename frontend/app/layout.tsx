import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers/Providers";
import { AppLayoutWrapper } from "@/components/layout/AppLayoutWrapper";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LeadFlux AI - Lead Scraper SaaS",
  description: "AI-powered lead generation and enrichment platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <AppLayoutWrapper>
            {children}
          </AppLayoutWrapper>
        </Providers>
      </body>
    </html>
  );
}

