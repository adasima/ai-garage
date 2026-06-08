"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { CryptoData } from "@/lib/types";
import { useCurrencyStore } from "@/components/CurrencyToggle";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/hooks/use-translation";

interface Props {
    data: CryptoData | undefined; // Undefined = loading skeleton
}

export function CryptoTile({ data }: Props) {
    const { currency, formatPrice } = useCurrencyStore();
    const { t } = useTranslation();
    const [flash, setFlash] = useState(false);
    const prevPriceRef = useRef<number>(0);

    // Effect to trigger flash when price changes
    useEffect(() => {
        if (data) {
            const currentPrice = data.prices[currency as keyof typeof data.prices];

            // If we have a previous price and it's different (and not first load 0 -> val)
            if (prevPriceRef.current > 0 && prevPriceRef.current !== currentPrice) {
                setFlash(true);
                // Remove class after animation finishes to allow re-trigger
                const timer = setTimeout(() => setFlash(false), 500);
                return () => clearTimeout(timer);
            }
            prevPriceRef.current = currentPrice;
        }
    }, [data, currency]);

    if (!data) {
        return (
            <div className="relative overflow-hidden rounded-2xl border border-border/50 bg-secondary/20 p-6 shadow-sm backdrop-blur-sm">
                <div className="flex items-center gap-4 mb-4">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-3 w-16" />
                    </div>
                </div>
                <div className="space-y-2 mt-6">
                    <Skeleton className="h-8 w-32" />
                    <Skeleton className="h-4 w-20" />
                </div>
            </div>
        );
    }

    const { config, prices, change24h } = data;
    const currentPrice = prices[currency as keyof typeof prices];
    const isPositive = change24h >= 0;

    return (
        <Link href={`/coins/${config.symbol}`}>
            <div className={cn(
                "group relative overflow-hidden rounded-2xl border border-border/50 bg-secondary/20 p-6 shadow-sm backdrop-blur-sm transition-all duration-300 hover:bg-secondary/40 hover:scale-[1.02] hover:shadow-md cursor-pointer",
                flash && "animate-flash"
            )}>
                {/* Background Gradient Glow */}
                <div
                    className={cn(
                        "absolute -top-24 -right-24 h-48 w-48 rounded-full blur-3xl transition-opacity duration-500 opacity-0 group-hover:opacity-20",
                        isPositive ? "bg-emerald-500" : "bg-red-500"
                    )}
                />

                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                        {/* Icon: Use Url if available, else Fallback */}
                        {config.iconUrl ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={config.iconUrl} alt={config.name} className="h-12 w-12 rounded-full shadow-sm object-cover" />
                        ) : (
                            <div className={cn("flex h-12 w-12 items-center justify-center rounded-full bg-background/50 shadow-inner text-xl font-bold", isPositive ? "text-emerald-500" : "text-red-500")}>
                                {config.symbol[0]}
                            </div>
                        )}
                        <div>
                            <h3 className="text-lg font-bold tracking-tight text-foreground">{config.name}</h3>
                            <p className="text-sm font-medium text-muted-foreground">{config.symbol}</p>
                        </div>
                    </div>
                    {/* 24h Change Badge */}
                    <div
                        className={cn(
                            "flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium backdrop-blur-md border",
                            isPositive
                                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                                : "bg-red-500/10 text-red-500 border-red-500/20"
                        )}
                    >
                        {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        <span>{Math.abs(change24h).toFixed(2)}%</span>
                    </div>
                </div>

                <div className="mt-4">
                    <div className="text-3xl font-bold tracking-tight text-foreground">
                        {formatPrice(currentPrice)}
                    </div>
                    <div className="flex items-center justify-between mt-1">
                        <p className="text-sm text-muted-foreground">{t.dashboard.currentPrice || "Current Price"}</p>
                    </div>
                </div>
            </div>
        </Link>
    );
}
