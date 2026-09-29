import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bangladesh Legal Intelligence & Operations SaaS",
  description: "Bangladesh-first AI Legal Operating System for Legal Drafting, Review, and Research",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="bn">
      <body className="antialiased min-h-screen flex flex-col bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}
