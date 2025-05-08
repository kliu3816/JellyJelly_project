import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "JellyJelly Video Analyzer",
  description: "AI-powered video analysis for Jelly videos",
  keywords: ["video analysis", "AI", "Jelly", "content analysis"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${geist.className} bg-gradient-to-b from-gray-900 to-gray-800 text-white min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
