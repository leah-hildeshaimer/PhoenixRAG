import type { CompassTurnRequest, CompassTurnResponse } from "../types/compass";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function sendCompassTurn(
  request: CompassTurnRequest,
): Promise<CompassTurnResponse> {
  const response = await fetch(`${API_BASE_URL}/api/compass/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Compass API returned status ${response.status}`);
  }

  const body: CompassTurnResponse = await response.json();
  if (
    !body ||
    !["question", "answer", "insufficient_evidence"].includes(body.kind) ||
    typeof body.message !== "string" ||
    !Array.isArray(body.choices) ||
    !Array.isArray(body.sources) ||
    !body.state
  ) {
    throw new Error("Invalid Compass response");
  }
  return body;
}
