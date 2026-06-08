import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(req: NextRequest) {
    const { searchParams } = new URL(req.url);
    const query = searchParams.get('q');

    if (!query) {
        return NextResponse.json({ results: [] });
    }

    try {
        // Parallel Usage: Search both if possible, or prioritize CoinGecko for general, DexScreener for specific pairs
        // For simplicity/robustness within free tier, let's try CoinGecko first as it's cleaner for "Coins".
        // If the user types a contract address, we might want DexScreener.

        const results: any[] = [];
        const isContractAddress = query.length > 30 && !query.includes(' ');

        // 1. DexScreener (Great for contract addresses or specific pairs)
        if (isContractAddress) {
            const dexUrl = `https://api.dexscreener.com/latest/dex/search?q=${query}`;
            try {
                const dexRes = await axios.get(dexUrl, { timeout: 3000 });
                if (dexRes.data.pairs) {
                    dexRes.data.pairs.slice(0, 5).forEach((pair: any) => {
                        results.push({
                            id: pair.baseToken.address, // Use address as ID for dex coins
                            symbol: pair.baseToken.symbol,
                            name: pair.baseToken.name,
                            apiId: pair.baseToken.address, // Important for our config
                            source: 'dexscreener',
                            thumb: pair.info?.imageUrl,
                            subtitle: `${pair.quoteToken.symbol} Pair on ${pair.dexId}`
                        });
                    });
                }
            } catch (e) {
                console.error("Dex search failed", e);
            }
        }

        // 2. CoinGecko (General Search)
        // Only run if not purely looking like a contract, or as supplement
        const cgUrl = `https://api.coingecko.com/api/v3/search?query=${query}`;
        try {
            const cgRes = await axios.get(cgUrl, { timeout: 3000 });
            if (cgRes.data.coins) {
                cgRes.data.coins.slice(0, 8).forEach((coin: any) => {
                    results.push({
                        id: coin.id,
                        symbol: coin.symbol,
                        name: coin.name,
                        apiId: coin.id,
                        source: 'coingecko',
                        thumb: coin.thumb,
                        subtitle: `Rank #${coin.market_cap_rank || '?'}`
                    });
                });
            }
        } catch (e) {
            console.error("CG search failed", e);
        }

        return NextResponse.json({ results });

    } catch (error) {
        console.error('Search error:', error);
        return NextResponse.json({ error: 'Search failed' }, { status: 500 });
    }
}
