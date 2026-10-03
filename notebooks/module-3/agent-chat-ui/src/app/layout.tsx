import type { Metadata } from "next";
import "./globals.css";

import React from "react";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { APP_CONFIG } from "@/lib/app-config";



export const metadata: Metadata = {
  title: APP_CONFIG.name,
  description: APP_CONFIG.description,
  icons: {
    icon: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans">
        <NuqsAdapter>{children}</NuqsAdapter>
      </body>
    </html>
  );
}
