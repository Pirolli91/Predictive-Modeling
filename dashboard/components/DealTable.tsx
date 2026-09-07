"use client";

import { Calculator } from "lucide-react";
import type { Listing } from "@/lib/types";
import { formatCompactCurrency, formatPercent, investorEligibilityLabel } from "@/lib/format";

export default function DealTable({
  listings,
  onOpenCalculator,
}: {
  listings: Listing[];
  onOpenCalculator: (listing: Listing) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[900px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-3 py-2.5">Community / Builder</th>
            <th className="px-3 py-2.5">County</th>
            <th className="px-3 py-2.5">Price</th>
            <th className="px-3 py-2.5">Beds/Baths</th>
            <th className="px-3 py-2.5">SqFt</th>
            <th className="px-3 py-2.5">HOA</th>
            <th className="px-3 py-2.5">Promo Rate</th>
            <th className="px-3 py-2.5">Investor Eligibility</th>
            <th className="px-3 py-2.5">Yield</th>
            <th className="px-3 py-2.5"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {listings.map((listing) => (
            <tr key={listing.id} className="hover:bg-slate-50">
              <td className="px-3 py-2.5">
                <p className="font-medium text-slate-900">
                  {listing.community_name ?? listing.address ?? "—"}
                </p>
                <p className="text-xs text-slate-500">{listing.builder_name}</p>
              </td>
              <td className="px-3 py-2.5 text-slate-700">{listing.county}</td>
              <td className="px-3 py-2.5">
                <span className="font-semibold text-ocean-700">
                  {formatCompactCurrency(listing.price)}
                </span>
                {listing.price_change !== null && listing.price_change !== 0 && (
                  <span
                    className={`ml-1.5 text-xs ${
                      listing.price_change < 0 ? "text-emerald-600" : "text-amber-600"
                    }`}
                  >
                    {listing.price_change < 0 ? "▼" : "▲"}{" "}
                    {formatCompactCurrency(Math.abs(listing.price_change))}
                  </span>
                )}
              </td>
              <td className="px-3 py-2.5 text-slate-700">
                {listing.beds ?? "—"} / {listing.baths ?? "—"}
              </td>
              <td className="px-3 py-2.5 text-slate-700">
                {listing.sqft ? listing.sqft.toLocaleString() : "—"}
              </td>
              <td className="px-3 py-2.5 text-slate-700">
                {formatCompactCurrency(listing.estimated_hoa_fee_monthly)}
              </td>
              <td className="px-3 py-2.5 text-slate-700">
                {listing.builder_rate_promo ?? "—"}
              </td>
              <td className="px-3 py-2.5">
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                    listing.investor_eligibility_flag === "investor_eligible"
                      ? "bg-emerald-100 text-emerald-800"
                      : listing.investor_eligibility_flag === "primary_residence_only"
                      ? "bg-rose-100 text-rose-800"
                      : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {investorEligibilityLabel(listing.investor_eligibility_flag)}
                </span>
              </td>
              <td className="px-3 py-2.5 text-slate-700">
                {formatPercent(listing.gross_rental_yield_pct)}
              </td>
              <td className="px-3 py-2.5">
                <button
                  onClick={() => onOpenCalculator(listing)}
                  className="flex items-center gap-1 rounded-lg bg-ocean-700 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-ocean-800"
                >
                  <Calculator className="h-3.5 w-3.5" />
                  Calc
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
