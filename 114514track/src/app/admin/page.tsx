"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { SystemConfig, CoinConfig } from "@/lib/types";
import { Trash2, Plus, Save, Search, Edit2 } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/hooks/use-translation";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function AdminPage() {
    const [config, setConfig] = useState<SystemConfig | null>(null);
    const [loading, setLoading] = useState(true);

    // Search & Add
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

    // Edit Mode
    const [editingCoin, setEditingCoin] = useState<CoinConfig | null>(null);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

    const { t } = useTranslation();

    const fetchConfig = async () => {
        try {
            const res = await axios.get("/api/admin/config");
            setConfig(res.data);
        } catch (e) {
            toast.error(t.common.error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConfig();
    }, []);

    const handleSave = async () => {
        if (!config) return;
        try {
            await axios.post("/api/admin/config", config);
            toast.success(t.admin.configurationSaved);
        } catch (e) {
            toast.error(t.common.error);
        }
    };

    const toggleCoin = (id: string) => {
        if (!config) return;
        const updatedCoins = config.coins.map(c =>
            c.id === id ? { ...c, isEnabled: !c.isEnabled } : c
        );
        setConfig({ ...config, coins: updatedCoins });
    };

    const removeCoin = (id: string) => {
        if (!config) return;
        if (!confirm(t.common.delete + "?")) return;
        const updatedCoins = config.coins.filter(c => c.id !== id);
        setConfig({ ...config, coins: updatedCoins });
    };

    // --- Search & One-Click Add ---
    const handleSearch = async (q: string) => {
        setSearchQuery(q);
        if (q.length < 2) return;

        setIsSearching(true);
        try {
            const res = await axios.get(`/api/admin/search?q=${q}`);
            setSearchResults(res.data.results);
        } catch (e) {
            console.error(e);
        } finally {
            setIsSearching(false);
        }
    };

    const addCoinFromSearch = (result: any) => {
        if (!config) return;

        // Prevent duplicates
        if (config.coins.some(c => c.apiId === result.apiId || c.symbol === result.symbol)) {
            toast.error("Coin already exists!");
            return;
        }

        const newCoin: CoinConfig = {
            id: result.source === 'dexscreener' ? result.symbol.toLowerCase() + '-' + result.id.substring(0, 4) : result.id, // Ensure unique ID
            symbol: result.symbol.toUpperCase(),
            name: result.name,
            apiId: result.apiId,
            source: result.source,
            isEnabled: true
        };

        setConfig({ ...config, coins: [...config.coins, newCoin] });
        toast.success(`${newCoin.name} added!`);
        setIsAddDialogOpen(false);
        setSearchQuery("");
        setSearchResults([]);
    };

    // --- Edit Functionality ---
    const startEdit = (coin: CoinConfig) => {
        setEditingCoin({ ...coin });
        setIsEditDialogOpen(true);
    };

    const saveEdit = () => {
        if (!config || !editingCoin) return;
        const updatedCoins = config.coins.map(c =>
            c.id === editingCoin.id ? editingCoin : c
        );
        setConfig({ ...config, coins: updatedCoins });
        setIsEditDialogOpen(false);
        toast.success("Coin updated!");
    };


    if (loading) return <div className="p-8"><Skeleton className="h-96 w-full" /></div>;
    if (!config) return <div className="p-8">{t.common.error}</div>;

    return (
        <div className="container py-8 max-w-4xl space-y-8 animate-in fade-in">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold">{t.admin.title}</h1>
                <div className="flex gap-2">
                    <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <Plus className="w-4 h-4" /> {t.admin.addNewCoin}
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-md">
                            <DialogHeader>
                                <DialogTitle>{t.admin.addNewCoin}</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4">
                                <div className="relative">
                                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        placeholder="Search by name, symbol, or address..."
                                        className="pl-9"
                                        value={searchQuery}
                                        onChange={(e) => handleSearch(e.target.value)}
                                    />
                                </div>
                                <div className="max-h-[300px] overflow-y-auto space-y-2">
                                    {isSearching ? (
                                        <div className="flex justify-center p-4"><Skeleton className="h-8 w-full" /></div>
                                    ) : searchResults.length > 0 ? (
                                        searchResults.map((res) => (
                                            <div key={res.id + res.source} className="flex items-center justify-between p-2 rounded-lg border hover:bg-secondary/50">
                                                <div className="flex items-center gap-3">
                                                    {res.thumb && <img src={res.thumb} alt="" className="w-6 h-6 rounded-full" />}
                                                    <div>
                                                        <div className="font-bold text-sm">{res.name} ({res.symbol})</div>
                                                        <div className="text-xs text-muted-foreground">{res.subtitle}</div>
                                                    </div>
                                                </div>
                                                <Button size="sm" variant="ghost" onClick={() => addCoinFromSearch(res)}>
                                                    {t.common.add}
                                                </Button>
                                            </div>
                                        ))
                                    ) : searchQuery.length > 2 && (
                                        <div className="text-center text-sm text-muted-foreground p-4">No results found</div>
                                    )}
                                </div>
                            </div>
                        </DialogContent>
                    </Dialog>

                    <Button onClick={handleSave} className="gap-2">
                        <Save className="w-4 h-4" /> {t.common.save}
                    </Button>
                </div>
            </div>

            {/* Global Settings */}
            <section className="bg-secondary/20 p-6 rounded-xl border border-border">
                <h2 className="text-xl font-semibold mb-4">{t.admin.systemStatus}</h2>
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={config.globalEnabled}
                            onChange={(e) => setConfig({ ...config, globalEnabled: e.target.checked })}
                            className="w-5 h-5 accent-primary"
                        />
                        <span>{t.admin.globalEnabled}</span>
                    </label>
                </div>
            </section>

            {/* Coin Management */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">{t.admin.coinManagement}</h2>
                <div className="grid gap-4">
                    {config.coins.map((coin) => (
                        <div key={coin.id} className="flex items-center justify-between bg-card p-4 rounded-lg border border-border shadow-sm group">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center font-bold">
                                    {coin.symbol[0]}
                                </div>
                                <div>
                                    <div className="font-bold flex items-center gap-2">
                                        {coin.name}
                                        <span className={cn("text-xs px-2 py-0.5 rounded text-muted-foreground", coin.source === 'dexscreener' ? "bg-purple-500/10 text-purple-500" : "bg-green-500/10 text-green-500")}>
                                            {coin.source}
                                        </span>
                                    </div>
                                    <div className="text-xs text-muted-foreground font-mono">{coin.apiId}</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => startEdit(coin)}>
                                    <Edit2 className="w-4 h-4 text-muted-foreground" />
                                </Button>
                                <label className="flex items-center gap-2 text-sm cursor-pointer px-2">
                                    <input
                                        type="checkbox"
                                        checked={coin.isEnabled}
                                        onChange={() => toggleCoin(coin.id)}
                                        className="w-4 h-4 accent-emerald-500"
                                    />
                                    <span className="hidden sm:inline">{coin.isEnabled ? "Active" : "Hidden"}</span>
                                </label>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => removeCoin(coin.id)}
                                    className="text-destructive hover:bg-destructive/10"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Edit Dialog */}
            <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{t.admin.editCoin}</DialogTitle>
                    </DialogHeader>
                    {editingCoin && (
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Name</label>
                                <Input
                                    value={editingCoin.name}
                                    onChange={e => setEditingCoin({ ...editingCoin, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Symbol</label>
                                <Input
                                    value={editingCoin.symbol}
                                    onChange={e => setEditingCoin({ ...editingCoin, symbol: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">API ID / Address</label>
                                <Input
                                    value={editingCoin.apiId}
                                    onChange={e => setEditingCoin({ ...editingCoin, apiId: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Source</label>
                                <select
                                    className="w-full p-2 rounded-md border bg-background"
                                    value={editingCoin.source}
                                    onChange={e => setEditingCoin({ ...editingCoin, source: e.target.value as any })}
                                >
                                    <option value="coingecko">CoinGecko</option>
                                    <option value="dexscreener">DexScreener</option>
                                </select>
                            </div>
                            <Button onClick={saveEdit} className="w-full">{t.common.save}</Button>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
