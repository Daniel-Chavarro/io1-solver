// TODO(P2 - Dizast3r, issue #7): dynamic form per docs/contracts.md section 1
// (vars/restraints with names+units, all-<= warnings for simplex, 422 handling,
// example loader via api.ts -> ejemplos()).
export function ProblemForm() {
  return (
    <form className="mt-6 space-y-4" onSubmit={(e) => e.preventDefault()}>
      <p className="text-sm text-slate-500">
        Formulario del problema (variables, objetivo, restricciones) — TODO, ver issues.
      </p>
    </form>
  );
}
