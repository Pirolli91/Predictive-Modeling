"use client";

import { useMemo, useState } from "react";
import { X } from "lucide-react";
import type { Listing } from "@/lib/types";
import {
  computeDebtService,
  dscr,
  estimatedMonthlyTaxesInsurance,
  parseRateStringToFloat,
} from "@/lib/calculations";
import { formatCompactCurrency } from "@/lib/format";

const DEFAULT_INVESTOR_RATE = 7.5;
const DEFAULT_DOWN_PAYMENT_PCT = 25;
const DEFAULT_TERM_YEARS = 30;

export default function MortgageCalculatorModal({
  listing,
  onClose,
}: {
  listing: Listing;
  onClose: () => void;
}) {
  const builderRate = parseRateStringToFloat(listing.builder_rate_promo);

  const [downPaymentPct, setDownPaymentPct] = useState(DEFAULT_DOWN_PAYMENT_PCT);
  const [investorRate, setInvestorRate] = useState(DEFAULT_INVESTOR_RATE);
  const [promoRate, setPromoRate] = useState(builderRate ?? DEFAULT_INVESTOR_RATE);
  const [termYears, setTermYears] = useState<15 | 30>(DEFAULT_TERM_YEARS);
  const [monthlyRent, setMonthlyRent] = useState(listing.estimated_monthly_rent ?? 0);

  const hoa = listing.estimated_hoa_fee_monthly ?? 0;
  const taxesInsurance = estimatedMonthlyTaxesInsurance(listing.price);

  const investorScenario = useMemo(
    () =>
      computeDebtService({
        price: listing.price,
        downPaymentPct: downPaymentPct / 100,
        annualRatePct: investorRate,
        termYears,
      }),
    [listing.price, downPaymentPct, investorRate, termYears]
  );

  const promoScenario = useMemo(
    () =>
      computeDebtService({
        price: listing.price,
        downPaymentPct: downPaymentPct / 100,
        annualRatePct: promoRate,
        termYears,
      }),
    [listing.price, downPaymentPct, promoRate, termYears]
  );

  const investorTotalMonthly = investorScenario.monthlyPI + hoa + taxesInsurance;
  const promoTotalMonthly = promoScenario.monthlyPI + hoa + taxesInsurance;

  const investorDscr = dscr(monthlyRent, investorScenario.monthlyPI, hoa, taxesInsurance);
  const promoDscr = dscr(monthlyRent, promoScenario.monthlyPI, hoa, taxesInsurance);

  const investorCashflow = monthlyRent - investorTotalMonthly;
  const promoCashflow = monthlyRent - promoTotalMonthly;

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-slate-900/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white shadow-xl">
        <div className="sticky top-0 flex items-start justify-between border-b border-slate-200 bg-white p-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Mortgage & DSCR Calculator
            </h2>
            <p className="text-sm text-slate-500">
              {listing.community_name ?? listing.address} — {formatCompactCurrency(listing.price)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-5 p-4">
          <div className="grid grid-cols-2 gap-4">
            <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
              Down Payment: {downPaymentPct}%
              <input
                type="range"
                min={5}
                max={50}
                step={1}
                value={downPaymentPct}
                onChange={(e) => setDownPaymentPct(Number(e.target.value))}
                className="accent-ocean-600"
              />
            </label>

            <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
              Loan Term
              <select
                value={termYears}
                onChange={(e) => setTermYears(Number(e.target.value) as 15 | 30)}
                className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
              >
                <option value={30}>30-year fixed</option>
                <option value={15}>15-year fixed</option>
              </select>
            </label>

            <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
              Standard Investor Rate: {investorRate.toFixed(2)}%
              <input
                type="range"
                min={4}
                max={10}
                step={0.05}
                value={investorRate}
                onChange={(e) => setInvestorRate(Number(e.target.value))}
                className="accent-ocean-600"
              />
            </label>

            <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
              Builder Promo Rate: {promoRate.toFixed(2)}%
              <input
                type="range"
                min={2}
                max={10}
                step={0.05}
                value={promoRate}
                onChange={(e) => setPromoRate(Number(e.target.value))}
                className="accent-emerald-600"
              />
            </label>

            <label className="col-span-2 flex flex-col gap-1 text-xs font-medium text-slate-600">
              Estimated Gross Monthly Rent: {formatCompactCurrency(monthlyRent)}
              <input
                type="range"
                min={500}
                max={4000}
                step={25}
                value={monthlyRent}
                onChange={(e) => setMonthlyRent(Number(e.target.value))}
                className="accent-ocean-600"
              />
            </label>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <ScenarioCard
              title="Standard Investor Rate"
              rate={investorRate}
              downPayment={investorScenario.downPaymentAmount}
              loanAmount={investorScenario.loanAmount}
              monthlyPI={investorScenario.monthlyPI}
              hoa={hoa}
              taxesInsurance={taxesInsurance}
              totalMonthly={investorTotalMonthly}
              dscrValue={investorDscr}
              cashflow={investorCashflow}
              accent="border-slate-300 bg-slate-50"
            />
            <ScenarioCard
              title="Builder Promo Rate"
              rate={promoRate}
              downPayment={promoScenario.downPaymentAmount}
              loanAmount={promoScenario.loanAmount}
              monthlyPI={promoScenario.monthlyPI}
              hoa={hoa}
              taxesInsurance={taxesInsurance}
              totalMonthly={promoTotalMonthly}
              dscrValue={promoDscr}
              cashflow={promoCashflow}
              accent="border-emerald-300 bg-emerald-50"
            />
          </div>

          {listing.investor_eligibility_flag === "primary_residence_only" && (
            <p className="rounded-lg bg-amber-50 p-2.5 text-xs text-amber-800">
              Note: this listing&apos;s promotional rate terms indicate primary-residence buyers
              only. The builder promo scenario above is illustrative; investors would likely
              qualify only for the standard investor rate.
            </p>
          )}

          <p className="text-[11px] text-slate-400">
            Estimates only. Standard investor rate, taxes/insurance, and rent are configurable
            placeholders — replace with live quotes before making investment decisions.
          </p>
        </div>
      </div>
    </div>
  );
}

function ScenarioCard({
  title,
  rate,
  downPayment,
  loanAmount,
  monthlyPI,
  hoa,
  taxesInsurance,
  totalMonthly,
  dscrValue,
  cashflow,
  accent,
}: {
  title: string;
  rate: number;
  downPayment: number;
  loanAmount: number;
  monthlyPI: number;
  hoa: number;
  taxesInsurance: number;
  totalMonthly: number;
  dscrValue: number | null;
  cashflow: number;
  accent: string;
}) {
  return (
    <div className={`rounded-xl border p-3 text-xs ${accent}`}>
      <p className="mb-2 text-sm font-semibold text-slate-900">{title}</p>
      <Row label="Rate" value={`${rate.toFixed(2)}%`} />
      <Row label="Down Payment" value={formatCompactCurrency(downPayment)} />
      <Row label="Loan Amount" value={formatCompactCurrency(loanAmount)} />
      <Row label="Monthly P&I" value={formatCompactCurrency(monthlyPI)} />
      <Row label="+ HOA" value={formatCompactCurrency(hoa)} />
      <Row label="+ Tax & Insurance (est.)" value={formatCompactCurrency(taxesInsurance)} />
      <div className="my-1.5 border-t border-slate-300" />
      <Row label="Total Monthly PITIA" value={formatCompactCurrency(totalMonthly)} bold />
      <Row label="DSCR" value={dscrValue !== null ? dscrValue.toFixed(2) : "—"} bold />
      <Row
        label="Monthly Cashflow"
        value={formatCompactCurrency(cashflow)}
        bold
        positive={cashflow >= 0}
      />
    </div>
  );
}

function Row({
  label,
  value,
  bold,
  positive,
}: {
  label: string;
  value: string;
  bold?: boolean;
  positive?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-slate-600">{label}</span>
      <span
        className={`${bold ? "font-semibold" : ""} ${
          positive === true ? "text-emerald-700" : positive === false ? "text-rose-700" : "text-slate-900"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
