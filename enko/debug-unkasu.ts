
import { generateDomains } from './src/lib/domain-logic/generator';
import { toRomaji } from 'wanakana';

const inputs = ['うんかす', 'unkasu', 'unko', 'w', 'rust'];

console.log("=== Debugging 'unkasu' ===");
inputs.forEach(input => {
    console.log(`\nInput: "${input}"`);
    const romaji = toRomaji(input);
    console.log(` -> Romaji: "${romaji}"`);
    try {
        const results = generateDomains(input);
        console.log(` -> Generated: ${results.length} results`);
        results.forEach(r => console.log(`   - ${r.domain} (${r.type}) Voltage:${r.voltage.level}`));
    } catch (e) {
        console.error(e);
    }
});
