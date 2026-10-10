import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Leads Tracker",
  description: "Submit your information and resume to get in touch with our attorneys.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
