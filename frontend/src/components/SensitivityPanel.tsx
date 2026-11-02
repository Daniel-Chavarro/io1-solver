import { useEffect, useState, type ReactNode } from "react";
import type { MethodId, Problem, SensitivityReport } from "../types";
import { METHOD_NAMES } from "../types";
import { sensibilidad } from "../api";
import { ErrorBanner } from "./ErrorBanner";

// Sección Sensibilidad (docs/contracts.md §4): precios sombra, costos
// reducidos y rangos de c_j y b_i sobre el problema ya resuelto. El backend
// re-resuelve y entrega todo como strings y frases en español; aquí solo se
// muestra. Lo único que se traduce es "-inf"/"+inf" al símbolo ∞.
interface Props {
  problem: Problem;
  method: MethodId;
}

type Load =
  | { state: "loading" }
  | { state: "error"; message: string }
  | { state: "ready"; report: SensitivityReport };

const INF: Record<string, string> = { "-inf": "−∞", "+inf": "+∞" };
const bound = (s: string) => INF[s] ?? s;

export function SensitivityPanel({ problem, method }: Props) {
  const [load, setLoad] = useState<Load>({ state: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoad({ state: "loading" });
    sensibilidad(method, problem)
      .then((report) => alive && setLoad({ state: "ready", report }))
      .catch((e: unknown) =>
        alive &&
        setLoad({
          state: "error",
          message:
            e instanceof Error ? e.message : "Error inesperado al calcular la sensibilidad.",
        }),
      );
    return () => {
      alive = false;
    };
  }, [problem, method, attempt]);

  return (
    <section className="sheet space-y-6 p-4 sm:p-6" aria-label="Sensibilidad">
      <header>
        <h2 className="font-display text-xl font-semibold">Sensibilidad</h2>
        <p className="mt-1 max-w-2xl text-sm text-ink-soft">
          Sobre la tabla óptima de <span className="font-medium">{problem.name}</span>{" "}
          ({METHOD_NAMES[method]}): cuánto vale cada recurso, cuánto le falta a
          cada variable para entrar y entre qué valores el plan óptimo se mantiene.
        </p>
      </header>

      {load.state === "loading" && (
        <p className="text-sm text-ink-soft" role="status">
          Calculando sensibilidad…
        </p>
      )}

      {load.state === "error" && (
        <div className="space-y-2">
          <ErrorBanner
            message={load.message}
            onDismiss={() => setAttempt((n) => n + 1)}
          />
          <p className="text-xs text-ink-soft">Al cerrar el aviso se vuelve a intentar.</p>
        </div>
      )}

      {load.state === "ready" && <Report report={load.report} />}
    </section>
  );
}

function Report({ report }: { report: SensitivityReport }) {
  return (
    <div className="space-y-8">
      <Block
        title="Precios sombra"
        hint="Cambio de Z por cada unidad adicional del lado derecho de la restricción."
        empty={report.shadow_prices.length === 0}
        head={[["Restricción"], ["Precio sombra", true], ["Estado"]]}
      >
        {report.shadow_prices.map((s) => (
          <Row key={s.constraint} phrase={s.phrase}>
            <Cell>
              {s.constraint} <Unit>{s.unit}</Unit>
            </Cell>
            <Cell num>{s.value}</Cell>
            <Cell>
              {s.binding ? (
                <Tag tone="pen">Activa · sin holgura</Tag>
              ) : (
                <Tag tone="grade">Con holgura</Tag>
              )}
            </Cell>
          </Row>
        ))}
      </Block>

      <Block
        title="Costos reducidos"
        hint="Cuánto debe mejorar el coeficiente de una variable no básica para que convenga producirla."
        empty={report.reduced_costs.length === 0}
        emptyText="Todas las variables de decisión son básicas: no hay costos reducidos que reportar."
        head={[["Variable"], ["Costo reducido", true]]}
      >
        {report.reduced_costs.map((r) => (
          <Row key={r.variable} phrase={r.phrase}>
            <Cell>
              {r.variable} <Unit>{r.unit}</Unit>
            </Cell>
            <Cell num>{r.value}</Cell>
          </Row>
        ))}
      </Block>

      <Block
        title={
          <>
            Rangos de los coeficientes c<sub>j</sub>
          </>
        }
        hint="Mientras cada coeficiente de la función objetivo quede en su rango (uno a la vez), la solución óptima no cambia."
        empty={report.objective_ranges.length === 0}
        head={[["Variable"], ["Actual", true], ["Mínimo", true], ["Máximo", true]]}
      >
        {report.objective_ranges.map((r) => (
          <Row key={r.variable} phrase={r.phrase}>
            <Cell>{r.variable}</Cell>
            <Cell num>{r.current}</Cell>
            <Cell num>{bound(r.range[0])}</Cell>
            <Cell num>{bound(r.range[1])}</Cell>
          </Row>
        ))}
      </Block>

      <Block
        title={
          <>
            Rangos de los lados derechos b<sub>i</sub>
          </>
        }
        hint="Mientras cada lado derecho quede en su rango (uno a la vez), la base óptima y los precios sombra se mantienen."
        empty={report.rhs_ranges.length === 0}
        head={[["Restricción"], ["Actual", true], ["Mínimo", true], ["Máximo", true]]}
      >
        {report.rhs_ranges.map((r) => (
          <Row key={r.constraint} phrase={r.phrase}>
            <Cell>{r.constraint}</Cell>
            <Cell num>{r.current}</Cell>
            <Cell num>{bound(r.range[0])}</Cell>
            <Cell num>{bound(r.range[1])}</Cell>
          </Row>
        ))}
      </Block>
    </div>
  );
}

function Block({
  title,
  hint,
  head,
  empty,
  emptyText = "Sin datos para esta sección.",
  children,
}: {
  title: ReactNode;
  hint: string;
  head: [label: string, numeric?: boolean][];
  empty: boolean;
  emptyText?: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-2">
      <h3 className="font-display text-lg font-semibold">{title}</h3>
      <p className="max-w-2xl text-xs text-ink-soft">{hint}</p>
      {empty ? (
        <p className="text-sm text-ink-soft">{emptyText}</p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-rule/70 bg-paper">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-rule-strong/60 text-left text-xs text-ink-soft">
                {head.map(([label, numeric]) => (
                  <th
                    key={label}
                    className={`px-3 py-2 font-medium ${numeric ? "text-right" : ""}`}
                  >
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            {children}
          </table>
        </div>
      )}
    </section>
  );
}

// Cada entrada ocupa dos filas: los datos y, debajo, su frase interpretativa
// tal cual llega del backend.
function Row({ phrase, children }: { phrase: string; children: ReactNode }) {
  return (
    <tbody className="border-b border-rule/60 last:border-b-0">
      <tr>{children}</tr>
      <tr>
        <td colSpan={99} className="px-3 pb-2.5 text-sm text-ink-soft italic">
          {phrase}
        </td>
      </tr>
    </tbody>
  );
}

function Cell({ num, children }: { num?: boolean; children: ReactNode }) {
  return (
    <td
      className={`px-3 pt-2.5 pb-1 ${num ? "tnum text-right font-display whitespace-nowrap" : ""}`}
    >
      {children}
    </td>
  );
}

function Unit({ children }: { children: ReactNode }) {
  return children ? <span className="text-xs text-ink-soft">({children})</span> : null;
}

function Tag({ tone, children }: { tone: "pen" | "grade"; children: ReactNode }) {
  const cls =
    tone === "pen"
      ? "border-pen/40 bg-pen-wash text-pen"
      : "border-grade/40 bg-grade-wash text-grade";
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${cls}`}>
      {children}
    </span>
  );
}
