/** Validated input for `get_call`. */
export interface GetCallInput {
  call_id: string;
}

/**
 * Presented view of a call. In-flight carries lifecycle + a cheap transcript
 * tail; terminal adds outcome/talk_seconds/recording_url. Shape is owned by
 * `presentGetCall`; this is the minimal contract callers rely on.
 */
export interface GetCallView {
  id: string;
  lifecycle: string;
  [key: string]: unknown;
}
