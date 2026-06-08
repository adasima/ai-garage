
// Basic Goroawase Mappings
const PHONETIC_MAP: Record<string, string[]> = {
  // 0
  'o': ['0'], 'ze': ['0'], 'ro': ['0', '6'], 're': ['0'], 'n': ['0'], 'wa': ['0', '8'], 'ma': ['0'], 'wo': ['0'], 'po': ['0'], 'bo': ['0'],
  // 1
  'i': ['1', '5'], 'ichi': ['1'], 'hi': ['1'], 'wan': ['1'], 'a': ['1'], 'un': ['1'], 'e': ['1'], 'le': ['1'],
  // 2
  'ni': ['2'], 'fu': ['2'], 'tsu': ['2'], 'ji': ['2'], 'tu': ['2'], 'to': ['2', '10'], 'z': ['2'],
  // 3
  'san': ['3'], 'sa': ['3'], 'mi': ['3'], 'zo': ['3'], 'sun': ['3'], 'ta': ['3'],
  // 4
  'yon': ['4'], 'yo': ['4'], 'shi': ['4'], 'fo': ['4'], 'ho': ['4'], 'su': ['4'], 'c': ['4'],
  // 5
  'go': ['5'], 'ko': ['5', '9'], 'fa': ['5'], 'fi': ['5'], 'it': ['5'], 'u': ['5'], 'ka': ['5'], 'co': ['5'], 's': ['5'],
  // 6
  'roku': ['6'], 'ru': ['6'], 'mu': ['6'], 'ryu': ['6'], 'b': ['6'], 'v': ['6'],
  // 7
  'nana': ['7'], 'na': ['7'], 'shichi': ['7'], 'se': ['7'], 'sh': ['7'],
  // 8
  'hachi': ['8'], 'ha': ['8'], 'pa': ['8'], 'ba': ['8'], 'ya': ['8'], 'ei': ['8'], 'be': ['8'],
  // 9
  'kyuu': ['9'], 'ku': ['9'], 'gu': ['9'], 'qe': ['9'], 'ke': ['9'], 'q': ['9'], 'k': ['9'],
  // 10 (Special)
  'ten': ['10'], 'ju': ['10'], 'de': ['10'],
  // 100
  'hyaku': ['100'], 'mo': ['100'],
  // 1000
  'sen': ['1000']
};

export type GoroawaseResult = {
  original: string;
  converted: string;
  readings: string[];
};

/**
 * Attempts to convert a romaji string into a number sequence (Goroawase).
 * This is a simple greedy approach and might need refinement.
 */
export function generateGoroawase(input: string): GoroawaseResult[] {
  const normalized = input.toLowerCase().replace(/[^a-z0-9]/g, '');
  // console.log("Goroawase Normalized:", normalized);
  const results: GoroawaseResult[] = [];

  // Recursive search for combinations
  function findCombinations(remaining: string, currentNumbers: string, currentReadings: string[]) {
    // console.log(`Searching: rem="${remaining}", curr="${currentNumbers}"`);
    if (remaining.length === 0) {
      if (currentNumbers.length > 0) {
        results.push({
          original: input,
          converted: currentNumbers,
          readings: currentReadings
        });
      }
      return;
    }

    // Try to match prefixes of length 1 to 4 characters
    let matchedAny = false;
    for (let len = 4; len >= 1; len--) {
      if (remaining.length < len) continue;
      const substr = remaining.substring(0, len);

      if (PHONETIC_MAP[substr]) {
        matchedAny = true;
        for (const num of PHONETIC_MAP[substr]) {
          findCombinations(remaining.substring(len), currentNumbers + num, [...currentReadings, substr]);
        }
      }
    }

    // Fallback: If no Goroawase match found for current prefix, keep the character as is.
    if (!matchedAny) {
      findCombinations(remaining.substring(1), currentNumbers + remaining[0], [...currentReadings, remaining[0]]);
    }
  }

  findCombinations(normalized, "", []);

  // Deduplicate and filter simplistic results if needed
  const uniqueResults = Array.from(new Set(results.map(r => JSON.stringify(r)))).map(s => JSON.parse(s));
  return uniqueResults.sort((a, b) => a.converted.length - b.converted.length); // Shortest first
}
