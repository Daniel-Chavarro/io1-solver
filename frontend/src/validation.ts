// Inline validation, mirror of docs/contracts.md section 6 / schemas.py.
// Errors are keyed per field so each input can show its own message:
//   p = nombre del problema
//   v{i} = nombre de la variable i, u{i} = unidad, o{i} = coeficiente en Z
//   c{i} = nombre de la restricción i, r{i} = RHS, a{i}-{j} = coeficiente j
import type { Problem } from "./types";

export const DECIMAL = /^-?\d+(\.\d+)?$/;
export const MAX_VARIABLES = 8;
export const MAX_CONSTRAINTS = 13;

export type ProblemErrors = Record<string, string>;

const NUMBER_MSG = "Escribe un número, como 2.5 o -40.";

export function validateProblem(problem: Problem): ProblemErrors {
  const errors: ProblemErrors = {};
  if (!problem.name.trim()) errors.p = "Ponle un nombre al problema.";

  problem.variables.forEach((v, i) => {
    if (!v.name.trim()) errors[`v${i}`] = "Toda variable necesita nombre.";
    else if (!v.unit.trim())
      errors[`u${i}`] = "Escribe la unidad (por ejemplo, lotes u horas).";
    if (!DECIMAL.test(problem.objective.coefficients[i]?.trim() ?? ""))
      errors[`o${i}`] = NUMBER_MSG;
  });

  const names = problem.variables.map((v) => v.name.trim()).filter(Boolean);
  const duplicated = new Set(
    names.filter((n, i) => names.indexOf(n) !== i),
  );
  problem.variables.forEach((v, i) => {
    if (duplicated.has(v.name.trim()))
      errors[`v${i}`] = "Hay dos variables con el mismo nombre.";
  });

  if (problem.variables.length > MAX_VARIABLES)
    errors.v0 = `Máximo ${MAX_VARIABLES} variables.`;
  if (problem.constraints.length > MAX_CONSTRAINTS)
    errors.c0 = `Máximo ${MAX_CONSTRAINTS} restricciones.`;

  problem.constraints.forEach((c, i) => {
    if (!c.name.trim()) errors[`c${i}`] = "Toda restricción necesita nombre.";
    if (!DECIMAL.test(c.rhs.trim())) errors[`r${i}`] = NUMBER_MSG;
    c.coefficients.forEach((x, j) => {
      if (!DECIMAL.test(x.trim())) errors[`a${i}-${j}`] = NUMBER_MSG;
    });
  });

  return errors;
}
