import { useState, type FormEvent } from "react";
import type { MethodId, Op, Problem } from "../types";
import { METHOD_NAMES } from "../types";
import { MAX_CONSTRAINTS, MAX_VARIABLES, validateProblem } from "../validation";
import {
  addConstraint,
  addVariable,
  patchCoefficient,
  patchConstraint,
  patchObjectiveCoef,
  patchVariable,
  removeConstraint,
  removeVariable,
  setSense,
} from "../draft";
import { ExamplesMenu } from "./ExamplesMenu";

// Borrador en blanco: 2 variables y 2 restricciones vacías, sentido max.
// Nunca se muta: toda edición pasa por draft.ts y devuelve un Problem nuevo.
export const BLANK_DRAFT: Problem = {
  name: "",
  variables: [
    { name: "", unit: "" },
    { name: "", unit: "" },
  ],
  objective: { sense: "max", coefficients: ["", ""] },
  constraints: [
    { name: "", coefficients: ["", ""], op: "<=", rhs: "" },
    { name: "", coefficients: ["", ""], op: "<=", rhs: "" },
  ],
};

const OPS: { value: Op; label: string }[] = [
  { value: "<=", label: "≤" },
  { value: ">=", label: "≥" },
  { value: "=", label: "=" },
];

const METHOD_HINT: Record<MethodId, string> = {
  simplex:
    "Simplex solo admite restricciones ≤ con lado derecho no negativo; para ≥ o = usa Gran M.",
  big_m: "Gran M admite restricciones ≤, ≥ y =; la penalización M queda visible en las tablas.",
};

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-pen">{message}</p>;
}

interface Props {
  value: Problem;
  onChange: (p: Problem) => void;
  method: MethodId;
  onMethodChange: (m: MethodId) => void;
  onSolve: () => void;
  loading: boolean;
}

export function ProblemForm({
  value,
  onChange,
  method,
  onMethodChange,
  onSolve,
  loading,
}: Props) {
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const [submitted, setSubmitted] = useState(false);

  // Errores derivados durante el render (validación inline, espejo del
  // contrato); se muestran por campo al tocarlo o tras intentar resolver.
  const errors = validateProblem(value);
  const shown = (key: string) =>
    (submitted || touched.has(key)) ? errors[key] : undefined;
  const touch = (key: string) =>
    setTouched((prev) => (prev.has(key) ? prev : new Set(prev).add(key)));

  const dirty = JSON.stringify(value) !== JSON.stringify(BLANK_DRAFT);

  const terms = value.variables
    .map((v, i) => {
      const c = value.objective.coefficients[i]?.trim();
      return c ? `${c} · ${v.name.trim() || `x${i + 1}`}` : null;
    })
    .filter((t): t is string => t !== null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitted(true);
    if (Object.keys(errors).length > 0) {
      document.getElementById(Object.keys(errors)[0])?.focus();
      return;
    }
    onSolve();
  }

  return (
    <form onSubmit={onSubmit} noValidate className="sheet space-y-6 p-4 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-xl font-semibold">Problema</h2>
        <ExamplesMenu
          dirty={dirty}
          onLoad={(p) => {
            onChange(p);
            setSubmitted(false);
            setTouched(new Set());
          }}
        />
      </div>

      <div className="max-w-md">
        <label htmlFor="p" className="mb-1 block text-sm font-medium">
          Nombre del problema
        </label>
        <input
          id="p"
          className={`field ${shown("p") ? "field-error" : ""}`}
          value={value.name}
          onChange={(e) => onChange({ ...value, name: e.target.value })}
          onBlur={() => touch("p")}
          placeholder="Plan de producción de la panadería"
        />
        <FieldError message={shown("p")} />
      </div>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-display text-lg font-semibold">
            Variables de decisión
          </h3>
          <div
            className="flex rounded-md border border-rule-strong/50 p-0.5"
            role="radiogroup"
            aria-label="Sentido de la función objetivo"
          >
            {(["max", "min"] as const).map((s) => (
              <button
                key={s}
                type="button"
                role="radio"
                aria-checked={value.objective.sense === s}
                className={`rounded px-3 py-1 text-sm font-medium ${
                  value.objective.sense === s
                    ? "bg-ink text-paper"
                    : "text-ink-soft hover:text-ink"
                }`}
                onClick={() => onChange(setSense(value, s))}
              >
                {s === "max" ? "Maximizar" : "Minimizar"}
              </button>
            ))}
          </div>
        </div>
        {terms.length > 0 && (
          <p className="tnum font-display text-sm text-ink-soft italic">
            Z = {terms.join(" + ")}
          </p>
        )}
        <div className="grid gap-3 sm:grid-cols-2">
          {value.variables.map((v, i) => (
            <div
              key={i}
              className="rounded-md border border-rule/70 bg-white/50 p-3"
            >
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label htmlFor={`v${i}`} className="mb-0.5 block text-xs text-ink-soft">
                    Nombre
                  </label>
                  <input
                    id={`v${i}`}
                    className={`field ${shown(`v${i}`) ? "field-error" : ""}`}
                    value={v.name}
                    onChange={(e) =>
                      onChange(patchVariable(value, i, { name: e.target.value }))
                    }
                    onBlur={() => touch(`v${i}`)}
                    placeholder="pandesal"
                  />
                  <FieldError message={shown(`v${i}`)} />
                </div>
                <div>
                  <label htmlFor={`u${i}`} className="mb-0.5 block text-xs text-ink-soft">
                    Unidad
                  </label>
                  <input
                    id={`u${i}`}
                    className={`field ${shown(`u${i}`) ? "field-error" : ""}`}
                    value={v.unit}
                    onChange={(e) =>
                      onChange(patchVariable(value, i, { unit: e.target.value }))
                    }
                    onBlur={() => touch(`u${i}`)}
                    placeholder="lotes"
                  />
                  <FieldError message={shown(`u${i}`)} />
                </div>
                <div>
                  <label htmlFor={`o${i}`} className="mb-0.5 block text-xs text-ink-soft">
                    Coeficiente en Z
                  </label>
                  <input
                    id={`o${i}`}
                    className={`field tnum ${shown(`o${i}`) ? "field-error" : ""}`}
                    value={value.objective.coefficients[i] ?? ""}
                    onChange={(e) => onChange(patchObjectiveCoef(value, i, e.target.value))}
                    onBlur={() => touch(`o${i}`)}
                    placeholder="40"
                  />
                  <FieldError message={shown(`o${i}`)} />
                </div>
                <div className="flex items-end">
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={value.variables.length <= 1}
                    onClick={() => onChange(removeVariable(value, i))}
                    aria-label={`Quitar la variable ${v.name || i + 1}`}
                  >
                    Quitar
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        {value.variables.length < MAX_VARIABLES ? (
          <button
            type="button"
            className="btn btn-quiet"
            onClick={() => onChange(addVariable(value))}
          >
            Añadir variable
          </button>
        ) : (
          <p className="text-xs text-ink-soft">Máximo {MAX_VARIABLES} variables.</p>
        )}
      </section>

      <section className="space-y-3">
        <h3 className="font-display text-lg font-semibold">Restricciones</h3>
        <div className="space-y-3">
          {value.constraints.map((c, i) => (
            <div key={i} className="rounded-md border border-rule/70 bg-white/50 p-3">
              <div className="flex items-baseline justify-between gap-2">
                <label htmlFor={`c${i}`} className="text-sm font-medium">
                  Restricción {i + 1}
                </label>
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={value.constraints.length <= 1}
                  onClick={() => onChange(removeConstraint(value, i))}
                  aria-label={`Quitar la restricción ${c.name || i + 1}`}
                >
                  Quitar
                </button>
              </div>
              <input
                id={`c${i}`}
                className={`field mt-1 ${shown(`c${i}`) ? "field-error" : ""}`}
                value={c.name}
                onChange={(e) => onChange(patchConstraint(value, i, { name: e.target.value }))}
                onBlur={() => touch(`c${i}`)}
                placeholder="horas de horno"
              />
              <FieldError message={shown(`c${i}`)} />
              <div className="mt-2 flex flex-wrap items-end gap-2">
                {value.variables.map((v, j) => {
                  const label = v.name.trim() || `x${j + 1}`;
                  return (
                    <div key={j} className="w-24">
                      <label
                        htmlFor={`a${i}-${j}`}
                        className="mb-0.5 block truncate text-xs text-ink-soft"
                        title={label}
                      >
                        {label}
                      </label>
                      <input
                        id={`a${i}-${j}`}
                        className={`field tnum text-center ${shown(`a${i}-${j}`) ? "field-error" : ""}`}
                        value={c.coefficients[j] ?? ""}
                        onChange={(e) => onChange(patchCoefficient(value, i, j, e.target.value))}
                        onBlur={() => touch(`a${i}-${j}`)}
                        placeholder="1"
                      />
                      <FieldError message={shown(`a${i}-${j}`)} />
                    </div>
                  );
                })}
                <div className="w-16">
                  <label htmlFor={`op${i}`} className="mb-0.5 block text-xs text-ink-soft">
                    Operador
                  </label>
                  <select
                    id={`op${i}`}
                    className="field text-center"
                    value={c.op}
                    onChange={(e) =>
                      onChange(patchConstraint(value, i, { op: e.target.value as Op }))
                    }
                  >
                    {OPS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="w-24">
                  <label htmlFor={`r${i}`} className="mb-0.5 block text-xs text-ink-soft">
                    Lado derecho
                  </label>
                  <input
                    id={`r${i}`}
                    className={`field tnum ${shown(`r${i}`) ? "field-error" : ""}`}
                    value={c.rhs}
                    onChange={(e) => onChange(patchConstraint(value, i, { rhs: e.target.value }))}
                    onBlur={() => touch(`r${i}`)}
                    placeholder="40"
                  />
                  <FieldError message={shown(`r${i}`)} />
                </div>
              </div>
            </div>
          ))}
        </div>
        {value.constraints.length < MAX_CONSTRAINTS ? (
          <button
            type="button"
            className="btn btn-quiet"
            onClick={() => onChange(addConstraint(value))}
          >
            Añadir restricción
          </button>
        ) : (
          <p className="text-xs text-ink-soft">Máximo {MAX_CONSTRAINTS} restricciones.</p>
        )}
      </section>

      <div className="space-y-2 border-t border-rule/60 pt-4">
        <div
          className="flex rounded-md border border-rule-strong/50 p-0.5"
          role="radiogroup"
          aria-label="Método"
        >
          {(["simplex", "big_m"] as const).map((m) => (
            <button
              key={m}
              type="button"
              role="radio"
              aria-checked={method === m}
              className={`rounded px-3 py-1.5 text-sm font-medium ${
                method === m ? "bg-ink text-paper" : "text-ink-soft hover:text-ink"
              }`}
              onClick={() => onMethodChange(m)}
            >
              {METHOD_NAMES[m]}
            </button>
          ))}
        </div>
        <p className="text-xs text-ink-soft">{METHOD_HINT[method]}</p>
        <div className="flex justify-end">
          <button type="submit" className="btn btn-primary px-6" disabled={loading}>
            {loading ? "Resolviendo…" : `Resolver con ${METHOD_NAMES[method]}`}
          </button>
        </div>
      </div>
    </form>
  );
}
