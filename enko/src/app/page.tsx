
'use client';

import React, { useState, useEffect } from 'react';
import { HeroInput } from '@/components/HeroInput';
import { ResultStream } from '@/components/ResultStream';
import { generateDomains, DomainResult } from '@/lib/domain-logic/generator';

export default function Home() {
  const [input, setInput] = useState('');
  const [results, setResults] = useState<DomainResult[]>([]);
  // Default to "Hunter Mode" (Hide Taken = true)
  // Toggle enables "Museum Mode" (Hide Taken = false -> Show All)
  // So gachiMode = true means "Strict/Hunter Mode" (Hide Taken)
  const [gachiMode, setGachiMode] = useState(true);

  // Debounced Generation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (input.length > 0) {
        const generated = generateDomains(input);
        setResults(generated);
      } else {
        setResults([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [input]);

  return (
    <main className="min-h-screen bg-black text-white selection:bg-yellow-400/30 selection:text-yellow-100">
      <div className="container mx-auto px-4 pb-20">
        <HeroInput
          value={input}
          onChange={setInput}
          gachiMode={gachiMode}
          setGachiMode={setGachiMode}
        />

        <ResultStream
          results={results}
          gachiMode={gachiMode}
        />
      </div>
    </main>
  );
}
