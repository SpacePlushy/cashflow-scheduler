import { ExportFormat, Plan, SolveResponse } from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_SOLVER_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type");
  const isJson = contentType?.includes("application/json");
  if (!response.ok) {
    const message = isJson ? ((await response.json()) as { error?: string }).error : undefined;
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  if (!isJson) {
    throw new Error("Unexpected response from solver API");
  }
  return (await response.json()) as T;
}

export async function solvePlan(plan: Plan): Promise<SolveResponse> {
  const response = await fetch(`${API_BASE}/solve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ plan }),
  });
  return handleResponse<SolveResponse>(response);
}

export async function exportPlan(plan: Plan, format: ExportFormat): Promise<string> {
  const response = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ plan, format }),
  });
  const payload = await handleResponse<{ format: string; content: string }>(response);
  return payload.content;
}
