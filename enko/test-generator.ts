
import { generateDomains } from './src/lib/domain-logic/generator';

const testInputs = [
    'niku',
    'konnichiwa',
    'a',
    'superlongstringthatmightcauseperformanceissuesifrecursionisbad',
    '123',
    '日本語' // Kanji/Hiragana might be stripped but check
];

console.log("Starting Test...");

testInputs.forEach(input => {
    const start = performance.now();
    try {
        const res = generateDomains(input);
        const end = performance.now();
        console.log(`Input: "${input}" | Results: ${res.length} | Time: ${(end - start).toFixed(2)}ms`);
    } catch (e) {
        console.error(`Input: "${input}" | CRASHED:`, e);
    }
});

console.log("Test Complete.");
