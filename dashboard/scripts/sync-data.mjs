// Copies the repo's data/listings.json into dashboard/public/data/ so it can
// ship as the offline/local-dev fallback bundled with the app. Run this
// whenever you want the fallback snapshot to reflect the latest scrape
// (the primary data path in production is the live NEXT_PUBLIC_DATA_URL
// fetch in lib/data.ts, which does not need this step).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");

const source = join(repoRoot, "data", "listings.json");
const destDir = join(__dirname, "..", "public", "data");
const dest = join(destDir, "listings.json");

mkdirSync(destDir, { recursive: true });
copyFileSync(source, dest);

console.log(`Synced ${source} -> ${dest}`);
