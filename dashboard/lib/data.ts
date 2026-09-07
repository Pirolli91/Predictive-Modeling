import type { ListingsPayload } from "./types";

/**
 * Zero-cost data decoupling: the daily GitHub Action commits fresh JSON to
 * data/listings.json in the repo, but we don't want every viewer to require
 * a Vercel/Cloudflare redeploy to see it. So in production this fetches the
 * raw GitHub URL for that file (set NEXT_PUBLIC_DATA_URL), revalidated on an
 * interval by Next's fetch cache. If that URL isn't configured (e.g. local
 * dev), it falls back to the bundled snapshot shipped in public/data.
 */
const REVALIDATE_SECONDS = 60 * 60 * 3; // 3 hours: fresh enough vs. the daily cron, free on ISR

function resolveDataUrl(): string | null {
  const configured = process.env.NEXT_PUBLIC_DATA_URL;
  if (configured && configured.trim().length > 0) {
    return configured.trim();
  }
  return null;
}

export async function getListings(): Promise<ListingsPayload> {
  const remoteUrl = resolveDataUrl();

  if (remoteUrl) {
    try {
      const res = await fetch(remoteUrl, {
        next: { revalidate: REVALIDATE_SECONDS },
      });
      if (res.ok) {
        return (await res.json()) as ListingsPayload;
      }
      console.warn(`Failed to fetch listings from ${remoteUrl}: HTTP ${res.status}`);
    } catch (err) {
      console.warn(`Failed to fetch listings from ${remoteUrl}:`, err);
    }
  }

  // Local/offline fallback: statically bundled snapshot of data/listings.json.
  // Kept in sync manually or via `npm run sync-data` (see package.json / README).
  const fallback = await import("../public/data/listings.json");
  return fallback.default as unknown as ListingsPayload;
}
