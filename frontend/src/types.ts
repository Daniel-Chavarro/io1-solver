// Mirror of backend/src/solver/schemas.py (docs/contracts.md). Numbers are
// always decimal strings rendered as-is; the frontend never computes.
export type Sense = "max" | "min";
export type Op = "<=" | ">=" | "=";
export type MethodId = "simplex" | "big_m";

export const METHOD_NAMES: Record<string, string> = {
  simplex: "Simplex",
  big_m: "Gran M",
};
export interface Variable { name: string; unit: string }
export interface Constraint { name: string; coefficients: string[]; op: Op; rhs: string }
export interface Objective { sense: Sense; coefficients: string[] }
export interface Problem { name: string; variables: Variable[]; objective: Objective; constraints: Constraint[] }

export interface TableauRow { basic: string; cells: string[] }
export interface TableauData { columns: string[]; rows: TableauRow[] }

export interface Iteration {
  number: number;
  tableau: TableauData;
  entering: string | null;
  leaving: string | null;
  pivot: string | null;
  ratios: string[];
  ties: string[];
}

export type SpecialCaseType =
  | "degenerate_pivot"
  | "alternative_optima"
  | "unbounded"
  | "infeasible"
  | "normalized_constraint";

export interface SpecialCase { type: string; iteration: number | null; detail: string }
export interface VariableValue { name: string; unit: string; value: string }

export interface MethodResult {
  method: string;
  status: string;
  solution: VariableValue[];
  objective: { sense: Sense; value: string };
  special_cases: SpecialCase[];
  iterations: Iteration[];
  final_table: TableauData;
  elapsed_ms: number;
}

export interface ExampleSummary { id: string; name: string; description: string; kind: string }
