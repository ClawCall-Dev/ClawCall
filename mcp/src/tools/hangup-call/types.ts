/** Validated input for `hangup_call`. */
export interface HangupCallInput {
  call_id: string;
}

/** Result of a (idempotent) hangup request. */
export interface HangupCallOutput {
  success: true;
  call_id: string;
  status: string;
  message: string;
}
