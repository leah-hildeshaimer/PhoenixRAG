import type { ChatRequest, ChatResponse } from "../types/chat";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function sendChatMessage(
  question: string
): Promise<ChatResponse> {
  const requestBody: ChatRequest = {
    question,
  };

  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    throw new Error(
      `Chat request failed with status ${response.status}`
    );
  }

  const data: ChatResponse = await response.json();

  return data;
}