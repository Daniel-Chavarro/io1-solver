import type { Iteration } from "../types";

// What the professor asks per tableau: which variable enters, which leaves,
// the pivot, and any tie in the minimum ratio. On the final tableau the
// closing note (optimal / unbounded / infeasible).
const FINAL_NOTE: Record<string, string> = {
  optimal: "La fila z ya no tiene entradas negativas: ésta es la tabla óptima.",
  unbounded:
    "La columna elegida no tiene coeficientes positivos: el problema no está acotado.",
  infeasible:
    "Quedó una variable artificial en la base: el problema es infactible.",
};

interface Props {
  index: number;
  total: number;
  step: Iteration | null;
  status: string;
}

export function IterationStrip({ index, total, step, status }: Props) {
  const isInitial = index === 0 && total > 1;
  const isFinal = index === total - 1;
  return (
    <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1 text-sm">
      {isInitial && (
        <span className="rounded-sm bg-rule-wash px-1.5 py-0.5 font-sans text-xs font-medium text-ink-soft">
          tabla inicial
        </span>
      )}
      {isFinal && (
        <span className="rounded-sm bg-rule-wash px-1.5 py-0.5 font-sans text-xs font-medium text-ink-soft">
          tabla final
        </span>
      )}
      {step ? (
        step.leaving ? (
          <p>
            Entra <strong className="font-semibold text-pen">{step.entering}</strong>, sale{" "}
            <strong className="font-semibold">{step.leaving}</strong>, pivote{" "}
            <strong className="tnum font-semibold">{step.pivot}</strong>
          </p>
        ) : (
          <p className="text-pen">
            La columna <strong className="font-semibold">{step.entering}</strong> no
            tiene coeficientes positivos: el problema no está acotado.
          </p>
        )
      ) : (
        <p className="text-ink-soft">{FINAL_NOTE[status] ?? "Tabla final."}</p>
      )}
      {step?.leaving && step.ties.length > 0 && (
        <p className="text-warn">empate en la razón mínima: {step.ties.join(", ")}</p>
      )}
    </div>
  );
}
