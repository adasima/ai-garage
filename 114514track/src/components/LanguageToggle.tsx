"use client";

import { useLanguageStore } from "@/store/language-store";
import { Button } from "@/components/ui/button";
import { Languages } from "lucide-react";

export function LanguageToggle() {
    const { language, setLanguage } = useLanguageStore();

    const toggleLanguage = () => {
        setLanguage(language === 'en' ? 'ja' : 'en');
    };

    return (
        <Button
            variant="ghost"
            size="icon"
            onClick={toggleLanguage}
            className="rounded-full hover:bg-secondary/80"
            title={language === 'en' ? "Switch to Japanese" : "英語に切り替え"}
        >
            <Languages className="w-5 h-5" />
            <span className="sr-only">Toggle Language</span>
        </Button>
    );
}
