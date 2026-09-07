/**
 * Client-side mirror of scraper/utils/financials.py, used by the mortgage
 * & DSCR calculator modal so users can interactively vary rate/down
 * payment/term without a round trip.
 */

export function monthlyPrincipalAndInterest(
  loanAmount: number,
  annualRatePct: number,
  termYears: number
): number {
  if (loanAmount <= 0) return 0;

  const monthlyRate = annualRatePct / 100 / 12;
  const numPayments = termYears * 12;

  if (monthlyRate === 0) {
    return round2(loanAmount / numPayments);
  }

  const payment =
    (loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments))) /
    (Math.pow(1 + monthlyRate, numPayments) - 1);

  return round2(payment);
}

export interface DebtServiceInputs {
  price: number;
  downPaymentPct: number;
  annualRatePct: number;
  termYears: number;
}

export interface DebtServiceResult {
  downPaymentAmount: number;
  loanAmount: number;
  monthlyPI: number;
}

export function computeDebtService({
  price,
  downPaymentPct,
  annualRatePct,
  termYears,
}: DebtServiceInputs): DebtServiceResult {
  const downPaymentAmount = round2(price * downPaymentPct);
  const loanAmount = round2(price - downPaymentAmount);
  const monthlyPI = monthlyPrincipalAndInterest(loanAmount, annualRatePct, termYears);
  return { downPaymentAmount, loanAmount, monthlyPI };
}

export function estimatedMonthlyTaxesInsurance(
  price: number,
  annualPctOfPrice = 0.016
): number {
  return round2((price * annualPctOfPrice) / 12);
}

export function dscr(
  monthlyRent: number | null,
  monthlyDebtService: number,
  monthlyHOA: number = 0,
  monthlyTaxesInsurance: number = 0
): number | null {
  if (!monthlyRent) return null;
  const totalObligation = monthlyDebtService + monthlyHOA + monthlyTaxesInsurance;
  if (totalObligation <= 0) return null;
  return round2(monthlyRent / totalObligation);
}

export function grossRentalYieldPct(
  monthlyRent: number | null,
  price: number
): number | null {
  if (!monthlyRent || price <= 0) return null;
  return round2(((monthlyRent * 12) / price) * 100);
}

export function parseRateStringToFloat(rateStr: string | null): number | null {
  if (!rateStr) return null;
  const match = rateStr.match(/(\d{1,2}(?:\.\d{1,3})?)/);
  if (!match) return null;
  return parseFloat(match[1]);
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
