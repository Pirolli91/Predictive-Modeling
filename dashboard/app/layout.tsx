import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NC Coastal Townhomes | Investment Dashboard",
  description:
    "New-construction coastal North Carolina townhomes under $240,000, tracked daily.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
