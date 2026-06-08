
import { generateDomains } from './src/lib/domain-logic/generator';
import { toRomaji } from 'wanakana';

const inputs = [
    'にく',        // Hiragana
    'サウナ',      // Katakana
    'Tokyo',       // English
    '焼肉',        // Kanji (wanakana might not handle Kanji -> Reading automatically)
    '123',         // Numbers
    'mixedにく'    // Mixed
];

console.log("=== Debugging Generator Logic with Wanakana ===");

inputs.forEach(input => {
    console.log(`\nInput: "${input}"`);

    // 1. Test Wanakana directly first
    const romaji = toRomaji(input);
    console.log(` -> Romaji: "${romaji}"`);

    // 2. Test Generator
    try {
        const results = generateDomains(input);
        console.log(` -> Generated: ${results.length} domains`);
        if (results.length > 0) {
            console.log(`    Top result: ${results[0].domain} (${results[0].type})`);
        } else {
            console.log(`    [!] No results generated.`);
        }
    } catch (e) {
        console.error(` -> CRASHED:`, e);
    }
});
