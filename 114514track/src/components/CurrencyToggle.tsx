"use client";

import { cn } from "@/lib/utils";
import { create } from "zustand";
import { useTranslation } from "@/hooks/use-translation";

// Simple global state for currency
interface CurrencyState {
    currency: "usd" | "jpy" | "sol";
    setCurrency: (c: "usd" | "jpy" | "sol") => void;
    symbol: string;
    formatPrice: (price: number | string) => string;
}

export const useCurrencyStore = create<CurrencyState>((set, get) => ({
    currency: "jpy", // Default JPY
    symbol: "¥",
    setCurrency: (c) =>
        set(() => ({
            currency: c,
            symbol: c === "usd" ? "$" : c === "jpy" ? "¥" : "SOL",
        })),
    formatPrice: (price) => {
        const val = typeof price === 'string' ? parseFloat(price) : price;
        if (isNaN(val)) return '';
        const { currency } = get();

        if (currency === 'sol') {
            return `◎ ${val.toLocaleString(undefined, { maximumFractionDigits: 6 })}`;
        }

        const isSmall = Math.abs(val) >= 1 && Math.abs(val) < 100;

        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: currency.toUpperCase(),
            minimumFractionDigits: val < 1 ? 4 : (isSmall ? 2 : undefined),
            maximumFractionDigits: val < 1 ? 6 : (isSmall ? 2 : undefined),
        }).format(val);
    }
}));

export function CurrencyToggle() {
    const { currency, setCurrency } = useCurrencyStore();
    const { t } = useTranslation();

    return (
        <div className="flex items-center gap-3 bg-secondary/20 p-1.5 rounded-lg border border-border/50 backdrop-blur-sm">
            <span className="text-xs font-medium text-muted-foreground px-2">{t.common.currency}</span>
            <div className="flex">
                {(["jpy", "usd", "sol"] as const).map((c) => (
                    <button
                        key={c}
                        onClick={() => setCurrency(c)}
                        className={cn(
                            "px-3 py-1 rounded-md text-sm font-medium transition-all duration-200 uppercase",
                            currency === c
                                ? "bg-background text-foreground shadow-sm scale-105"
                                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                        )}
                    >
                        {c}
                    </button>
                ))}
            </div>
        </div>
    );
}
