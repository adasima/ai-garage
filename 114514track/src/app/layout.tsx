import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google"; // Using Outfit for modern tech feel
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";

const fontSans = Outfit({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "CryptoDash - Cloud Run Optimized",
  description: "Real-time cryptocurrency dashboard",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className="dark">
      <body className={cn(fontSans.variable, "font-sans min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary")}>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 md:ml-64 relative min-h-screen transition-all duration-300 bg-dot-white/[0.05] overflow-x-hidden">
            {/* bg-dot is a placeholder for a pattern if we add one later */}
            <div className="absolute pointer-events-none inset-0 flex items-center justify-center bg-background [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"></div>
            <div className="relative z-10 w-full">
              {children}
            </div>
          </main>
        </div>
        <Toaster theme="dark" position="bottom-right" />
      </body>
    </html>
  );
}
