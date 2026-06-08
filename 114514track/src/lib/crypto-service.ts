import axios from 'axios';
import { CoinConfig, CryptoData, MarketData, SystemConfig } from './types';
import { HistoryService } from './history-service';

// Default initial configuration
const DEFAULT_COINS: CoinConfig[] = [
    { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', source: 'coingecko', apiId: 'bitcoin', isEnabled: true, iconUrl: 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png' },
    { id: 'dogecoin', symbol: 'DOGE', name: 'Dogecoin', source: 'coingecko', apiId: 'dogecoin', isEnabled: true, iconUrl: 'https://assets.coingecko.com/coins/images/5/large/dogecoin.png' },
    { id: 'monacoin', symbol: 'MONA', name: 'MonaCoin', source: 'coingecko', apiId: 'monacoin', isEnabled: true, iconUrl: 'https://cryptologos.cc/logos/monacoin-mona-logo.png' },
    { id: 'solana', symbol: 'SOL', name: 'Solana', source: 'coingecko', apiId: 'solana', isEnabled: true, iconUrl: 'https://assets.coingecko.com/coins/images/4128/large/solana.png' },
    { id: '114514', symbol: '114514', name: '114514', source: 'dexscreener', apiId: 'AGdGTQa8iRnSx4fQJehWo4Xwbh1bzTazs55R6Jwupump', isEnabled: true, iconUrl: 'https://cdn.dexscreener.com/cms/images/a9f282ee6fbc1ca5066e19bef80a0cf9f4cae1024dd836825b70e7719c8f56a3?width=128&height=128&quality=90' },
];

let systemConfig: SystemConfig = {
    coins: DEFAULT_COINS,
    globalEnabled: true,
    refreshInterval: 60,
};

// In-memory cache
const cache: Record<string, MarketData> = {};
let lastFetchTime = 0;
let fetchPromise: Promise<void> | null = null;
let solPrice = 0; // Cache SOL price specifically for conversion
let jpyRate = 150; // Fallback JPY rate

export const CryptoService = {
    // Get current configuration
    getConfig: () => systemConfig,

    // Update configuration (Runtime)
    updateConfig: (newConfig: Partial<SystemConfig>) => {
        systemConfig = { ...systemConfig, ...newConfig };
    },

    // Main entry point: Get all prices
    getPrices: async (): Promise<CryptoData[]> => {
        if (!systemConfig.globalEnabled) {
            throw new Error('Service is currently paused by administrator.');
        }

        const now = Date.now();
        const isStale = now - lastFetchTime > systemConfig.refreshInterval * 1000;

        // Coalescing: If a fetch is running, return that promise. If stale, start new.
        if (isStale && !fetchPromise) {
            // SWR: Launch background fetch, do NOT await it if we have cache
            fetchPromise = fetchAllPrices().catch(e => console.error("Background fetch failed", e)).finally(() => {
                fetchPromise = null;
            });
        }

        // COLD START CHECK: Only wait if we have absolutely nothing to show
        const hasCache = Object.keys(cache).length > 0;
        if (!hasCache && fetchPromise) {
            await fetchPromise;
        }

        // Transform cache to CryptoData with conversions
        return systemConfig.coins
            .filter((c) => c.isEnabled)
            .map((coin) => {
                const data = cache[coin.id] || { price: 0, change24h: 0, lastUpdated: 0 };
                return {
                    config: coin,
                    ...data,
                    prices: {
                        usd: data.price,
                        jpy: data.price * jpyRate,
                        sol: solPrice > 0 ? data.price / solPrice : 0,
                    },
                };
            });
    },
};

// Internal fetch logic
async function fetchAllPrices() {
    try {
        const coins = systemConfig.coins.filter((c) => c.isEnabled);

        // Group by source
        const coingeckoCoins = coins.filter((c) => c.source === 'coingecko');
        const dexCoins = coins.filter((c) => c.source === 'dexscreener');

        // 1. Fetch Exchange Rates (USD/JPY) if needed (Mock for now or fetch from separate API)
        // For simplicity, we assume USD base and fixed JPY rate or fetch JPY rate from CG

        // 2. Fetch CoinGecko
        if (coingeckoCoins.length > 0) {
            const ids = coingeckoCoins.map((c) => c.apiId).join(',');
            const url = `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd,jpy&include_24hr_change=true`;

            const res = await axios.get(url, { timeout: 5000 });

            // Update SOL price for conversion if present
            if (res.data.solana) {
                solPrice = res.data.solana.usd;
            }

            // Update global JPY rate from Bitcoin or Solana data if available (heuristic)
            if (res.data.bitcoin && res.data.bitcoin.jpy && res.data.bitcoin.usd) {
                jpyRate = res.data.bitcoin.jpy / res.data.bitcoin.usd;
            }

            coingeckoCoins.forEach((c) => {
                if (res.data[c.apiId]) {
                    cache[c.id] = {
                        price: res.data[c.apiId].usd,
                        change24h: res.data[c.apiId].usd_24h_change || 0,
                        lastUpdated: Date.now(),
                    };
                }
            });
        }

        // 3. Fetch DexScreener (Parallel)
        if (dexCoins.length > 0) {
            // DexScreener allows fetching by token address: https://api.dexscreener.com/latest/dex/tokens/:tokenAddreses
            // Max 30 addresses per request
            const addresses = dexCoins.map(c => c.apiId).join(',');
            const url = `https://api.dexscreener.com/latest/dex/tokens/${addresses}`;

            try {
                const res = await axios.get(url, { timeout: 5000 });
                const pairs = res.data.pairs; // DexScreener returns pairs

                dexCoins.forEach(c => {
                    // Find the best pair (usually highest liquidity, or just the first matching one)
                    // We match by baseToken address roughly
                    const pair = pairs?.find((p: { baseToken: { address: string }, priceUsd: string, priceChange: { m5: number; h1: number; h6: number; h24: number }, info?: { imageUrl?: string } }) => p.baseToken.address.toLowerCase() === c.apiId.toLowerCase());
                    if (pair) {
                        // Dynamic Icon Update: If provided by DexScreener
                        if (pair.info?.imageUrl && !c.iconUrl) {
                            c.iconUrl = pair.info.imageUrl;
                        }

                        cache[c.id] = {
                            price: parseFloat(pair.priceUsd),
                            change24h: pair.priceChange.h24,
                            priceChange: {
                                m5: pair.priceChange.m5 || 0,
                                h1: pair.priceChange.h1 || 0,
                                h6: pair.priceChange.h6 || 0,
                                h24: pair.priceChange.h24 || 0,
                            },
                            lastUpdated: Date.now()
                        };
                    }
                });
            } catch (e) {
                console.error("DexScreener API Error:", e);
            }
        }

        // ... existing fetching logic ...

        lastFetchTime = Date.now();

        // LOGGING: Save current state to history file
        // Reconstruct CryptoData[] style list from cache to pass to logger
        const liveData: CryptoData[] = coins.map(c => ({
            config: c,
            price: cache[c.id]?.price || 0,
            change24h: cache[c.id]?.change24h || 0,
            priceChange: cache[c.id]?.priceChange,
            lastUpdated: cache[c.id]?.lastUpdated || 0,
            prices: {
                usd: cache[c.id]?.price || 0,
                // These rates might be slight approximations if JPY/SOL rate changed in this tick
                jpy: (cache[c.id]?.price || 0) * jpyRate,
                sol: solPrice > 0 ? (cache[c.id]?.price || 0) / solPrice : 0,
            }
        }));

        // Fire and forget logging (don't await to block UI response)
        HistoryService.logPrices(liveData).catch(err => console.error("Logging failed:", err));

    } catch (error: any) {
        console.error('Failed to fetch prices:', error.message || error);
        if (axios.isAxiosError(error)) {
            console.error('Axios Error Details:', {
                status: error.response?.status,
                statusText: error.response?.statusText,
                url: error.config?.url
            });
        }
        // On error, we keep stale cache (resilience)
    }
}
