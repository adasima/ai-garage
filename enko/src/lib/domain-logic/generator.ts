import { toRomaji } from 'wanakana';
import { generateGoroawase, GoroawaseResult } from './goroawase';
import { generateWordHacks, WordHackResult } from './wordhacks';
import { calculateVoltage, VoltageResult } from './voltage';
import { getAssociations } from './associations';

export type DomainResult = {
    id: string; // Unique ID for keying
    domain: string;
    type: 'goroawase' | 'hack';
    voltage: VoltageResult;
    metadata: {
        origin: string;
        goroawase?: GoroawaseResult;
        hack?: WordHackResult;
    };
    status: 'unknown' | 'available' | 'taken'; // Initial status
};

export function generateDomains(input: string): DomainResult[] {
    const results: DomainResult[] = [];

    // Convert Japanese input to Romaji (e.g., "にく" -> "niku")
    // If input is already English, it stays largely the same (wanakana handles it)
    const normalized = toRomaji(input);

    // 0. Associations (Memes & Related Topics)
    const relatedTerms = getAssociations(normalized);
    for (const term of relatedTerms) {
        // Generate hacks for the related term
        const termHacks = generateWordHacks(term);
        for (const h of termHacks) {
            const voltage = calculateVoltage(h.domain, 'hack', h);
            results.push({
                id: `assoc-${term}-${h.domain}`,
                domain: h.domain,
                type: 'hack',
                voltage: {
                    level: Math.random() > 0.5 ? 2 : 1, // Random excitement for meme
                    advantages: [`関連ワード: ${term} (Related)`, ...voltage.advantages]
                },
                metadata: {
                    origin: input,
                    hack: { ...h, original: term } // Hack comes from related term
                },
                status: 'unknown'
            });
        }

        // Also add direct match for related term
        const tld = '.com'; // Stick to .com for simplicity or iterate
        const domainName = `${term}${tld}`;
        results.push({
            id: `assoc-direct-${domainName}`,
            domain: domainName,
            type: 'hack',
            voltage: {
                level: 2,
                advantages: [`関連ワード: ${term}`, '連想ゲーム (Assoc.)']
            },
            metadata: { origin: input, hack: { original: term, domain: domainName, prefix: term, tld: 'com' } },
            status: 'unknown'
        });
    }

    // 1. Goroawase (Disabled by user request - too abstract/boring)
    /*
    const goros = generateGoroawase(normalized);
    for (const g of goros) {
        // ... (logic removed) ...
    }
    */

    // 2. Direct Match (Simple Connect)
    // Always suggest [word].jp, [word].com, [word].net if reasonable length
    // User requested "zura zura" (many results)
    const directTlds = [
        '.jp', '.com', '.net', '.io', '.co', '.xyz',
        '.ai', '.app', '.dev', '.gg', '.me', '.org',
        '.tech', '.site', '.online', '.store', '.shop',
        '.fun', '.lol', '.world', '.ninja', '.pro'
    ];
    for (const tld of directTlds) {
        const domainName = `${normalized}${tld}`;
        const voltage = calculateVoltage(domainName, 'hack', { original: input, domain: domainName, prefix: normalized, tld: tld.replace('.', '') });
        results.push({
            id: `direct-${domainName}`,
            domain: domainName,
            type: 'hack', // Treat as hack or new 'direct' type? 'hack' is fine for UI
            voltage: {
                level: 3, // Boost direct matches as "Impactful"
                advantages: ['シンプルイズベスト (Simple)', '覚えやすい (Memorable)', ...voltage.advantages]
            },
            metadata: {
                origin: input,
                hack: {
                    original: input,
                    domain: domainName,
                    prefix: normalized,
                    tld: tld.replace('.', '')
                }
            },
            status: 'unknown'
        });
    }

    // 3. Word Hacks
    const hacks = generateWordHacks(normalized);
    for (const h of hacks) {
        const voltage = calculateVoltage(h.domain, 'hack', h);
        results.push({
            id: `hack-${h.domain}-${Math.random().toString(36).substr(2, 9)}`,
            domain: h.domain,
            type: 'hack',
            voltage,
            metadata: {
                origin: input,
                hack: h
            },
            status: 'unknown'
        });
    }

    // Sort by Voltage Level descending, then length ascending
    return results.sort((a, b) => {
        if (b.voltage.level !== a.voltage.level) {
            return b.voltage.level - a.voltage.level;
        }
        return a.domain.length - b.domain.length;
    });
}
