import { NextResponse } from 'next/server';
import { CryptoService } from '@/lib/crypto-service';

export const dynamic = 'force-dynamic'; // Prevent Next.js from caching this route statically at build time

export async function GET() {
    try {
        const data = await CryptoService.getPrices();
        return NextResponse.json(data);
    } catch (error: any) {
        return NextResponse.json(
            { error: error.message || 'Internal Server Error' },
            { status: 503 }
        );
    }
}
