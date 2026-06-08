"use client";

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { ChartContainer } from '@/components/ChartContainer';
import { CoinConfig } from '@/lib/types';
import { useTranslation } from '@/hooks/use-translation';

interface Props {
    coin: CoinConfig;
}

export function CoinDetailView({ coin }: Props) {
    const { t } = useTranslation();

    return (
        <div className="container py-8 space-y-8 animate-in slide-in-from-bottom-5 duration-500">
            {/* Header Card */}
            <div className="relative overflow-hidden rounded-3xl bg-secondary/10 border border-border/50 p-8 backdrop-blur-sm">
                {/* Ambient Glow */}
                <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-primary/20 blur-3xl opacity-50" />
                <div className="absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-accent/20 blur-3xl opacity-50" />

                <div className="relative z-10 flex items-center gap-6">
                    <Link href="/" className="group p-3 -ml-2 rounded-full hover:bg-background/80 transition-all border border-transparent hover:border-border/50">
                        <ArrowLeft className="w-6 h-6 text-muted-foreground group-hover:text-foreground transition-colors" />
                    </Link>

                    {/* Coin Icon */}
                    {coin.iconUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                            src={coin.iconUrl}
                            alt={coin.name}
                            className="w-16 h-16 rounded-full shadow-lg ring-4 ring-background/50 object-cover"
                        />
                    ) : (
                        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 shadow-inner text-2xl font-bold text-primary ring-4 ring-background/50">
                            {coin.symbol[0]}
                        </div>
                    )}

                    <div>
                        <h1 className="text-4xl font-bold tracking-tight text-foreground flex items-center gap-3">
                            {coin.name}
                        </h1>
                        <p className="text-xl font-medium text-muted-foreground">{coin.symbol}</p>
                    </div>
                </div>
            </div>

            {/* Main Chart Area */}
            <section className="space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-muted-foreground">{t.coin.priceChart}</h2>
                </div>

                <ChartContainer symbol={coin.symbol} coinId={coin.id} />

                <p className="text-xs text-muted-foreground text-center pt-2">
                    {t.coin.dataSource} {coin.source === 'coingecko' ? 'CoinGecko' : 'DexScreener'}.
                    {coin.source === 'dexscreener' && ` ${t.coin.estimated}`}
                </p>
            </section>
        </div>
    );
}
