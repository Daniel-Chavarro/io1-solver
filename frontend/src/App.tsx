import { useState } from "react";
import type { MethodId, MethodResult, Problem } from "./types";
import { METHOD_NAMES } from "./types";
import { resolver } from "./api";
import { MethodTabs, type TabId } from "./components/MethodTabs";
import { ProblemForm, BLANK_DRAFT } from "./components/ProblemForm";
import { ErrorBanner } from "./components/ErrorBanner";
import { SolutionSummary } from "./components/SolutionSummary";
import { SpecialCasesPanel } from "./components/SpecialCasesPanel";
import { Stepper } from "./components/Stepper";

interface Solved {
  problem: Problem;
  method: MethodId;
  result: MethodResult;
}

export default function App() {
  const [tab, setTab] = useState<TabId>("resolver");
  const [draft, setDraft] = useState<Problem>(BLANK_DRAFT);
  const [method, setMethod] = useState<MethodId>("simplex");
  const [editing, setEditing] = useState(true);
  const [solved, setSolved] = useState<Solved | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [solveId, setSolveId] = useState(0);

  async function solve() {
    setLoading(true);
    setError(null);
    try {
      const result = await resolver(method, draft);
      setSolved({ problem: draft, method, result });
      setEditing(false);
      setSolveId((n) => n + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error inesperado al resolver.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header>
        <div className="mx-auto max-w-6xl px-4 pt-10 pb-6 sm:px-6">
          <h1 className="font-display text-3xl font-bold sm:text-4xl">
            Solver de programación lineal
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-ink-soft sm:text-base">
            Simplex y Gran M paso a paso, con aritmética exacta. Escribe tu
            problema o carga un ejemplo y sigue cada tabla, pivote a pivote.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 pb-16 sm:px-6">
        <MethodTabs value={tab} onChange={setTab} />

        {tab === "resolver" && (
          <div className="space-y-6">
            {editing ? (
              <ProblemForm
                value={draft}
                onChange={setDraft}
                method={method}
                onMethodChange={setMethod}
                onSolve={() => void solve()}
                loading={loading}
              />
            ) : (
              solved && <SolvedBar solved={solved} onEdit={() => setEditing(true)} />
            )}

            {error && (
              <ErrorBanner message={error} onDismiss={() => setError(null)} />
            )}

            {solved && (
              <section className="sheet space-y-6 p-4 sm:p-6" aria-label="Resultados">
                <SolutionSummary result={solved.result} />
                <SpecialCasesPanel cases={solved.result.special_cases} />
                <Stepper
                  key={solveId}
                  iterations={solved.result.iterations}
                  status={solved.result.status}
                />
              </section>
            )}
          </div>
        )}

        {tab === "comparar" && (
          <section className="sheet space-y-2 p-6">
            <h2 className="font-display text-xl font-semibold">Comparación</h2>
            <p className="max-w-xl text-sm text-ink-soft">
              Correrá Simplex y Gran M sobre el mismo problema y comparará
              iteraciones, tiempo y valor de Z. Disponible en la entrega final.
            </p>
          </section>
        )}

        {tab === "sensibilidad" && (
          <section className="sheet space-y-2 p-6">
            <h2 className="font-display text-xl font-semibold">Sensibilidad</h2>
            <p className="max-w-xl text-sm text-ink-soft">
              Precios sombra, costos reducidos y rangos de c<sub>j</sub> y
              b<sub>i</sub> sobre el problema resuelto, con su interpretación.
              Disponible en la entrega final.
            </p>
          </section>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 text-xs text-ink-soft sm:px-6">
        Investigación de Operaciones 1, Grupo 3. Los problemas se escriben en
        la interfaz: ningún dato va dentro del código.
      </footer>
    </div>
  );
}

function SolvedBar({
  solved,
  onEdit,
}: {
  solved: Solved;
  onEdit: () => void;
}) {
  const { problem, method } = solved;
  const sense = problem.objective.sense === "max" ? "maximizar" : "minimizar";
  return (
    <section className="sheet flex flex-wrap items-center justify-between gap-3 p-4">
      <p className="text-sm">
        <span className="font-display text-base font-semibold">{problem.name}</span>{" "}
        <span className="text-ink-soft">
          ({problem.variables.length} variables,{" "}
          {problem.constraints.length} restricciones, {sense}), resuelto con{" "}
          {METHOD_NAMES[method]}.
        </span>
      </p>
      <button type="button" className="btn btn-quiet" onClick={onEdit}>
        Editar problema
      </button>
    </section>
  );
}
