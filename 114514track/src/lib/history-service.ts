import fs from 'fs/promises';
import path from 'path';
import { CryptoData } from './types';

// Define the shape of our stored history
export interface HistoryEntry {
    timestamp: number;
    prices: Record<string, number>; // coinId -> price
}

const DATA_DIR = path.join(process.cwd(), 'data');
const FILE_PATH = path.join(DATA_DIR, 'price_history.json');

// Ensure data directory exists
const ensureDir = async () => {
    try {
        await fs.access(DATA_DIR);
    } catch {
        await fs.mkdir(DATA_DIR, { recursive: true });
    }
};

export const HistoryService = {
    // Append new prices to history log
    logPrices: async (data: CryptoData[]) => {
        await ensureDir();

        let history: HistoryEntry[] = [];
        try {
            const fileContent = await fs.readFile(FILE_PATH, 'utf-8');
            history = JSON.parse(fileContent);
        } catch (error) {
            // File doesn't exist or empty, start new
            history = [];
        }

        // Create new entry
        const entry: HistoryEntry = {
            timestamp: Math.floor(Date.now() / 1000),
            prices: {},
        };

        data.forEach(coin => {
            entry.prices[coin.config.id] = coin.prices.usd;
        });

        // Check last entry to avoid duplicates (stuttering)
        if (history.length > 0) {
            const lastEntry = history[history.length - 1];
            // If less than 60 seconds have passed, check for price changes
            if (entry.timestamp - lastEntry.timestamp < 60) {
                const isSame = data.every(coin => {
                    const lastPrice = lastEntry.prices[coin.config.id];
                    const currentPrice = coin.prices.usd;
                    return lastPrice === currentPrice;
                });

                // If prices are exactly the same and time is short, skip logging
                // This prevents "stuttery" flat lines when SWR returns stale data
                if (isSame) {
                    return;
                }
            }
        }

        history.push(entry);

        // Optional: Prune old data (keep last 7 days? or 24h * 60 * 60 points?)
        // Let's keep last 7 days for now (approx 10k points if 1 min interval)
        const ONE_WEEK_SECONDS = 7 * 24 * 60 * 60;
        const cutoff = entry.timestamp - ONE_WEEK_SECONDS;
        history = history.filter(h => h.timestamp > cutoff);

        await fs.writeFile(FILE_PATH, JSON.stringify(history, null, 2));
    },

    // Get history for a specific coin
    getHistory: async (coinId: string) => {
        try {
            const fileContent = await fs.readFile(FILE_PATH, 'utf-8');
            const history: HistoryEntry[] = JSON.parse(fileContent);

            return history
                .filter(h => h.prices[coinId] !== undefined)
                .map(h => ({
                    time: h.timestamp,
                    value: h.prices[coinId]
                }));
        } catch (error) {
            return [];
        }
    }
};
