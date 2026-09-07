"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import type { Listing } from "@/lib/types";
import { formatCompactCurrency } from "@/lib/format";

function isDeepDeal(listing: Listing): boolean {
  const hasPromo = listing.investor_eligibility_flag === "investor_eligible" && !!listing.builder_rate_promo;
  const isPriceDrop = listing.listing_status === "price_drop";
  return hasPromo || isPriceDrop;
}

export default function MapView({
  listings,
  onSelect,
}: {
  listings: Listing[];
  onSelect: (listing: Listing) => void;
}) {
  const center: [number, number] =
    listings.length > 0
      ? [
          listings.reduce((sum, l) => sum + l.latitude, 0) / listings.length,
          listings.reduce((sum, l) => sum + l.longitude, 0) / listings.length,
        ]
      : [34.5, -77.5];

  return (
    <MapContainer
      center={center}
      zoom={7}
      scrollWheelZoom={true}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {listings.map((listing) => {
        const deep = isDeepDeal(listing);
        return (
          <CircleMarker
            key={listing.id}
            center={[listing.latitude, listing.longitude]}
            radius={8}
            pathOptions={{
              color: deep ? "#059669" : "#0685d1",
              fillColor: deep ? "#10b981" : "#3fc4ff",
              fillOpacity: 0.85,
              weight: 2,
            }}
            eventHandlers={{ click: () => onSelect(listing) }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{listing.community_name ?? listing.address}</p>
                <p className="text-slate-600">{listing.builder_name}</p>
                <p className="mt-1 font-semibold text-ocean-700">
                  {formatCompactCurrency(listing.price)}
                </p>
                <p className="text-xs text-slate-500">
                  {listing.beds ?? "?"} bd / {listing.baths ?? "?"} ba
                  {listing.sqft ? ` / ${listing.sqft.toLocaleString()} sqft` : ""}
                </p>
                {listing.builder_rate_promo && (
                  <p className="mt-1 text-xs font-medium text-emerald-700">
                    {listing.builder_rate_promo}
                  </p>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
