// Thin fetch wrappers over the FastAPI backend (docs/contracts.md section 5).
// 422 bodies arrive either as {code, message} (Pydantic handler) or as
// FastAPI's {detail} (HTTPException); both are surfaced as-is in Spanish.
import type { ExampleSummary, MethodResult, Problem } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
  }
}

// One-off field read from an untyped error body: narrow with `in`, no casts.
function pickMessage(data: unknown): string | undefined {
  if (typeof data !== "object" || data === null) return undefined;
  if ("detail" in data && typeof data.detail === "string" && data.detail.trim())
    return data.detail;
  if ("message" in data && typeof data.message === "string" && data.message.trim())
    return data.message;
  return undefined;
}

async function call<T>(path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      "No se pudo conectar con el servidor. Verifica que el backend esté corriendo.",
    );
  }

  if (!res.ok) {
    let message = `El servidor respondió con error ${res.status}.`;
    try {
      const parsed: unknown = await res.json();
      const detail = pickMessage(parsed);
      if (detail) message = detail;
    } catch {
      // respuesta sin cuerpo: se conserva el mensaje genérico
    }
    throw new ApiError(message, res.status);
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

export const ejemplo = (id: string) =>
  call<{ problem: Problem }>(`/api/ejemplos/${encodeURIComponent(id)}`);
