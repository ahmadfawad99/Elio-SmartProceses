import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Elio Control Plane",
  description: "Agentic AI for data center operations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
