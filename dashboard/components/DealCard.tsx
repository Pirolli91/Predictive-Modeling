"use client";

import { MapPin, Bed, Bath, Ruler, TrendingDown, TrendingUp, Sparkles, Calculator } from "lucide-react";
import type { Listing } from "@/lib/types";
import { formatCompactCurrency, formatPercent, investorEligibilityLabel } from "@/lib/format";

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  new: { label: "New", className: "bg-ocean-100 text-ocean-800" },
  price_drop: { label: "Price Drop", className: "bg-emerald-100 text-emerald-800" },
  price_increase: { label: "Price Increase", className: "bg-amber-100 text-amber-800" },
  unchanged: { label: "", className: "" },
};

export default function DealCard({
  listing,
  onOpenCalculator,
}: {
  listing: Listing;
  onOpenCalculator: (listing: Listing) => void;
}) {
  const badge = STATUS_BADGE[listing.listing_status];
  const investorEligible = listing.investor_eligibility_flag === "investor_eligible";

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-900">
            {listing.community_name ?? listing.address ?? "Unnamed community"}
          </p>
          <p className="truncate text-xs text-slate-500">{listing.builder_name}</p>
        </div>
        <p className="shrink-0 text-lg font-bold text-ocean-700">
          {formatCompactCurrency(listing.price)}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {badge?.label && (
          <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${badge.className}`}>
            {badge.label}
          </span>
        )}
        {investorEligible && (
          <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
            <Sparkles className="h-3 w-3" />
            Investor Eligible
          </span>
        )}
        {listing.price_change !== null && listing.price_change !== 0 && (
          <span
            className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${
              listing.price_change < 0
                ? "bg-emerald-50 text-emerald-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {listing.price_change < 0 ? (
              <TrendingDown className="h-3 w-3" />
            ) : (
              <TrendingUp className="h-3 w-3" />
            )}
            {formatCompactCurrency(Math.abs(listing.price_change))}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-600">
        <span className="flex items-center gap-1">
          <Bed className="h-3.5 w-3.5" />
          {listing.beds ?? "—"}
        </span>
        <span className="flex items-center gap-1">
          <Bath className="h-3.5 w-3.5" />
          {listing.baths ?? "—"}
        </span>
        <span className="flex items-center gap-1">
          <Ruler className="h-3.5 w-3.5" />
          {listing.sqft ? `${listing.sqft.toLocaleString()} sqft` : "—"}
        </span>
      </div>

      <div className="flex items-center gap-1 text-xs text-slate-500">
        <MapPin className="h-3.5 w-3.5" />
        {listing.city}, {listing.county} County — {listing.distance_to_water_miles.toFixed(1)} mi to{" "}
        {listing.nearest_water_point}
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1 rounded-lg bg-slate-50 p-2.5 text-xs">
        <div>
          <p className="text-slate-500">HOA / mo</p>
          <p className="font-medium text-slate-800">
            {listing.estimated_hoa_fee_monthly
              ? formatCompactCurrency(listing.estimated_hoa_fee_monthly)
              : "—"}
          </p>
        </div>
        <div>
          <p className="text-slate-500">Est. Rent / mo</p>
          <p className="font-medium text-slate-800">
            {formatCompactCurrency(listing.estimated_monthly_rent)}
          </p>
        </div>
        <div>
          <p className="text-slate-500">Gross Yield</p>
          <p className="font-medium text-slate-800">
            {formatPercent(listing.gross_rental_yield_pct)}
          </p>
        </div>
        <div>
          <p className="text-slate-500">Investor Eligibility</p>
          <p className="font-medium text-slate-800">
            {investorEligibilityLabel(listing.investor_eligibility_flag)}
          </p>
        </div>
      </div>

      {listing.builder_rate_promo && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-2.5 text-xs">
          <p className="font-semibold text-emerald-800">{listing.builder_rate_promo}</p>
          {listing.closing_cost_credit && (
            <p className="text-emerald-700">{listing.closing_cost_credit}</p>
          )}
        </div>
      )}

      <button
        onClick={() => onOpenCalculator(listing)}
        className="mt-1 flex items-center justify-center gap-1.5 rounded-lg bg-ocean-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-ocean-800"
      >
        <Calculator className="h-3.5 w-3.5" />
        Mortgage & DSCR Calculator
      </button>
    </div>
  );
}
