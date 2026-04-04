import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TEX — AI Scouting",
  description: "AI-powered basketball scouting platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className="min-h-screen bg-background text-white antialiased">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
