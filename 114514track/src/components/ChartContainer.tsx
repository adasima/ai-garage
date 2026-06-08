"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, Time, AreaSeries, MouseEventParams } from "lightweight-charts";
import axios from "axios";
import { useCurrencyStore } from "./CurrencyToggle";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { CryptoData } from "@/lib/types";

interface ChartContainerProps {
    symbol: string; // Coin ID or Symbol
    coinId: string; // ID for API fetch
    color?: string;
}

export function ChartContainer({ coinId, symbol }: ChartContainerProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const mainSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
    const estSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);

    const [loading, setLoading] = useState(true);
    const { currency, formatPrice } = useCurrencyStore();

    // State for legend
    const [range, setRange] = useState<string>("1d");
    const [noData, setNoData] = useState(false);

    const TIMEFRAMES = [
        { label: "1H", value: "1h" },
        { label: "1D", value: "1d" },
        { label: "3D", value: "3d" },
        { label: "1W", value: "1w" },
        { label: "1M", value: "1m" },
        { label: "6M", value: "6m" },
        { label: "1Y", value: "1y" },
    ];

    // State for legend
    const [currentPrice, setCurrentPrice] = useState<string>("");
    const [priceChange, setPriceChange] = useState<number>(0);
    const [hoverPrice, setHoverPrice] = useState<string | null>(null);
    const [hoverDate, setHoverDate] = useState<string | null>(null);

    const [flash, setFlash] = useState(false);
    const prevPriceRef = useRef<number>(0);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Initialize Chart
        const handleResize = () => {
            chartRef.current?.applyOptions({ width: chartContainerRef.current!.clientWidth });
        };

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: "#A1A1AA", // zinc-400
            },
            grid: {
                vertLines: { color: "rgba(42, 42, 42, 0.1)" },
                horzLines: { color: "rgba(42, 42, 42, 0.1)" },
            },
            width: chartContainerRef.current.clientWidth,
            height: 600,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: "#27272a", // zinc-800
                rightOffset: 12,
                fixLeftEdge: true,
                fixRightEdge: true,
            },
            rightPriceScale: {
                borderColor: "#27272a",
                visible: true,
            },
            crosshair: {
                mode: 1, // CrosshairMode.Magnet
                vertLine: {
                    color: '#758696',
                    width: 1,
                    style: 3,
                    labelBackgroundColor: '#758696',
                },
                horzLine: {
                    color: '#758696',
                    width: 1,
                    style: 3,
                    labelBackgroundColor: '#758696',
                },
            },
        });

        // 1. Estimated Series (Yellow/Orange) - Added FIRST so it's behind main if overlap
        const estSeries = chart.addSeries(AreaSeries, {
            lineColor: "#FBBF24", // Amber-400
            topColor: "rgba(251, 191, 36, 0.4)",
            bottomColor: "rgba(251, 191, 36, 0.05)",
            lineWidth: 2,
            lineStyle: 1 // Solid
        });

        // 2. Main Series (Blue)
        const mainSeries = chart.addSeries(AreaSeries, {
            lineColor: "#2962FF",
            topColor: "#2962FF",
            bottomColor: "rgba(41, 98, 255, 0.28)",
            lineWidth: 2,
        });

        chartRef.current = chart;
        mainSeriesRef.current = mainSeries;
        estSeriesRef.current = estSeries;

        // Subscribe to crosshair move (Check both series)
        chart.subscribeCrosshairMove((param: MouseEventParams) => {
            if (
                param.point === undefined ||
                !param.time ||
                param.point.x < 0 ||
                param.point.x > chartContainerRef.current!.clientWidth ||
                param.point.y < 0 ||
                param.point.y > chartContainerRef.current!.clientHeight
            ) {
                setHoverPrice(null);
                setHoverDate(null);
            } else {
                // Try main series first, then est series
                let data = param.seriesData.get(mainSeries);
                if (!data) data = param.seriesData.get(estSeries);

                // @ts-expect-error - value exists on Area data
                const price = data?.value || data?.close;
                if (price !== undefined) {
                    setHoverPrice(price.toString());
                    const date = new Date((param.time as number) * 1000);
                    setHoverDate(date.toLocaleString());
                } else {
                    setHoverPrice(null);
                    setHoverDate(null);
                }
            }
        });

        window.addEventListener("resize", handleResize);

        // Fetch Data Function
        const fetchHistory = async () => {
            if (!chartRef.current) return;
            setNoData(false);

            try {
                // Pass range param
                const res = await axios.get(`/api/history/${coinId}?range=${range}`);
                const pricesRes = await axios.get('/api/prices');

                // Calculate Rates
                const btc = pricesRes.data.find((c: CryptoData) => c.config.id === 'bitcoin');
                let jpyRate = 150;
                let solPrice = 140;

                if (btc && btc.prices.usd) {
                    jpyRate = btc.prices.jpy / btc.prices.usd;
                }
                const solCoin = pricesRes.data.find((c: CryptoData) => c.config.id === 'solana');
                if (solCoin) {
                    solPrice = solCoin.prices.usd;
                }

                if (res.data && Array.isArray(res.data) && res.data.length > 0) {
                    // Convert data based on currency
                    const allData = res.data.map((d: { time: number; value: number; isEstimated?: boolean }) => {
                        let val = d.value;
                        if (currency === 'jpy') val *= jpyRate;
                        if (currency === 'sol' && solPrice > 0) val /= solPrice;
                        return {
                            time: d.time as Time,
                            value: val,
                            isEstimated: !!d.isEstimated
                        };
                    });

                    // Split into Main and Estimated
                    const mainData: { time: Time; value: number }[] = [];
                    const estData: { time: Time; value: number }[] = [];

                    allData.forEach((item, index) => {
                        if (item.isEstimated) {
                            estData.push({ time: item.time, value: item.value });
                            // STITCHING
                            if (index < allData.length - 1 && !allData[index + 1].isEstimated) {
                                const next = allData[index + 1];
                                estData.push({ time: next.time, value: next.value });
                            }
                        } else {
                            mainData.push({ time: item.time, value: item.value });
                        }
                    });

                    mainSeries.setData(mainData);
                    estSeries.setData(estData);

                    chart.timeScale().fitContent();

                    // Update Current Price & Trigger Flash
                    if (allData.length > 0) {
                        const last = allData[allData.length - 1];
                        const newVal = last.value;

                        setCurrentPrice(newVal.toString());

                        const first = allData[0];
                        const change = ((newVal - first.value) / first.value) * 100;
                        setPriceChange(change);

                        // Flash Logic
                        if (prevPriceRef.current > 0 && Math.abs(prevPriceRef.current - newVal) > 0.0000001) {
                            setFlash(true);
                            setTimeout(() => setFlash(false), 1500);
                        }
                        prevPriceRef.current = newVal;
                    }
                } else {
                    // No data returned
                    setNoData(true);
                    mainSeries.setData([]);
                    estSeries.setData([]);
                }
            } catch (e) {
                console.error(e);
                setNoData(true);
            } finally {
                setLoading(false);
            }
        };

        // Initial Fetch
        setLoading(true); // Set loading true for initial fetch
        fetchHistory();

        // Polling (30s)
        const intervalId = setInterval(fetchHistory, 30000);

        return () => {
            window.removeEventListener("resize", handleResize);
            clearInterval(intervalId);
            chart.remove();
        };
    }, [coinId, currency, range]); // Re-run when currency OR range changes

    return (
        <div className="relative w-full h-[600px] bg-secondary/10 rounded-xl border border-border/50 backdrop-blur-sm p-4 group flex flex-col">

            {/* Header / Controls */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4 z-20 relative">
                {/* Legend / Price Info */}
                <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground font-medium uppercase tracking-wider">{symbol} / {currency}</span>
                        {/* Legend Dot */}
                        <div className="flex items-center gap-2 ml-4 text-xs text-muted-foreground bg-black/20 px-2 py-1 rounded-full border border-white/5">
                            <div className="w-2 h-2 rounded-full bg-[#FBBF24]"></div>
                            <span>Estimated</span>
                        </div>
                    </div>

                    <div className="flex items-baseline gap-3">
                        <span className={cn(
                            "text-3xl font-bold tracking-tight text-foreground px-2 py-1 rounded transition-colors duration-200",
                            flash && "animate-flash bg-white/10" // Flash Effect
                        )}>
                            {hoverPrice ? formatPrice(hoverPrice) : formatPrice(currentPrice)}
                        </span>
                        {!hoverPrice && (
                            <span className={cn("text-sm font-medium px-2 py-0.5 rounded", priceChange >= 0 ? "text-emerald-500 bg-emerald-500/10" : "text-rose-500 bg-rose-500/10")}>
                                {priceChange > 0 ? "+" : ""}{priceChange.toFixed(2)}%
                            </span>
                        )}
                    </div>
                    {hoverDate && (
                        <span className="text-xs text-muted-foreground mt-1 px-2">
                            {hoverDate}
                        </span>
                    )}
                </div>

                {/* Range Selector */}
                <div className="flex bg-secondary/30 p-1 rounded-lg border border-border/30">
                    {TIMEFRAMES.map((tf) => (
                        <button
                            key={tf.value}
                            onClick={() => setRange(tf.value)}
                            className={cn(
                                "px-3 py-1 text-sm font-medium rounded-md transition-all",
                                range === tf.value
                                    ? "bg-primary text-primary-foreground shadow-sm"
                                    : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                            )}
                        >
                            {tf.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart Area */}
            <div className="relative flex-1 min-h-0 w-full">
                {loading && (
                    <div className="absolute inset-0 z-30 flex items-center justify-center bg-background/50 backdrop-blur-sm rounded-xl">
                        <Skeleton className="w-full h-full" />
                    </div>
                )}

                {noData && !loading && (
                    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-background/20 backdrop-blur-sm">
                        <p className="text-muted-foreground font-medium text-lg">No Data Available</p>
                        <p className="text-sm text-muted-foreground/60">Try selecting a shorter timeframe.</p>
                    </div>
                )}

                <div ref={chartContainerRef} className="w-full h-full" />
            </div>
        </div>
    );
}
