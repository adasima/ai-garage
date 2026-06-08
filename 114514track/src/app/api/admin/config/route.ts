import { NextRequest, NextResponse } from 'next/server';
import { CryptoService } from '@/lib/crypto-service';
import { SystemConfig } from '@/lib/types';

export const dynamic = 'force-dynamic';

export async function GET() {
    return NextResponse.json(CryptoService.getConfig());
}

export async function POST(req: NextRequest) {
    try {
        const body: Partial<SystemConfig> = await req.json();

        // Very basic validation could go here
        if (body.refreshInterval && body.refreshInterval < 5) {
            return NextResponse.json({ error: 'Refresh interval too low' }, { status: 400 });
        }

        CryptoService.updateConfig(body);
        return NextResponse.json(CryptoService.getConfig());
    } catch (error) {
        return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
    }
}
