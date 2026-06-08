
import { GoroawaseResult } from './goroawase';
import { WordHackResult } from './wordhacks';

export type VoltageResult = {
    level: 1 | 2 | 3; // 1: Mild shake, 2: Strong shake, 3: EXPLOSION
    advantages: string[];
};

const FAMOUS_NUMBERS = [
    '29', '1122', '4649', '39', '1107', '8888', '777', '5963', '3150', '2525'
];

export function calculateVoltage(
    domainName: string,
    type: 'goroawase' | 'hack',
    details?: GoroawaseResult | WordHackResult
): VoltageResult {
    let score = 0;
    const advantages: string[] = [];

    // Base score
    score += 1;

    // Length Bonus
    const length = domainName.length;
    if (length <= 5) {
        score += 1;
        advantages.push('短さは正義 (Short)');
    }

    // TLD Bonus
    if (domainName.endsWith('.jp')) {
        score += 1;
        advantages.push('信頼のJPブランド');
    } else if (domainName.endsWith('.com')) {
        score += 1;
        advantages.push('王道の.com');
    } else if (domainName.endsWith('.io') || domainName.endsWith('.ai') || domainName.endsWith('.dev')) {
        advantages.push('Dev/Tech御用達');
    }

    // Type Specific Bonus
    if (type === 'goroawase' && details) {
        const goro = details as GoroawaseResult;
        if (FAMOUS_NUMBERS.includes(goro.converted)) {
            score += 2; // Huge bonus
            advantages.push('伝説の語呂合わせ');
        } else if (goro.converted.length <= 2) {
            score += 1;
        }

        // Check if readings are simple
        if (goro.readings.every(r => r.length <= 2)) {
            advantages.push('リズムが良い');
        }
    }

    if (type === 'hack' && details) {
        const hack = details as WordHackResult;
        advantages.push('芸術的ハック');
        if (hack.original.length <= 4) {
            score += 1;
        }
    }

    // Cap Level
    let level: 1 | 2 | 3 = 1;
    if (score >= 4) level = 3;
    else if (score >= 3) level = 2;
    else level = 1;

    // Fallback advantage if empty
    if (advantages.length === 0) {
        advantages.push('可能性の獣');
    }

    return { level, advantages: advantages.slice(0, 3) };
}
