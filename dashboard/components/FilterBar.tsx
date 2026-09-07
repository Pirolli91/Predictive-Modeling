"use client";

import { SlidersHorizontal } from "lucide-react";
import type { FilterState } from "@/lib/types";

export default function FilterBar({
  filters,
  onChange,
  counties,
}: {
  filters: FilterState;
  onChange: (next: FilterState) => void;
  counties: string[];
}) {
  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2 pr-2 text-slate-500">
        <SlidersHorizontal className="h-4 w-4" />
        <span className="text-xs font-semibold uppercase tracking-wide">Filters</span>
      </div>

      <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
        County
        <select
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 focus:border-ocean-500 focus:outline-none focus:ring-1 focus:ring-ocean-500"
          value={filters.county}
          onChange={(e) => onChange({ ...filters, county: e.target.value })}
        >
          <option value="all">All counties</option>
          {counties.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
        Max Price: ${filters.maxPrice.toLocaleString()}
        <input
          type="range"
          min={100000}
          max={240000}
          step={5000}
          value={filters.maxPrice}
          onChange={(e) => onChange({ ...filters, maxPrice: Number(e.target.value) })}
          className="w-40 accent-ocean-600"
        />
      </label>

      <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
        Min SqFt: {filters.minSqft.toLocaleString()}
        <input
          type="range"
          min={0}
          max={2500}
          step={100}
          value={filters.minSqft}
          onChange={(e) => onChange({ ...filters, minSqft: Number(e.target.value) })}
          className="w-40 accent-ocean-600"
        />
      </label>

      <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
        <input
          type="checkbox"
          checked={filters.investorEligibleOnly}
          onChange={(e) =>
            onChange({ ...filters, investorEligibleOnly: e.target.checked })
          }
          className="h-4 w-4 rounded border-slate-300 text-ocean-600 focus:ring-ocean-500"
        />
        Investor-eligible promos only
      </label>
    </div>
  );
}
