import { Metadata } from 'next';
import { CryptoService } from '@/lib/crypto-service';
import { notFound } from 'next/navigation';
import { CoinDetailView } from '@/components/CoinDetailView';

// Force dynamic rendering for real-time prices on initial load
export const dynamic = 'force-dynamic';

interface Props {
    params: Promise<{ symbol: string }>;
}

// Generate Metadata for SEO/OGP
export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const { symbol } = await params;
    const coins = CryptoService.getConfig().coins;
    const coin = coins.find((c) => c.symbol.toUpperCase() === symbol.toUpperCase() || c.id === symbol);

    if (!coin) {
        return { title: 'Coin Not Found' };
    }

    return {
        title: `${coin.name} (${coin.symbol}) Price Chart | CryptoDash`,
        description: `Track real-time ${coin.name} prices, charts, and market data.`,
        openGraph: {
            title: `${coin.symbol} Price Analysis`,
            description: `Live chart for ${coin.name}`,
        },
    };
}

export default async function CoinPage({ params }: Props) {
    const { symbol } = await params;
    const coins = CryptoService.getConfig().coins;
    const coin = coins.find((c) => c.symbol.toUpperCase() === symbol.toUpperCase() || c.id === symbol);

    if (!coin) {
        return notFound();
    }

    return <CoinDetailView coin={coin} />;
}
