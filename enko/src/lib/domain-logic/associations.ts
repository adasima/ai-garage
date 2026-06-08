
// Association Dictionary for Omoshiro.dom
// Maps keywords to related concepts, memes, or funny terms.

export const ASSOCIATIONS: Record<string, string[]> = {
    // Dirty / Funny
    'unko': ['poop', 'shit', 'toilet', 'flush', 'benjo', 'kuso', 'wc', 'digest', 'nagase', 'feces', 'dung', 'manure'],
    // Japanese Direct Mapping (toRomaji handles some, but direct kana mapping helps context)
    // Actually generator uses normalized (romaji), but we can map romaji -> english here.
    // user said "日本語で入れたら英語にして" -> "unkasu" -> "scum", "trash"
    'unkasu': ['garbage', 'trash', 'debris', 'kuzu', 'scrap', 'scum', 'dregs'],
    'chinchin': ['wiener', 'sausage', 'rocket', 'joystick', 'tower', 'pemis', 'dick'],
    'oppai': ['milk', 'mountain', 'melon', 'papaya', 'twinpeaks', 'boobs', 'breast'],

    // Tech / Memes
    'bug': ['feature', 'fixme', 'blame', 'oops', 'kafka'],
    'deploy': ['friday', 'yolo', 'pray', 'rollback'],
    'javascript': ['undefined', 'nan', 'wat', 'java', 'script'],
    'rust': ['crab', 'rewrite', 'safe', 'ferris', 'oxidize'],

    // Culture / Internet
    'w': ['kusa', 'grass', 'lol', 'lmao', 'warota'],
    'kusa': ['grass', 'forest', 'jungle', 'amazon'],
    'neko': ['cat', 'nyan', 'meow', 'kitty', 'paws'],
    'inu': ['dog', 'wan', 'bowwow', 'puppy', 'doge'],
    'doge': ['shiba', 'coin', 'moon', 'wow'],

    // General Positive
    'kami': ['god', 'zeus', 'creator', 'admin', 'sudo'],
    'tensai': ['genius', 'brain', 'iq200', 'einstein'],

    // Common Phrases
    'otsu': ['cheers', 'beer', 'rest', 'home'],
    'test': ['ignore', 'temp', 'sandbox', 'beta', 'alpha']
};

export function getAssociations(input: string): string[] {
    const normalized = input.toLowerCase().trim();
    return ASSOCIATIONS[normalized] || [];
}
