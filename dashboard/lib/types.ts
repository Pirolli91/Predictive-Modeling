export type InvestorEligibility =
  | "primary_residence_only"
  | "investor_eligible"
  | "unspecified";

export type ListingStatus =
  | "new"
  | "price_drop"
  | "price_increase"
  | "unchanged";

export type MoveInStatus =
  | "Move-In Ready"
  | "Under Construction"
  | "To Be Built"
  | string
  | null;

export interface DebtServiceEstimate {
  down_payment_pct: number;
  down_payment_amount: number;
  loan_amount: number;
  annual_rate_pct: number;
  monthly_pi: number;
}

export interface Listing {
  id: string;
  builder_name: string | null;
  community_name: string | null;
  plan_name: string | null;
  address: string | null;
  city: string | null;
  state: string;
  zip: string | null;
  county: string | null;
  latitude: number;
  longitude: number;
  price: number;
  price_change: number | null;
  beds: number | null;
  baths: number | null;
  sqft: number | null;
  price_per_sqft: number | null;
  estimated_hoa_fee_monthly: number | null;
  estimated_completion_date: string | null;
  move_in_status: MoveInStatus;
  distance_to_water_miles: number;
  nearest_water_point: string;
  estimated_drive_minutes_to_water: number;
  builder_rate_promo: string | null;
  closing_cost_credit: string | null;
  investor_eligibility_flag: InvestorEligibility;
  raw_incentive_text: string | null;
  estimated_monthly_rent: number | null;
  gross_rental_yield_pct: number | null;
  investor_debt_service: DebtServiceEstimate;
  builder_promo_debt_service: DebtServiceEstimate | null;
  investor_dscr: number | null;
  builder_promo_dscr: number | null;
  source_name: string | null;
  source_url: string | null;
  listing_status: ListingStatus;
  first_seen: string;
  last_seen: string;
}

export interface ListingsSummary {
  generated_at: string;
  total_active_listings: number;
  new_today: number;
  price_drops_today: number;
  price_increases_today: number;
  sold_or_delisted_today: number;
}

export interface ListingsPayload {
  generated_at: string;
  price_cap: number;
  summary: ListingsSummary;
  listings: Listing[];
}

export interface FilterState {
  county: string | "all";
  maxPrice: number;
  minSqft: number;
  investorEligibleOnly: boolean;
}
