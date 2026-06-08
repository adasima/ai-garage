
'use client';

import React from 'react';
import { Search, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

type HeroInputProps = {
    value: string;
    onChange: (val: string) => void;
    gachiMode: boolean;
    setGachiMode: (val: boolean) => void;
};

export function HeroInput({ value, onChange, gachiMode, setGachiMode }: HeroInputProps) {
    return (
        <div className="flex flex-col items-center justify-center w-full pt-12 pb-2 px-4">
            {/* Brand */}
            <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="flex items-center gap-2 mb-8"
            >
                <Zap className="text-yellow-400 fill-yellow-400" size={32} />
                <h1 className="text-4xl font-bold text-white tracking-tighter">
                    Omoshiro<span className="text-zinc-500">.dom</span>
                </h1>
            </motion.div>

            {/* Input */}
            <div className="relative w-full max-w-2xl group">
                <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                    <Search className="text-zinc-500 group-focus-within:text-yellow-400 transition-colors" />
                </div>
                <input
                    type="text"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder="Enter a keyword (e.g. niku, focus, awesome)..."
                    className="w-full bg-zinc-900 border border-zinc-700 text-white text-xl p-4 pl-12 rounded-2xl focus:outline-none focus:ring-2 focus:ring-yellow-400/50 focus:border-yellow-400/50 transition-all placeholder:text-zinc-600"
                    autoFocus
                />
                {/* Decorative particles or glow could go here */}
            </div>

            {/* Controls */}
            <div className="w-full max-w-2xl mt-4 flex justify-between items-center text-sm text-zinc-400 px-2">
                <div className="flex items-center gap-2">
                    {/* Placeholder for future features */}
                </div>

                {/* Museum Mode Toggle (Show Taken) */}
                {/* Logic: gachiMode=true (Hunter/Hide Taken) vs false (Museum/Show All) */}
                {/* User wants "Selectable mode to include unavailable". So Toggle ON = Museum Mode (gachi=false) */}
                <div className="flex items-center gap-3">
                    <span className={!gachiMode ? "text-pink-400 font-bold" : "text-zinc-500"}>
                        Museum Mode <span className="text-xs font-normal opacity-70">(Includes Taken)</span>
                    </span>
                    <button
                        onClick={() => setGachiMode(!gachiMode)}
                        className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${!gachiMode ? 'bg-pink-500' : 'bg-zinc-700'
                            }`}
                    >
                        <motion.div
                            className="w-4 h-4 rounded-full bg-white shadow-sm"
                            animate={{ x: !gachiMode ? 24 : 0 }}
                            transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                    </button>
                </div>
            </div>
        </div>
    );
}
