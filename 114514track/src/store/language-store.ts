import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Locale } from '@/lib/dictionaries';

interface LanguageState {
    language: Locale;
    setLanguage: (lang: Locale) => void;
}

export const useLanguageStore = create<LanguageState>()(
    persist(
        (set) => ({
            language: 'ja', // Default to Japanese as requested
            setLanguage: (language) => set({ language }),
        }),
        {
            name: 'language-storage',
        }
    )
);
