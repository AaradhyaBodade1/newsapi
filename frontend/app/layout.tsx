import type { Metadata } from "next";
import { Source_Serif_4, Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif",
  weight: ["400", "600", "700"],
  display: "swap",
});

const sans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Arka News",
    template: "%s | Arka News",
  },
  description: "Arka News — coverage across Technology, Business, Stock Market, Sports, and more.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable}`}>
      <body className="min-h-screen flex flex-col font-sans" suppressHydrationWarning>
        <Header />
        <main className="flex-1 mx-auto max-w-6xl w-full px-4 py-10 sm:py-12">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
