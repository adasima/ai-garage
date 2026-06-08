
import dns from 'dns';
import { promisify } from 'util';

const resolve = promisify(dns.resolve);

export type AvailabilityStatus = 'available' | 'taken' | 'unknown';

/**
 * Checks if a domain resolves via DNS.
 * If it resolves, it is definitely TAKEN.
 * If it doesn't resolve, it is LIKELY AVAILABLE (but not guaranteed).
 */
export async function checkDnsAvailability(domain: string): Promise<AvailabilityStatus> {
    try {
        await resolve(domain);
        return 'taken';
    } catch (error: any) {
        if (error.code === 'ENOTFOUND') {
            return 'available'; // Likely available
        }
        // Other errors (timeout, etc) -> unknown
        console.error(`DNS check error for ${domain}:`, error);
        return 'unknown';
    }
}
