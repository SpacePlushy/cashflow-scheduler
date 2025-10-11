import { Plan, Schedule } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function solveSchedule(plan?: Plan): Promise<Schedule> {
  const response = await fetch(`${API_BASE_URL}/solve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(plan ? { plan } : {}),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(error.error || `API error: ${response.status}`);
  }

  return response.json();
}

export async function setEOD(
  day: number,
  eodAmount: number,
  plan: Plan
): Promise<Schedule> {
  const response = await fetch(`${API_BASE_URL}/set_eod`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      day,
      eod_amount: eodAmount,
      plan,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(error.error || `API error: ${response.status}`);
  }

  return response.json();
}

export async function exportSchedule(
  plan: Plan,
  format: "md" | "csv" | "json" = "md"
): Promise<{ format: string; content: string }> {
  const response = await fetch(`${API_BASE_URL}/export`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      plan,
      format,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(error.error || `API error: ${response.status}`);
  }

  return response.json();
}
