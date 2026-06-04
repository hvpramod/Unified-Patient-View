import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

const inter = { className: "" };

export const metadata: Metadata = {
  title: "Unified Patient View",
  description: "AI-powered clinical data aggregation and reconciliation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
