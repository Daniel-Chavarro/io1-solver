"""FastAPI app - routing/plumbing only. Method logic lives in methods/ and
engine/ (contracts sections 2-5). Serves frontend/dist when present (README
ruta A).
"""
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .methods import REGISTRY, MethodNotAdmissibleError
from .methods.simplex import uses_equivalent_transform
from .schemas import Comparison, ComparisonRequest, MethodSummary, Problem, ResolverRequest, SensitivityRequest
from .sensitivity import SensitivityNotAvailableError, analyze

app = FastAPI(title="io1-solver", version="0.1.0")

EXAMPLES_DIR = Path(
    os.environ.get("SOLVER_EXAMPLES_DIR", Path(__file__).resolve().parents[3] / "examples")
)


# Codes raised by schemas.py validators (pydantic error `type` == API code).
_VALIDATION_CODES = {"INVALID_NUMBER", "EMPTY_FIELD", "DUPLICATE_NAME",
                     "SIZE_LIMIT", "INVALID_INPUT"}


def _error(status: int, code: str, message: str) -> JSONResponse:
    """Every bad-data answer has the same shape: {code, message}, in Spanish."""
    return JSONResponse(status_code=status, content={"code": code, "message": message})


@app.exception_handler(RequestValidationError)
async def _validation_handler(_req, exc: RequestValidationError):
    errors = exc.errors()
    err = errors[0] if errors else {}
    kind = err.get("type", "")
    where = ".".join(str(p) for p in err.get("loc", ()) if p != "body")

    if kind in _VALIDATION_CODES:
        return _error(422, kind, err["msg"])
    if kind == "missing":
        return _error(422, "EMPTY_FIELD", f"Falta el campo obligatorio '{where}'")
    if kind == "json_invalid":
        return _error(422, "INVALID_INPUT", "El cuerpo de la peticion no es un JSON valido")
    return _error(422, "INVALID_INPUT",
                  f"Dato invalido en '{where}'" if where else "Datos invalidos")


@app.get("/health")
def health():
    return {"status": "ok"}


def _example_files():
    if not EXAMPLES_DIR.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(EXAMPLES_DIR.glob("*.json"))]


@app.get("/api/ejemplos")
def list_examples():
    return [
        {"id": d["id"], "name": d["name"],
         "description": d.get("description", ""), "kind": d["kind"]}
        for d in _example_files()
    ]


@app.get("/api/ejemplos/{example_id}")
def get_example(example_id: str):
    for d in _example_files():
        if d["id"] == example_id:
            return {"problem": d["problem"]}
    raise HTTPException(status_code=404, detail="Ejemplo no encontrado")


def _run_method(method_id: str, problem: Problem):
    method = REGISTRY.get(method_id)
    if method is None:
        return _error(422, "INVALID_INPUT", f"Metodo desconocido: '{method_id}'")
    t0 = time.perf_counter()  # elapsed_ms covers build + solve + interpret (method.run)
    try:
        result = method.run(problem)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail=f"El metodo '{method_id}' aun no esta implementado (ver issues)")
    except MethodNotAdmissibleError as exc:
        return _error(422, "METHOD_NOT_ADMISSIBLE", str(exc))
    result.elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
    return result


@app.post("/api/resolver")
def resolver(req: ResolverRequest):
    return _run_method(req.method, req.problem)


@app.post("/api/sensibilidad")
def sensibilidad(req: SensitivityRequest):
    if req.method not in REGISTRY:
        return _error(422, "INVALID_INPUT", f"Metodo desconocido: '{req.method}'")
    try:
        return analyze(req.problem, REGISTRY[req.method])
    except MethodNotAdmissibleError as exc:
        return _error(422, "METHOD_NOT_ADMISSIBLE", str(exc))
    except SensitivityNotAvailableError as exc:
        return _error(422, "INVALID_INPUT", str(exc))


def _comparison_verdict(
    results: dict[str, MethodSummary],
    z_values: dict[str, str],
    same_objective: bool | None,
    used_transform: bool = False,
) -> str:
    if any(r.status == "unbounded" for r in results.values()):
        return "El problema no está acotado."
    if any(r.status == "infeasible" for r in results.values()):
        return "El problema no tiene solución factible (infactible)."

    s = results.get("simplex")
    b = results.get("big_m")
    d = results.get("dual_simplex")
    if s is None or b is None:
        return "Comparación disponible cuando ambos métodos estén registrados."

    if s.status == "optimal" and b.status == "optimal":
        z_s = z_values.get("simplex", "")
        z_b = z_values.get("big_m", "")
        if same_objective:
            if not used_transform:
                return (
                    f"Ambos métodos alcanzaron el mismo óptimo (Z = {z_s}) en "
                    f"{s.iterations} tablas ({s.tableau_shape}); no se requirió transformación "
                    f"al problema equivalente (todas las restricciones son ≤ con RHS ≥ 0) y "
                    f"Gran M no requirió variables artificiales, por lo que conviene Simplex por simplicidad."
                )
            return (
                f"Ambos métodos alcanzaron el mismo óptimo (Z = {z_s}): "
                f"Simplex usó transformación al problema equivalente por cambio de variables "
                f"en {s.iterations} tablas ({s.tableau_shape}, {s.elapsed_ms} ms) y "
                f"Gran M usó variables artificiales en {b.iterations} tablas ({b.tableau_shape}, {b.elapsed_ms} ms)."
            )
        return (
            f"Ambos métodos terminaron como óptimos pero con distinto valor de Z "
            f"(Simplex: Z = {z_s}, Gran M: Z = {z_b})."
        )

    if s.status == "not_admissible":
        if b.status == "optimal":
            z_b = z_values.get("big_m", "")
            if d and d.status == "optimal":
                return f"El problema no está en forma estándar para Simplex; Gran M y Simplex Dual convergen a la misma solución óptima (Z = {z_b})."
            return (
                f"No fue posible aplicar transformación al problema equivalente en Simplex estándar "
                f"(por igualdades '=', lados derechos negativos o cotas incompatibles); "
                f"Gran M lo resolvió hasta el óptimo (Z = {z_b}) en {b.iterations} tablas ({b.tableau_shape})."
            )
        if b.status == "infeasible":
            return (
                f"Simplex estándar no es admisible para este problema; Gran M "
                f"determinó que el problema es infactible tras {b.iterations} tablas."
            )
        if b.status == "unbounded":
            return (
                f"Simplex estándar no es admisible para este problema; Gran M "
                f"determinó que el problema no está acotado tras {b.iterations} tablas."
            )

    return "Comparación completada."


@app.post("/api/comparar")
def comparar(req: ComparisonRequest):
    results: dict[str, MethodSummary] = {}
    z_values: dict[str, str] = {}
    for method_id, method in REGISTRY.items():
        t0 = time.perf_counter()
        try:
            res = method.run(req.problem)
            results[method_id] = MethodSummary(
                method=method_id, status=res.status,
                iterations=len(res.iterations),
                elapsed_ms=round((time.perf_counter() - t0) * 1000, 3),
                tableau_shape=f"{len(res.final_table.rows)}x{len(res.final_table.columns)}")
            if res.status == "optimal":
                z_values[method_id] = str(res.objective.get("value", ""))
        except NotImplementedError:
            results[method_id] = MethodSummary(method=method_id, status="not_implemented")
        except MethodNotAdmissibleError:
            results[method_id] = MethodSummary(method=method_id, status="not_admissible")

    same = None
    optimal_vals = [z_values[m] for m, r in results.items() if r.status == "optimal" and m in z_values]
    if len(optimal_vals) == len(results):
        same = len(set(optimal_vals)) == 1
    used_transform = uses_equivalent_transform(req.problem)
    return Comparison(
        results=results,
        same_objective=same,
        verdict=_comparison_verdict(results, z_values, same, used_transform=used_transform),
    )


# Serve the built frontend (README ruta A). Needs frontend/dist (npm run build).
_dist = Path(
    os.environ.get(
        "SOLVER_FRONTEND_DIST",
        Path(__file__).resolve().parents[3] / "frontend" / "dist",
    )
)
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")