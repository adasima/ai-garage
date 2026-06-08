"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Settings, Info, BarChart3, Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { useTranslation } from "@/hooks/use-translation";
import { LanguageToggle } from "./LanguageToggle";

export function Sidebar() {
    const pathname = usePathname();
    const [isMobileOpen, setIsMobileOpen] = useState(false);
    const { t } = useTranslation();

    const NAV_ITEMS = [
        { href: "/", label: t.common.dashboard, icon: LayoutDashboard },
        { href: "/admin", label: t.common.admin, icon: Settings },
    ];

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setIsMobileOpen(!isMobileOpen)}
                className="fixed top-4 left-4 z-50 p-2 rounded-md bg-secondary/80 backdrop-blur-md md:hidden border border-border/50"
            >
                <Menu className="w-6 h-6" />
            </button>

            {/* Sidebar Container */}
            <aside
                className={cn(
                    "fixed inset-y-0 left-0 z-40 w-64 transform transition-transform duration-300 ease-in-out md:translate-x-0 bg-background/60 backdrop-blur-xl border-r border-border/50 shadow-2xl",
                    isMobileOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <div className="flex flex-col h-full p-6">
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-10 px-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                            <BarChart3 className="w-5 h-5 text-white" />
                        </div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500 tracking-tight">
                            CryptoDash
                        </h1>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 space-y-2">
                        {NAV_ITEMS.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname === item.href;
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    onClick={() => setIsMobileOpen(false)}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                                        isActive
                                            ? "bg-primary/10 text-primary font-medium"
                                            : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                                    )}
                                >
                                    {isActive && (
                                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-full" />
                                    )}
                                    <Icon className={cn("w-5 h-5 transition-colors", isActive ? "text-primary" : "group-hover:text-foreground")} />
                                    <span>{item.label}</span>
                                </Link>
                            );
                        })}
                    </nav>

                    {/* Footer Info */}
                    <div className="pt-6 mt-6 border-t border-border/30 space-y-4">
                        <div className="flex items-center justify-between px-2">
                            <span className="text-sm text-muted-foreground">{t.common.language}</span>
                            <LanguageToggle />
                        </div>

                        <div className="flex items-center gap-2 text-xs text-muted-foreground px-2">
                            <Info className="w-3 h-3" />
                            <span>Cloud Run Free Tier Optimized</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Mobile Overlay */}
            {isMobileOpen && (
                <div
                    className="fixed inset-0 z-30 bg-black/60 md:hidden backdrop-blur-sm"
                    onClick={() => setIsMobileOpen(false)}
                />
            )}
        </>
    );
}
