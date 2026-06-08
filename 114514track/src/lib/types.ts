export type CoinSource = 'coingecko' | 'dexscreener';

export interface CoinConfig {
    id: string;          // Internal unique ID (e.g., 'bitcoin', 'sol-114514')
    symbol: string;      // Display symbol (e.g., 'BTC', '114514')
    name: string;        // Full name
    source: CoinSource;  // Where to fetch data from
    apiId: string;       // CoinGecko ID or Contract Address
    isEnabled: boolean;
    iconUrl?: string;    // Optional icon URL
}

export interface MarketData {
    price: number;
    change24h: number;
    priceChange?: {
        m5: number;
        h1: number;
        h6: number;
        h24: number;
    };
    lastUpdated: number;
}

export interface CryptoData extends MarketData {
    config: CoinConfig;
    prices: {
        usd: number;
        jpy: number;
        sol: number;
    };
}

// Global configuration state
export interface SystemConfig {
    coins: CoinConfig[];
    globalEnabled: boolean;
    refreshInterval: number; // in seconds
}
