"use client";

import { Home, Ruler, Percent, TrendingDown } from "lucide-react";
import type { DashboardKpis } from "@/lib/kpis";
import { formatCompactCurrency } from "@/lib/format";

function KpiCard({
  icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  accent: string;
}) {
  return (
    <div className="flex flex-1 min-w-[200px] items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${accent}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
        <p className="mt-0.5 truncate text-xl font-semibold text-slate-900">{value}</p>
        {sub && <p className="mt-0.5 truncate text-xs text-slate-500">{sub}</p>}
      </div>
    </div>
  );
}

export default function KpiHeader({ kpis }: { kpis: DashboardKpis }) {
  return (
    <div className="flex flex-wrap gap-3">
      <KpiCard
        icon={<Home className="h-5 w-5 text-ocean-700" />}
        accent="bg-ocean-100"
        label="Active Deals Under $240k"
        value={kpis.totalActiveDeals.toString()}
      />
      <KpiCard
        icon={<Ruler className="h-5 w-5 text-ocean-700" />}
        accent="bg-ocean-100"
        label="Median $ / SqFt"
        value={
          kpis.medianPricePerSqft !== null
            ? `$${kpis.medianPricePerSqft.toFixed(0)}`
            : "—"
        }
      />
      <KpiCard
        icon={<Percent className="h-5 w-5 text-emerald-700" />}
        accent="bg-emerald-100"
        label="Best Builder Promo Rate"
        value={kpis.bestPromoRate ? `${kpis.bestPromoRate.rate}%` : "—"}
        sub={kpis.bestPromoRate?.builder}
      />
      <KpiCard
        icon={<TrendingDown className="h-5 w-5 text-rose-700" />}
        accent="bg-rose-100"
        label="Largest Price Cut"
        value={
          kpis.largestPriceCut ? formatCompactCurrency(kpis.largestPriceCut.amount) : "—"
        }
        sub={kpis.largestPriceCut?.address}
      />
    </div>
  );
}
