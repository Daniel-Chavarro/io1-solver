import type { ExampleSummary, MethodResult, Problem } from "./types";

async function call<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let message = `Error HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail || data?.message) message = data.detail ?? data.message;
    } catch {
      // keep default message
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export const resolver = (method: string, problem: Problem) =>
  call<MethodResult>("/api/resolver", { method, problem });

export const sensibilidad = (method: string, problem: Problem) =>
  call<unknown>("/api/sensibilidad", { method, problem });

export const comparar = (problem: Problem) =>
  call<unknown>("/api/comparar", { problem });

export const ejemplos = () => call<ExampleSummary[]>("/api/ejemplos");
