import { useState } from "react";
import type { Iteration } from "../types";
import { IterationStrip } from "./IterationStrip";
import { TableauTable } from "./TableauTable";

// Stepper over MethodResult.iterations. Each view pairs a tableau with the
// decision taken on it: iterations[i+1] carries the entering/leaving/pivot
// and ratios computed from iterations[i]. "Ver todas" stacks every view.
export function Stepper({
  iterations,
  status,
}: {
  iterations: Iteration[];
  status: string;
}) {
  const [index, setIndex] = useState(0);
  const [showAll, setShowAll] = useState(false);
  const total = iterations.length;
  if (total === 0) return null;

  const views = showAll ? iterations.map((_, i) => i) : [index];

  return (
    <section className="space-y-4" aria-label="Paso a paso">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="btn btn-quiet"
          disabled={showAll || index === 0}
          onClick={() => setIndex(index - 1)}
        >
          Tabla anterior
        </button>
        <span className="tnum font-display text-sm font-semibold">
          Tabla {index + 1} de {total}
        </span>
        <button
          type="button"
          className="btn btn-quiet"
          disabled={showAll || index === total - 1}
          onClick={() => setIndex(index + 1)}
        >
          Tabla siguiente
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          aria-pressed={showAll}
          onClick={() => setShowAll(!showAll)}
        >
          {showAll ? "Ver una a la vez" : "Ver todas las tablas"}
        </button>
      </div>
      <div className={showAll ? "space-y-6" : "space-y-2"}>
        {views.map((i) => (
          <div key={i} className="space-y-2">
            <IterationStrip
              index={i}
              total={total}
              step={iterations[i + 1] ?? null}
              status={status}
            />
            <TableauTable
              tableau={iterations[i].tableau}
              entering={iterations[i + 1]?.entering ?? null}
              leaving={iterations[i + 1]?.leaving ?? null}
              ratios={iterations[i + 1]?.ratios ?? null}
              ties={iterations[i + 1]?.ties ?? null}
            />
          </div>
        ))}
      </div>
    </section>
  );
}
