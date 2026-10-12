import { useEffect, useState } from "react";
import { ejemplo, ejemplos } from "../api";
import type { ExampleSummary, Problem } from "../types";

const KIND_LABEL: Record<string, string> = {
  real: "caso real",
  infeasible: "caso especial",
  test: "prueba",
};

// Dropdown con los ejemplos precargados del backend (GET /api/ejemplos).
// Si el formulario ya tiene datos escritos, pide confirmación antes de
// reemplazarlos (F15 del plan del frontend).
export function ExamplesMenu({
  dirty,
  onLoad,
}: {
  dirty: boolean;
  onLoad: (problem: Problem) => void;
}) {
  const [open, setOpen] = useState(false);
  const [summaries, setSummaries] = useState<ExampleSummary[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<ExampleSummary | null>(null);

  useEffect(() => {
    if (!open || summaries !== null || loading) return;
    setLoading(true);
    ejemplos()
      .then((list) => setSummaries(list))
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Error al cargar los ejemplos."),
      )
      .finally(() => setLoading(false));
  }, [open, summaries, loading]);

  async function load(ex: ExampleSummary) {
    setPending(null);
    setOpen(false);
    try {
      const { problem } = await ejemplo(ex.id);
      onLoad(problem);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar el ejemplo.");
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        className="btn btn-quiet"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        Cargar ejemplo
      </button>
      {open && (
        <>
          <button
            type="button"
            aria-hidden
            tabIndex={-1}
            className="fixed inset-0 z-20 cursor-default"
            onClick={() => {
              setOpen(false);
              setPending(null);
            }}
          />
          <div className="absolute right-0 z-30 mt-2 w-80 rounded-lg border border-rule/70 bg-paper p-3 shadow-md">
            {loading && <p className="px-1 text-sm text-ink-soft">Cargando ejemplos…</p>}
            {error && <p className="px-1 text-sm text-pen">{error}</p>}
            {summaries && !pending && (
              <ul className="space-y-1">
                {summaries.map((ex) => (
                  <li key={ex.id}>
                    <button
                      type="button"
                      className="block w-full rounded-md px-2 py-2 text-left hover:bg-rule-wash"
                      onClick={() => (dirty ? setPending(ex) : void load(ex))}
                    >
                      <span className="text-sm font-medium">{ex.name}</span>
                      <span className="ml-2 font-sans text-xs text-ink-soft">
                        {KIND_LABEL[ex.kind] ?? ex.kind}
                      </span>
                      <p className="mt-0.5 text-xs text-ink-soft">{ex.description}</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {pending && (
              <div className="rounded-md border border-warn/40 bg-warn-wash p-3">
                <p className="text-sm">
                  «{pending.name}» reemplaza el problema que estás escribiendo.
                </p>
                <div className="mt-2 flex gap-2">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => void load(pending)}
                  >
                    Cargar de todas formas
                  </button>
                  <button
                    type="button"
                    className="btn btn-quiet"
                    onClick={() => setPending(null)}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
