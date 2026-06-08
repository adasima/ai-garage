"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Settings, LayoutDashboard, Search, FileChartLine } from "lucide-react";

import {
    CommandDialog,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
    CommandSeparator,
} from "@/components/ui/command";
import { useTranslation } from "@/hooks/use-translation";

export function CommandPalette() {
    const [open, setOpen] = useState(false);
    const router = useRouter();
    const { t } = useTranslation();

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((open) => !open);
            }
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    const runCommand = (command: () => void) => {
        setOpen(false);
        command();
    };

    return (
        <>
            <button
                onClick={() => setOpen(true)}
                className="fixed bottom-4 right-4 z-50 md:hidden p-3 bg-primary text-primary-foreground rounded-full shadow-lg"
            >
                <Search className="w-6 h-6" />
            </button>

            <CommandDialog open={open} onOpenChange={setOpen}>
                <CommandInput placeholder={t.command.placeholder} />
                <CommandList>
                    <CommandEmpty>No results found.</CommandEmpty>
                    <CommandGroup heading={t.command.suggestions}>
                        <CommandItem onSelect={() => runCommand(() => router.push("/"))}>
                            <LayoutDashboard className="mr-2 h-4 w-4" />
                            <span>{t.common.dashboard}</span>
                        </CommandItem>
                        <CommandItem onSelect={() => runCommand(() => router.push("/admin"))}>
                            <Settings className="mr-2 h-4 w-4" />
                            <span>{t.common.admin}</span>
                        </CommandItem>
                    </CommandGroup>
                    <CommandSeparator />
                    <CommandGroup heading={t.command.coins}>
                        {/* Static list for now, strictly we should pass these or fetch them */}
                        <CommandItem onSelect={() => runCommand(() => router.push("/coins/BTC"))}>
                            <FileChartLine className="mr-2 h-4 w-4" />
                            <span>Bitcoin (BTC)</span>
                        </CommandItem>
                        <CommandItem onSelect={() => runCommand(() => router.push("/coins/ETH"))}>
                            <FileChartLine className="mr-2 h-4 w-4" />
                            <span>Ethereum (ETH)</span>
                        </CommandItem>
                        <CommandItem onSelect={() => runCommand(() => router.push("/coins/SOL"))}>
                            <FileChartLine className="mr-2 h-4 w-4" />
                            <span>Solana (SOL)</span>
                        </CommandItem>
                    </CommandGroup>
                </CommandList>
            </CommandDialog>
        </>
    );
}
