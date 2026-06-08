import { useLanguageStore } from '@/store/language-store';
import { dictionaries } from '@/lib/dictionaries';

export function useTranslation() {
    const { language } = useLanguageStore();
    const t = dictionaries[language];
    return { t, language };
}
