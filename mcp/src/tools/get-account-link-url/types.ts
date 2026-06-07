/** Validated input for `get_account_link_url` — none. */
export interface GetAccountLinkUrlInput {}

/** Either the browser sign-in link, or guidance when no key is saved yet. */
export interface GetAccountLinkUrlOutput {
  url?: string;
  message?: string;
}
