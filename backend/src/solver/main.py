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
from .schemas import Comparison, ComparisonRequest, MethodSummary, Problem, ResolverRequest, SensitivityRequest
from .sensitivity import analyze

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
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Sensibilidad aun no implementada (ver issues)")


@app.post("/api/comparar")
def comparar(req: ComparisonRequest):
    results: dict[str, MethodSummary] = {}
    for method_id, method in REGISTRY.items():
        t0 = time.perf_counter()
        try:
            res = method.run(req.problem)
            results[method_id] = MethodSummary(
                method=method_id, status=res.status,
                iterations=len(res.iterations),
                elapsed_ms=round((time.perf_counter() - t0) * 1000, 3),
                tableau_shape=f"{len(res.final_table.rows)}x{len(res.final_table.columns)}")
        except NotImplementedError:
            results[method_id] = MethodSummary(method=method_id, status="not_implemented")
        except MethodNotAdmissibleError:
            results[method_id] = MethodSummary(method=method_id, status="not_admissible")
    same = None
    if len(results) == 2 and all(r.status == "optimal" for r in results.values()):
        same = True  # TODO(P1): compare z values across methods, not just status
    return Comparison(
        results=results, same_objective=same,
        verdict="Comparacion completa cuando ambos metodos esten implementados")


# Serve the built frontend (README ruta A). Needs frontend/dist (npm run build).
_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")