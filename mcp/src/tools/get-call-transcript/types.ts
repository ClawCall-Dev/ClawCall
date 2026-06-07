/** Validated input for `get_call_transcript`. */
export interface GetCallTranscriptInput {
  call_id: string;
}

/** A single transcript turn. `user` = callee, `assistant` = voice agent. */
export interface TranscriptTurn {
  role: 'user' | 'assistant' | 'tool' | 'system';
  text: string;
  timestamp: string;
  tool?: string;
  toolArgs?: unknown;
}

/** Full turn-by-turn transcript output. */
export interface GetCallTranscriptOutput {
  transcript: TranscriptTurn[] | null;
  [key: string]: unknown;
}
