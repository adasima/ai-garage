import { NextRequest, NextResponse } from 'next/server';
import { CryptoService } from '@/lib/crypto-service';
import { HistoryService } from '@/lib/history-service';
import axios from 'axios';

// Cache history for 5 minutes to avoid Rate Limiting
const CACHE_DURATION = 5 * 60 * 1000;
const cache: Record<string, { data: unknown[]; timestamp: number }> = {};

export async function GET(
    req: NextRequest,
    { params }: { params: Promise<{ symbol: string }> }
) {
    const { symbol } = await params;
    const config = CryptoService.getConfig().coins.find(
        (c) => c.symbol.toLowerCase() === symbol.toLowerCase() || c.id === symbol
    );

    if (!config) {
        return NextResponse.json({ error: 'Coin not found' }, { status: 404 });
    }

    // Force fetch latest prices to ensure log is updated at least once recently
    await CryptoService.getPrices();

    const now = Date.now();

    // Parse Range
    const { searchParams } = new URL(req.url);
    const range = searchParams.get('range') || '1d';
    const cacheKey = `${config.id}-${range}`;

    // Check Cache
    if (cache[cacheKey] && now - cache[cacheKey].timestamp < CACHE_DURATION) {
        // console.log(`Serving ${cacheKey} from cache`);
        return NextResponse.json(cache[cacheKey].data);
    }

    try {
        let chartData: { time: number; value: number; isEstimated?: boolean }[] = [];

        // 1. Get Local History from CSV (High Res, Real Data)
        // We filter this later based on range if needed, but usually we just want all of it 
        // that falls within the requested range window.
        const localHistory = await HistoryService.getHistory(config.id);

        if (config.source === 'coingecko') {
            // Map range to days
            const daysMap: Record<string, string> = {
                '1h': '1', // CG min is 1 day (5min intervals). We just slice it later? Or days=1 is fine.
                '1d': '1',
                '3d': '3',
                '1w': '7',
                '1m': '30',
                '6m': '180',
                '1y': '365'
            };
            const days = daysMap[range] || '1';

            try {
                const url = `https://api.coingecko.com/api/v3/coins/${config.apiId}/market_chart?vs_currency=usd&days=${days}`;
                const res = await axios.get(url, { timeout: 5000 });
                chartData = res.data.prices.map((p: [number, number]) => ({
                    time: p[0] / 1000,
                    value: p[1],
                    isEstimated: false,
                }));
            } catch (e) {
                console.warn("CoinGecko fetch failed, falling back to local only");
            }

        } else if (config.source === 'dexscreener') {
            // DexScreener Strategy (Honest + Smart 24h Interpolation)

            // Define cutoff based on range
            const timeMap: Record<string, number> = {
                '1h': 3600,
                '1d': 86400,
                '3d': 259200,
                '1w': 604800,
                '1m': 2592000,
                '6m': 15552000,
                '1y': 31536000
            };
            const secondsBack = timeMap[range] || 86400;
            const cutoffTime = (now / 1000) - secondsBack;

            // 1. Use Local History FIRST
            // Filter local history for the requested range
            chartData = localHistory.filter(d => d.time >= cutoffTime).map(d => ({ ...d, isEstimated: false }));

            // 2. If range is within 24h, and we have sparse data, we can use DexScreener stats
            // to generate "Estimated" points (Yellow line) to fill context.
            // ONLY do this if we are looking at short term (<= 3d) to improve UX.
            // For longer terms (>3d), if we don't have data, we show nothing (Honest).
            if (secondsBack <= 259200) { // <= 3 days
                const prices = await CryptoService.getPrices();
                const coinData = prices.find(c => c.config.id === config.id);

                if (coinData) {
                    const currentP = coinData.prices.usd;
                    const changes = coinData.priceChange || { h24: 0, h6: 0, h1: 0, m5: 0 };

                    // Reconstruct likely past points (Estimated)
                    const p24h = (currentP / (1 + (changes.h24 / 100))) || currentP;
                    const p6h = (currentP / (1 + (changes.h6 / 100))) || currentP;
                    const p1h = (currentP / (1 + (changes.h1 / 100))) || currentP;
                    const p5m = (currentP / (1 + (changes.m5 / 100))) || currentP;
                    const nowSec = Math.floor(now / 1000);

                    const estPoints = [
                        { time: nowSec - 86400, value: p24h, isEstimated: true },
                        { time: nowSec - 21600, value: p6h, isEstimated: true },
                        { time: nowSec - 3600, value: p1h, isEstimated: true },
                        { time: nowSec - 300, value: p5m, isEstimated: true },
                    ];

                    // Filter Est points that are older than our Local History (if any)
                    // If we have local history starting at T-10h, we can keep T-24h est point.
                    // But if local history covers T-24h, we drop the est point.
                    // Simple logic: Add Est points ONLY if they are within range AND we don't have close local data?
                    // Simpler: Just add them, sort, and let the chart handle it? 
                    // Better: Add them if they are OLDER than the oldest local data point.

                    const oldestLocal = chartData.length > 0 ? chartData[0].time : Infinity;

                    estPoints.forEach(pt => {
                        if (pt.time >= cutoffTime && pt.time < oldestLocal) {
                            chartData.push(pt);
                        }
                    });

                    // Explicitly add Current Price as estimated if we have NO local data at all?
                    // No, `getPrices` forced a log update recently, so valid local data "now" should exist via HistoryService log, or soon.
                    // Actually, force fetch above `await CryptoService.getPrices()` triggers `HistoryService.logPrices`.
                    // So we SHOULD have at least one point (Now).
                }
            }
        }

        // Sort & Dedup
        chartData.sort((a, b) => a.time - b.time);

        // Remove exact duplicates
        chartData = chartData.filter((item, index, self) =>
            index === self.findIndex((t) => (t.time === item.time))
        );

        // SMOOTHING (Optional, maybe skip for 1h range to keep detail?)
        // Applying smoothing clears up noise
        if (chartData.length > 2) {
            const smoothed = [chartData[0]];
            for (let i = 1; i < chartData.length; i++) {
                if (chartData[i].value !== chartData[i - 1].value || i === chartData.length - 1) {
                    smoothed.push(chartData[i]);
                }
            }
            chartData = smoothed;
        }

        cache[cacheKey] = { data: chartData, timestamp: now };
        return NextResponse.json(chartData);
    } catch (error) {
        console.error('History fetch error:', error);
        return NextResponse.json({ error: 'Failed to fetch history' }, { status: 500 });
    }
}
