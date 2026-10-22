import type { Source } from "./chat";

export interface CompassState {
  topic: string;
  goal: string;
  asked_questions: string[];
  clarification_count: number;
}

export interface CompassHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export interface CompassTurnRequest {
  message: string;
  state: CompassState;
  history: CompassHistoryItem[];
}

export interface CompassTurnResponse {
  kind: "question" | "answer" | "insufficient_evidence";
  message: string;
  choices: string[];
  state: CompassState;
  sources: Source[];
}

export function emptyCompassState(): CompassState {
  return { topic: "", goal: "", asked_questions: [], clarification_count: 0 };
}
