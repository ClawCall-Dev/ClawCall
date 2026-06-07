/** Validated input for `place_call`. */
export interface PlaceCallInput {
  to: string;
  task: string;
  voice?: 'jessica' | 'sarah' | 'chris' | 'eric';
  personality?: string;
  greeting?: string;
  bridge_number?: string;
}

/** Output of `place_call` — the non-blocking queued-call acknowledgement. */
export interface PlaceCallOutput {
  call_id: string;
  status: 'queued';
  message?: string;
  workflow: string;
}
