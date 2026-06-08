
// Common TLDs useful for domain hacks
const HACK_TLDS = [
    'ac', 'ad', 'ag', 'ai', 'al', 'am', 'as', 'at', 'be', 'bg', 'bi', 'bs', 'bz',
    'ca', 'cc', 'cd', 'ch', 'ci', 'cl', 'cm', 'co', 'cr', 'cu', 'cx',
    'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'ee', 'eg', 'es', 'eu',
    'fi', 'fm', 'fo', 'fr', 'ga', 'gd', 'ge', 'gg', 'gl', 'gm', 'gp', 'gr', 'gs', 'gt', 'gy',
    'hk', 'hm', 'hn', 'hr', 'ht', 'hu', 'ie', 'im', 'in', 'io', 'iq', 'is', 'it',
    'je', 'jo', 'jp', 'kg', 'ki', 'km', 'kn', 'kr', 'ky', 'kz',
    'la', 'lc', 'li', 'lk', 'lu', 'lv', 'ly',
    'ma', 'mc', 'md', 'me', 'mg', 'mk', 'ml', 'mn', 'mo', 'mp', 'ms', 'mu', 'mw', 'mx', 'my',
    'na', 'nc', 'ne', 'nf', 'ng', 'nl', 'no', 'nr', 'nu',
    'om', 'pa', 'pe', 'ph', 'pk', 'pl', 'pn', 'pr', 'ps', 'pt', 'pw',
    're', 'ro', 'rs', 'ru', 'rw',
    'sa', 'sc', 'se', 'sg', 'sh', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'st', 'su', 'sv', 'sx', 'sy',
    'tc', 'td', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 'tr', 'tt', 'tv', 'tw',
    'ug', 'uk', 'us', 'uy', 'uz', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'ws',
    'yt', 'za', 'zm'
];

export type WordHackResult = {
    original: string;
    domain: string; // "foc.us"
    prefix: string; // "foc"
    tld: string;    // "us"
};

export function generateWordHacks(input: string): WordHackResult[] {
    const normalized = input.toLowerCase().replace(/[^a-z]/g, '');
    const results: WordHackResult[] = [];

    // 1. Direct TLD match
    for (const tld of HACK_TLDS) {
        if (normalized.endsWith(tld) && normalized.length > tld.length) {
            const prefix = normalized.slice(0, -tld.length);
            results.push({
                original: input,
                domain: `${prefix}.${tld}`,
                prefix: prefix,
                tld: tld
            });
        }
    }

    // 2. Phonetic TLD match
    // Map of TLD -> [phonetic equivalents]
    const PHONETIC_TLDS: Record<string, string[]> = {
        'co': ['ko', 'ka', 'ca'],
        'io': ['yo', 'eo'],
        'xyz': ['kush'], // hypothetical
        'biz': ['bis', 'vis'],
        'me': ['mi', 'mu'],
        'be': ['bi', 've'],
        'sh': ['ss', 's'], // fish -> fi.sh
        'ch': ['tch'],
        'to': ['t', 'tu'],
        'in': ['ing'],
        'it': ['et'],
        'is': ['iz', 'es'],
        'us': ['as'],
        // Add more as needed
    };

    for (const [tld, suffixes] of Object.entries(PHONETIC_TLDS)) {
        if (!HACK_TLDS.includes(tld)) continue;

        for (const suffix of suffixes) {
            if (normalized.endsWith(suffix) && normalized.length > suffix.length) {
                const prefix = normalized.slice(0, -suffix.length);
                results.push({
                    original: input,
                    domain: `${prefix}.${tld}`,
                    prefix: prefix,
                    tld: tld
                });
            }
        }
    }

    // Also try "subdomain hacks" like "play.station" ?
    // For MVP, stick to TLD hacks. 
    // Maybe simple splitting: delicious -> del.icio.us is hard without dict.
    // Let's stick to simple suffix hacks for now.

    return results;
}
