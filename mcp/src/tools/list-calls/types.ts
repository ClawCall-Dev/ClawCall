/** Validated input for `list_calls`. */
export interface ListCallsInput {
  limit?: number;
  direction?: 'inbound' | 'outbound';
  since?: string;
}

/** Pass-through history response from `GET /me/calls`. */
export interface ListCallsOutput {
  calls: unknown[];
  recordingWindowMinutes?: number;
  [key: string]: unknown;
}
