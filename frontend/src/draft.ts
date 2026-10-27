// Immutable updates over the problem draft (docs/contracts.md section 1).
// Adding or removing a variable keeps every coefficient array in sync, so
// the invariant `len(coefficients) == len(variables)` always holds in the UI.
import type { Constraint, Problem, Sense, Variable } from "./types";
import { MAX_CONSTRAINTS, MAX_VARIABLES } from "./validation";

export function patchVariable(
  p: Problem,
  i: number,
  patch: Partial<Variable>,
): Problem {
  return {
    ...p,
    variables: p.variables.map((v, j) => (j === i ? { ...v, ...patch } : v)),
  };
}

export function patchObjectiveCoef(p: Problem, i: number, coef: string): Problem {
  return {
    ...p,
    objective: {
      ...p.objective,
      coefficients: p.objective.coefficients.map((c, j) => (j === i ? coef : c)),
    },
  };
}

export function patchConstraint(
  p: Problem,
  i: number,
  patch: Partial<Constraint>,
): Problem {
  return {
    ...p,
    constraints: p.constraints.map((c, j) => (j === i ? { ...c, ...patch } : c)),
  };
}

export function patchCoefficient(
  p: Problem,
  ci: number,
  j: number,
  coef: string,
): Problem {
  return {
    ...p,
    constraints: p.constraints.map((c, i) =>
      i === ci
        ? { ...c, coefficients: c.coefficients.map((x, k) => (k === j ? coef : x)) }
        : c,
    ),
  };
}

export function setSense(p: Problem, sense: Sense): Problem {
  return { ...p, objective: { ...p.objective, sense } };
}

export function addVariable(p: Problem): Problem {
  if (p.variables.length >= MAX_VARIABLES) return p;
  return {
    ...p,
    variables: [...p.variables, { name: "", unit: "" }],
    objective: { ...p.objective, coefficients: [...p.objective.coefficients, ""] },
    constraints: p.constraints.map((c) => ({
      ...c,
      coefficients: [...c.coefficients, ""],
    })),
  };
}

export function removeVariable(p: Problem, i: number): Problem {
  if (p.variables.length <= 1) return p;
  const drop = (xs: string[]) => xs.filter((_, j) => j !== i);
  return {
    ...p,
    variables: p.variables.filter((_, j) => j !== i),
    objective: { ...p.objective, coefficients: drop(p.objective.coefficients) },
    constraints: p.constraints.map((c) => ({ ...c, coefficients: drop(c.coefficients) })),
  };
}

export function addConstraint(p: Problem): Problem {
  if (p.constraints.length >= MAX_CONSTRAINTS) return p;
  return {
    ...p,
    constraints: [
      ...p.constraints,
      { name: "", coefficients: p.variables.map(() => ""), op: "<=", rhs: "" },
    ],
  };
}

export function removeConstraint(p: Problem, i: number): Problem {
  if (p.constraints.length <= 1) return p;
  return { ...p, constraints: p.constraints.filter((_, j) => j !== i) };
}
