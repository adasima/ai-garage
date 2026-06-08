
import { useState, useEffect } from 'react';
import { AvailabilityStatus } from '@/lib/availability/dns';

export function useDomainAvailability(domain: string) {
    const [status, setStatus] = useState<AvailabilityStatus>('unknown');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        let mounted = true;

        async function check() {
            setLoading(true);
            try {
                const res = await fetch(`/api/check?domain=${domain}`);
                const data = await res.json();
                if (mounted && data.status) {
                    setStatus(data.status);
                }
            } catch (e) {
                console.error(e);
            } finally {
                if (mounted) setLoading(false);
            }
        }

        check();

        return () => { mounted = false; };
    }, [domain]);

    return { status, loading };
}
