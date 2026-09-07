import { getListings } from "@/lib/data";
import DashboardClient from "@/components/DashboardClient";

export const revalidate = 10800; // 3 hours, matches lib/data.ts's ISR window

export default async function Home() {
  const data = await getListings();
  return <DashboardClient data={data} />;
}
