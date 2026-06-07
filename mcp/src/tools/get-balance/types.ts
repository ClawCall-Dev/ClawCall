/** Validated input for `get_balance` — none. */
export interface GetBalanceInput {}

/** Account/balance status. `balance_seconds` is folded from response headers. */
export interface GetBalanceOutput {
  balance_seconds?: number;
  balance_minutes?: number;
  tier?: string;
  [key: string]: unknown;
}
