import type { Listing } from "./types";
import { parseRateStringToFloat } from "./calculations";

export interface DashboardKpis {
  totalActiveDeals: number;
  medianPricePerSqft: number | null;
  bestPromoRate: { rate: number; builder: string; rawLabel: string } | null;
  largestPriceCut: { amount: number; address: string; builder: string } | null;
}

function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0
    ? sorted[mid]
    : Math.round(((sorted[mid - 1] + sorted[mid]) / 2) * 100) / 100;
}

export function computeKpis(listings: Listing[]): DashboardKpis {
  const totalActiveDeals = listings.length;

  const pricesPerSqft = listings
    .map((l) => l.price_per_sqft)
    .filter((v): v is number => v !== null && v !== undefined);
  const medianPricePerSqft = median(pricesPerSqft);

  let bestPromoRate: DashboardKpis["bestPromoRate"] = null;
  for (const listing of listings) {
    const rate = parseRateStringToFloat(listing.builder_rate_promo);
    if (rate === null) continue;
    if (!bestPromoRate || rate < bestPromoRate.rate) {
      bestPromoRate = {
        rate,
        builder: listing.builder_name ?? "Unknown builder",
        rawLabel: listing.builder_rate_promo ?? `${rate}%`,
      };
    }
  }

  let largestPriceCut: DashboardKpis["largestPriceCut"] = null;
  for (const listing of listings) {
    if (listing.listing_status !== "price_drop" || listing.price_change === null) continue;
    if (!largestPriceCut || listing.price_change < -largestPriceCut.amount) {
      largestPriceCut = {
        amount: Math.abs(listing.price_change),
        address: listing.address ?? listing.community_name ?? "Unknown address",
        builder: listing.builder_name ?? "Unknown builder",
      };
    }
  }

  return { totalActiveDeals, medianPricePerSqft, bestPromoRate, largestPriceCut };
}
