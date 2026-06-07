/** Validated input for `get_recording`. */
export interface GetRecordingInput {
  call_id: string;
}

/** Resolved durable recording handle. Never inline audio bytes. */
export interface GetRecordingOutput {
  recording_url: string;
  [key: string]: unknown;
}
