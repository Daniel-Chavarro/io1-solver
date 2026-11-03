import { useEffect, useState, type ReactNode } from "react";
import type { Comparison, MethodSummary, Problem } from "../types";
import { METHOD_NAMES } from "../types";
import { comparar } from "../api";
import { ErrorBanner } from "./ErrorBanner";

// Sección Comparación (docs/contracts.md §5, docs/frontend-plan.md §6.6):
// ejecuta Simplex y Gran M en el servidor sobre el mismo problema y muestra
// el veredicto en español, el indicador same_objective y la tabla comparativa
// de estado, iteraciones, tamaño de tabla y tiempo. `not_admissible` se
// muestra como etiqueta de estado, nunca como error.
interface Props {
  problem: Problem;
}

type Load =
  | { state: "loading" }
  | { state: "error"; message: string }
  | { state: "ready"; comparison: Comparison };

type Tone = "grade" | "warn" | "pen" | "rule";

const STATUS_META: Record<string, { label: string; tone: Tone }> = {
  optimal: { label: "Óptimo", tone: "grade" },
  not_admissible: { label: "No admisible", tone: "warn" },
  infeasible: { label: "Infactible", tone: "pen" },
  unbounded: { label: "No acotado", tone: "pen" },
  not_implemented: { label: "No implementado", tone: "rule" },
};

const METHOD_ORDER = ["simplex", "big_m", "dual_simplex"];

export function ComparisonPanel({ problem }: Props) {
  const [load, setLoad] = useState<Load>({ state: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoad({ state: "loading" });
    comparar(problem)
      .then((comparison) => alive && setLoad({ state: "ready", comparison }))
      .catch((e: unknown) =>
        alive &&
        setLoad({
          state: "error",
          message:
            e instanceof Error
              ? e.message
              : "Error inesperado al comparar los métodos.",
        }),
      );
    return () => {
      alive = false;
    };
  }, [problem, attempt]);

  return (
    <section className="sheet space-y-6 p-4 sm:p-6" aria-label="Comparación">
      <header>
        <h2 className="font-display text-xl font-semibold">Comparación</h2>
        <p className="mt-1 max-w-2xl text-sm text-ink-soft">
          Simplex, Gran M y Simplex Dual ejecutados sobre{" "}
          <span className="font-medium">{problem.name}</span>: estado final,
          tablas generadas, dimensiones del tableau y tiempo de cómputo en el
          servidor.
        </p>
      </header>

      {load.state === "loading" && (
        <p className="text-sm text-ink-soft" role="status">
          Comparando métodos…
        </p>
      )}

      {load.state === "error" && (
        <div className="space-y-2">
          <ErrorBanner
            message={load.message}
            onDismiss={() => setAttempt((n) => n + 1)}
          />
          <p className="text-xs text-ink-soft">
            Al cerrar el aviso se vuelve a intentar.
          </p>
        </div>
      )}

      {load.state === "ready" && <Report comparison={load.comparison} />}
    </section>
  );
}

function Report({ comparison }: { comparison: Comparison }) {
  const orderedKeys = [
    ...METHOD_ORDER.filter((k) => k in comparison.results),
    ...Object.keys(comparison.results).filter((k) => !METHOD_ORDER.includes(k)),
  ];
  const rows: MethodSummary[] = orderedKeys.map((k) => comparison.results[k]);

  const bannerTone: Tone =
    comparison.same_objective === true
      ? "grade"
      : comparison.same_objective === false
        ? "pen"
        : "rule";

  const bannerCls =
    bannerTone === "grade"
      ? "border-grade/40 bg-grade-wash"
      : bannerTone === "pen"
        ? "border-pen/40 bg-pen-wash"
        : "border-rule-strong/50 bg-rule-wash";

  const titleCls =
    bannerTone === "grade"
      ? "text-grade"
      : bannerTone === "pen"
        ? "text-pen"
        : "text-ink";

  return (
    <div className="space-y-6">
      <div className={`rounded-lg border p-4 ${bannerCls}`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className={`font-display text-base font-semibold ${titleCls}`}>
            Veredicto
          </h3>
          {comparison.same_objective === true && (
            <Tag tone="grade">Mismo Z óptimo</Tag>
          )}
          {comparison.same_objective === false && (
            <Tag tone="pen">Distinto Z</Tag>
          )}
          {comparison.same_objective === null && (
            <Tag tone="rule">Z no comparable</Tag>
          )}
        </div>
        <p className="mt-1.5 text-sm text-ink">{comparison.verdict}</p>
      </div>

      <section className="space-y-2">
        <h3 className="font-display text-lg font-semibold">
          Métricas por método
        </h3>
        <p className="max-w-2xl text-xs text-ink-soft">
          El conteo de tablas incluye la tabla inicial (iteración 0) más cada
          pivote realizado. El tamaño corresponde a filas de restricción ×
          columnas totales (variables + auxiliares + b<sub>j</sub>).
        </p>
        <div className="overflow-x-auto rounded-md border border-rule/70 bg-paper">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-rule-strong/60 text-left text-xs text-ink-soft">
                <th className="px-3 py-2 font-medium">Método</th>
                <th className="px-3 py-2 font-medium">Estado</th>
                <th className="px-3 py-2 text-right font-medium">Tablas</th>
                <th className="px-3 py-2 text-right font-medium">
                  Tamaño de tabla
                </th>
                <th className="px-3 py-2 text-right font-medium">
                  Tiempo (ms)
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule/60">
              {rows.map((r) => {
                const status = STATUS_META[r.status] ?? {
                  label: r.status,
                  tone: "rule" as Tone,
                };
                return (
                  <tr key={r.method}>
                    <Cell>
                      <span className="font-medium">
                        {METHOD_NAMES[r.method] ?? r.method}
                      </span>
                    </Cell>
                    <Cell>
                      <Tag tone={status.tone}>{status.label}</Tag>
                    </Cell>
                    <Cell num>{r.iterations ?? "—"}</Cell>
                    <Cell num>
                      {r.tableau_shape
                        ? r.tableau_shape.replace("x", " × ")
                        : "—"}
                    </Cell>
                    <Cell num>
                      {r.elapsed_ms != null ? `${r.elapsed_ms} ms` : "—"}
                    </Cell>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Cell({ num, children }: { num?: boolean; children: ReactNode }) {
  return (
    <td
      className={`px-3 py-2.5 ${num ? "tnum text-right font-display whitespace-nowrap" : ""}`}
    >
      {children}
    </td>
  );
}

function Tag({ tone, children }: { tone: Tone; children: ReactNode }) {
  const cls =
    tone === "grade"
      ? "border-grade/40 bg-grade-wash text-grade"
      : tone === "warn"
        ? "border-warn/40 bg-warn-wash text-warn"
        : tone === "pen"
          ? "border-pen/40 bg-pen-wash text-pen"
          : "border-rule-strong/50 bg-rule-wash text-ink-soft";
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${cls}`}
    >
      {children}
    </span>
  );
}
