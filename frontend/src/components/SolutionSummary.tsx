import type { MethodResult } from "../types";
import { METHOD_NAMES } from "../types";

// Resultado final con los nombres y unidades del problema (regla del curso),
// no solo x1, x2. Los valores son strings canónicos mostrados tal cual.
export function SolutionSummary({ result }: { result: MethodResult }) {
  const sense = result.objective.sense === "max" ? "máximo" : "mínimo";
  const methodName = METHOD_NAMES[result.method] ?? result.method;
  if (result.status === "optimal") {
    return (
      <section className="space-y-3" aria-label="Solución">
        <div className="rounded-lg border border-grade/40 bg-grade-wash p-4">
          <p className="font-sans text-xs font-medium text-grade">
            Solución óptima
          </p>
          <p className="tnum font-display text-2xl font-semibold text-grade">
            Z = {result.objective.value}{" "}
            <span className="text-base font-normal">({sense})</span>
          </p>
          {result.solution.length > 0 && (
            <ul className="mt-3 flex flex-wrap gap-2">
              {result.solution.map((v) => (
                <li
                  key={v.name}
                  className="tnum rounded-md border border-grade/30 bg-paper px-3 py-1 font-display text-sm"
                >
                  {v.name} = {v.value}{" "}
                  <span className="text-ink-soft">{v.unit}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <p className="text-xs text-ink-soft">
          Resuelto con {methodName} en {result.elapsed_ms} ms.
        </p>
      </section>
    );
  }

  const verdict =
    result.status === "unbounded"
      ? {
          title: "No acotado",
          detail:
            "La función objetivo puede mejorar sin límite: falta una restricción que ponga cota a la variable que crece.",
        }
      : {
          title: "Infactible",
          detail:
            "No hay valores que cumplan todas las restricciones a la vez: alguna ≥ o = contradice a otra.",
        };

  return (
    <section className="space-y-3" aria-label="Solución">
      <div className="rounded-lg border border-pen/40 bg-pen-wash p-4">
        <h3 className="font-display text-xl font-semibold text-pen">
          {verdict.title}
        </h3>
        <p className="mt-1 text-sm">{verdict.detail}</p>
      </div>
      <p className="text-xs text-ink-soft">
        Resuelto con {methodName} en {result.elapsed_ms} ms.
      </p>
    </section>
  );
}
