/** Validated input for `set_api_key`. */
export interface SetApiKeyInput {
  api_key: string;
}

/** Acknowledgement — the key is NEVER echoed back. */
export interface SetApiKeyOutput {
  ok: true;
}
