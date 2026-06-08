
'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, Variants } from 'framer-motion';
import { ExternalLink, Copy, Check, Flame, Globe } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

type DomainCardProps = {
    domain: string;
    type: 'goroawase' | 'hack';
    voltage: {
        level: 1 | 2 | 3;
        advantages: string[];
    };
    metadata: any;
    status: 'available' | 'taken' | 'unknown';
    index: number;
};

export function DomainCard({ domain, type, voltage, metadata, status, index }: DomainCardProps) {
    const [copied, setCopied] = useState(false);
    // Fix: Only show slot for goroawase. Hacks should show immediately.
    const [showSlot, setShowSlot] = useState(type === 'goroawase');
    const [slotNumber, setSlotNumber] = useState('00');

    // Helper for merging classes
    function cn(...inputs: (string | undefined | null | false)[]) {
        return twMerge(clsx(inputs));
    }

    // Handle Copy
    const handleCopy = () => {
        navigator.clipboard.writeText(domain);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    // Slot Animation for Goroawase
    useEffect(() => {
        if (type === 'goroawase' && metadata.goroawase) {
            const target = metadata.goroawase.converted;
            const duration = 600; // ms
            const intervalTime = 50;
            let elapsed = 0;

            const timer = setInterval(() => {
                elapsed += intervalTime;
                if (elapsed < duration) {
                    // Random number of same length
                    setSlotNumber(Math.floor(Math.random() * Math.pow(10, target.length)).toString().padStart(target.length, '0'));
                } else {
                    setSlotNumber(target);
                    setShowSlot(false);
                    clearInterval(timer);
                }
            }, intervalTime);

            return () => clearInterval(timer);
        }
    }, [type, metadata]);

    // Shake Variant (Updated to ensure visibility)
    const shakeVariants: Variants = {
        shake1: {
            x: [0, -2, 2, -2, 2, 0],
            opacity: 1,
            transition: { duration: 0.2 }
        },
        shake2: {
            x: [0, -5, 5, -5, 5, 0],
            opacity: 1,
            transition: { duration: 0.25 }
        },
        shake3: {
            x: [0, -10, 10, -10, 10, -5, 5, 0],
            y: [0, 2, -2, 0],
            scale: [1, 1.05, 1],
            opacity: 1,
            transition: { duration: 0.3, type: 'spring', stiffness: 300 }
        }
    };

    const shakeLevel = `shake${voltage.level}` as keyof typeof shakeVariants;

    return (
        <motion.div
            layout
            // Removed initial/enter to fix "invisible" bug. Relies on parent for entry fade.
            animate={shakeLevel as string}
            variants={shakeVariants}
            className={cn(
                "relative group rounded-xl border p-4 mb-3 cursor-pointer transition-all",
                "bg-zinc-900 border-zinc-800 hover:border-zinc-600 hover:bg-zinc-800",
                status === 'taken' && "opacity-60 grayscale-[0.5]"
            )}
            onClick={handleCopy}
        >
            <div className="flex justify-between items-start">
                {/* Main Content */}
                <div className="flex-1">
                    <div className="flex items-baseline gap-2">
                        <h3 className="text-xl font-bold font-mono tracking-tight text-white">
                            {type === 'goroawase' && showSlot ? (
                                <span className="text-emerald-400 font-mono">{slotNumber}</span>
                            ) : (
                                <span className={cn(type === 'goroawase' ? "text-emerald-400" : "text-blue-400")}>
                                    {type === 'goroawase' ? metadata.goroawase?.converted : metadata.hack?.prefix}
                                </span>
                            )}
                            <span className="text-zinc-400">
                                {type === 'goroawase'
                                    ? domain.replace(metadata.goroawase?.converted || '', '')
                                    : `.${metadata.hack?.tld}`
                                }
                            </span>
                        </h3>

                        {/* Copied Tooltip */}
                        <AnimatePresence>
                            {copied && (
                                <motion.span
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0 }}
                                    className="text-xs text-emerald-500 font-bold flex items-center gap-1"
                                >
                                    <Check size={12} /> Copied!
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </div>

                    <div className="text-sm text-zinc-500 mt-1 flex items-center gap-2">
                        {type === 'goroawase' && (
                            <span>{metadata.origin} ({metadata.goroawase?.readings.join('-')})</span>
                        )}
                        {type === 'hack' && (
                            <span>{metadata.origin}</span>
                        )}
                    </div>

                    {/* Advantages */}
                    <div className="flex flex-wrap gap-2 mt-3">
                        {voltage.advantages.map((adv, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-full bg-zinc-800 text-xs text-zinc-300 border border-zinc-700">
                                {adv}
                            </span>
                        ))}
                        {status === 'taken' && (
                            <span className="px-2 py-0.5 rounded-full bg-red-900/30 text-red-400 text-xs border border-red-900">
                                Taken/Unresolved
                            </span>
                        )}
                        {status === 'available' && (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-900/30 text-emerald-400 text-xs border border-emerald-900">
                                Likely Available
                            </span>
                        )}
                    </div>
                </div>

                {/* Voltage Fire */}
                <div className="flex flex-col items-end gap-2">
                    <div className="flex">
                        {Array.from({ length: voltage.level }).map((_, i) => (
                            <motion.div
                                key={i}
                                initial={{ scale: 0, x: 20 }}
                                animate={{ scale: 1, x: 0 }}
                                transition={{ delay: 0.5 + (i * 0.1), type: 'spring' }}
                            >
                                <Flame className={cn(
                                    "w-5 h-5",
                                    voltage.level === 3 ? "text-orange-500 fill-orange-500 drop-shadow-[0_0_8px_rgba(249,115,22,0.8)]" :
                                        voltage.level === 2 ? "text-orange-400 fill-orange-400" : "text-yellow-600"
                                )} />
                            </motion.div>
                        ))}
                    </div>

                    {/* Action Links */}
                    <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                        <a
                            href={`https://www.namecheap.com/domains/registration/results/?domain=${domain}`}
                            target="_blank"
                            rel="noreferrer"
                            className="p-2 hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-white transition-colors"
                            title="Register on Namecheap"
                        >
                            <ExternalLink size={16} />
                        </a>
                        <a
                            href={`http://${domain}`}
                            target="_blank"
                            rel="noreferrer"
                            className="p-2 hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-white transition-colors"
                            title="Visit Site"
                        >
                            <Globe size={16} />
                        </a>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
