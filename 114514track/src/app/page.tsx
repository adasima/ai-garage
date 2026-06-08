"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { CryptoTile } from "@/components/CryptoTile";
import { CurrencyToggle } from "@/components/CurrencyToggle";
import { CryptoData } from "@/lib/types";
import { toast } from "sonner";
import { useTranslation } from "@/hooks/use-translation";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const [data, setData] = useState<CryptoData[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const { t } = useTranslation();

  const fetchData = async () => {
    try {
      const res = await axios.get<CryptoData[]>("/api/prices");
      setData(res.data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch prices", error);
      toast.error(t.common.error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="container py-8 space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{t.dashboard.title}</h2>
          <p className="text-muted-foreground">
            {t.dashboard.subtitle}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-xs text-muted-foreground hidden md:inline-block animate-pulse">
              {t.dashboard.lastUpdated}: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <CurrencyToggle />
        </div>
      </div>

      {/* Tiles Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {loading && data.length === 0
          ? Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-xl bg-secondary/20" />
          ))
          : data.map((coin) => (
            <CryptoTile key={coin.config.id} data={coin} />
          ))}
      </div>

      {/* Fallback for empty state */}
      {!loading && data.length === 0 && (
        <div className="text-center py-20">
          <p className="text-muted-foreground">No coins are currently being tracked.</p>
        </div>
      )}
    </div>
  );
}
