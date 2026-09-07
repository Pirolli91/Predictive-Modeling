"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { LayoutGrid, Table as TableIcon, Waves } from "lucide-react";
import type { FilterState, Listing, ListingsPayload } from "@/lib/types";
import { computeKpis } from "@/lib/kpis";
import KpiHeader from "@/components/KpiHeader";
import FilterBar from "@/components/FilterBar";
import DealCard from "@/components/DealCard";
import DealTable from "@/components/DealTable";
import MortgageCalculatorModal from "@/components/MortgageCalculatorModal";

const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-slate-400">
      Loading map…
    </div>
  ),
});

type ViewMode = "cards" | "table";

export default function DashboardClient({ data }: { data: ListingsPayload }) {
  const counties = useMemo(
    () =>
      Array.from(new Set(data.listings.map((l) => l.county).filter(Boolean))).sort() as string[],
    [data.listings]
  );

  const [filters, setFilters] = useState<FilterState>({
    county: "all",
    maxPrice: data.price_cap,
    minSqft: 0,
    investorEligibleOnly: false,
  });
  const [viewMode, setViewMode] = useState<ViewMode>("cards");
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);

  const filteredListings = useMemo(() => {
    return data.listings.filter((listing) => {
      if (filters.county !== "all" && listing.county !== filters.county) return false;
      if (listing.price > filters.maxPrice) return false;
      if (filters.minSqft > 0 && (listing.sqft ?? 0) < filters.minSqft) return false;
      if (filters.investorEligibleOnly && listing.investor_eligibility_flag !== "investor_eligible")
        return false;
      return true;
    });
  }, [data.listings, filters]);

  const kpis = useMemo(() => computeKpis(filteredListings), [filteredListings]);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-5 p-4 sm:p-6">
      <header className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Waves className="h-6 w-6 text-ocean-600" />
          <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">
            NC Coastal Townhome Investment Dashboard
          </h1>
        </div>
        <p className="text-sm text-slate-500">
          New-construction townhomes &amp; attached villas in coastal North Carolina, priced at
          or below ${data.price_cap.toLocaleString()}. Updated{" "}
          {new Date(data.generated_at).toLocaleString("en-US", {
            dateStyle: "medium",
            timeStyle: "short",
          })}
          .
        </p>
      </header>

      <KpiHeader kpis={kpis} />

      <FilterBar filters={filters} onChange={setFilters} counties={counties} />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
        <div className="h-[420px] rounded-xl border border-slate-200 bg-white p-2 shadow-sm lg:col-span-2 lg:h-auto">
          <MapView listings={filteredListings} onSelect={setSelectedListing} />
        </div>

        <div className="flex flex-col gap-3 lg:col-span-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-600">
              {filteredListings.length} matching listing
              {filteredListings.length === 1 ? "" : "s"}
            </p>
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
              <button
                onClick={() => setViewMode("cards")}
                className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium ${
                  viewMode === "cards"
                    ? "bg-ocean-700 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                Cards
              </button>
              <button
                onClick={() => setViewMode("table")}
                className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium ${
                  viewMode === "table"
                    ? "bg-ocean-700 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <TableIcon className="h-3.5 w-3.5" />
                Table
              </button>
            </div>
          </div>

          {viewMode === "cards" ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {filteredListings.map((listing) => (
                <DealCard key={listing.id} listing={listing} onOpenCalculator={setSelectedListing} />
              ))}
            </div>
          ) : (
            <DealTable listings={filteredListings} onOpenCalculator={setSelectedListing} />
          )}

          {filteredListings.length === 0 && (
            <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
              No listings match the current filters.
            </p>
          )}
        </div>
      </div>

      {selectedListing && (
        <MortgageCalculatorModal listing={selectedListing} onClose={() => setSelectedListing(null)} />
      )}
    </div>
  );
}
