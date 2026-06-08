
'use client';

import React from 'react';
import { DomainResult } from '@/lib/domain-logic/generator';
import { DomainCard } from './DomainCard';
import { useDomainAvailability } from '@/hooks/useDomainAvailability';
import { motion, AnimatePresence } from 'framer-motion';

type ResultStreamProps = {
    results: DomainResult[];
    gachiMode: boolean;
};

function StreamItem({ result, gachiMode }: { result: DomainResult; gachiMode: boolean }) {
    const { status, loading } = useDomainAvailability(result.domain);

    // If Gachi Mode is ON, and we know it's taken, hide it.
    // While loading (unknown), we likely show it? User said "Filter out Taken".
    // If we hide while loading, it might pop in later.
    // Better: Show while unknown. Hide if taken.

    if (gachiMode && status === 'taken') {
        return null;
    }

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3 }}
        >
            <DomainCard
                domain={result.domain}
                type={result.type}
                voltage={result.voltage}
                metadata={result.metadata}
                status={status} // Pass the fetched status
                index={0}
            />
        </motion.div>
    );
}

export function ResultStream({ results, gachiMode }: ResultStreamProps) {
    return (
        <div className="w-full max-w-2xl mx-auto pt-4 pb-12">
            <AnimatePresence>
                {results.map((result) => (
                    <StreamItem key={result.id} result={result} gachiMode={gachiMode} />
                ))}
            </AnimatePresence>

            {results.length === 0 && (
                <div className="text-center text-zinc-600 mt-10">
                    Type something to start...
                </div>
            )}
        </div>
    );
}
