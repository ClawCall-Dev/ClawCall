/** Validated input for `place_call_and_wait`. */
export interface PlaceCallAndWaitInput {
  to: string;
  task: string;
  voice?: 'jessica' | 'sarah' | 'chris' | 'eric';
  personality?: string;
  greeting?: string;
  bridge_number?: string;
  max_wait_seconds?: number;
}

/** Returned when the call did not finalize within the wait budget. */
export interface PlaceCallStillRunning {
  still_running: true;
  call_id: string;
  last_lifecycle: string;
  hint: string;
}
