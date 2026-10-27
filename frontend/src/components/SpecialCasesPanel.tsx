import type { SpecialCase } from "../types";

// Vocabulario del curso (GLOSSARY.md): cada tipo de caso especial con su
// nombre canónico en español; el detalle ya llega como frase en español.
const CASE_LABEL: Record<string, string> = {
  degenerate_pivot: "Degeneración",
  alternative_optima: "Óptimos alternativos",
  unbounded: "No acotado",
  infeasible: "Infactible",
  normalized_constraint: "Restricción normalizada",
};

export function SpecialCasesPanel({ cases }: { cases: SpecialCase[] }) {
  if (cases.length === 0) return null;
  return (
    <section
      className="rounded-lg border border-warn/40 bg-warn-wash p-4"
      aria-label="Casos especiales"
    >
      <h3 className="font-display text-base font-semibold text-warn">
        Casos especiales
      </h3>
      <ul className="mt-2 space-y-1.5">
        {cases.map((c, i) => (
          <li key={i} className="text-sm">
            <span className="font-medium text-warn">
              {CASE_LABEL[c.type] ?? c.type}
              {c.iteration != null && ` (iteración ${c.iteration})`}:
            </span>{" "}
            {c.detail}
          </li>
        ))}
      </ul>
    </section>
  );
}
