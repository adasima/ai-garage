
import { NextResponse } from 'next/server';
import { checkDnsAvailability } from '@/lib/availability/dns';
import { supabase } from '@/lib/supabase/client';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const domain = searchParams.get('domain');

    if (!domain) {
        return NextResponse.json({ error: 'Domain is required' }, { status: 400 });
    }

    try {
        // 1. Check Cache (Supabase)
        if (supabase) {
            const { data: cached } = await supabase
                .from('domains')
                .select('*')
                .eq('name', domain)
                .single();

            if (cached) {
                // Check if cache is fresh (e.g., < 24 hours)
                const checkedAt = new Date(cached.last_checked_at).getTime();
                const now = Date.now();
                const diffHours = (now - checkedAt) / (1000 * 60 * 60);

                if (diffHours < 24) {
                    return NextResponse.json({
                        domain,
                        status: cached.status,
                        cached: true,
                        favorites: cached.favorites_count || 0
                    });
                }
            }
        }

        // 2. Perform DNS Check
        const dnsStatus = await checkDnsAvailability(domain);

        // 3. Update/Insert Cache (background-ish, but we await to be safe)
        // 3. Update/Insert Cache (background-ish, but we await to be safe)
        if (supabase) {
            // Upsert to domains table
            await supabase.from('domains').upsert({
                name: domain,
                status: dnsStatus,
                last_checked_at: new Date().toISOString()
            }, { onConflict: 'name' });
        }

        return NextResponse.json({
            domain,
            status: dnsStatus,
            cached: false
        });

    } catch (error) {
        console.error('Check API Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
