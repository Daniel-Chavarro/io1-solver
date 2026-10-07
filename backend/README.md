# backend — solver (FastAPI, uv)

Python package `solver` (src layout, managed with uv).

```bash
uv sync                 # install (dev included)
uv run pytest           # tests (examples/ are shared fixtures)
uv run uvicorn solver.main:app --reload   # dev server on :8000
```

Architecture: `engine/` = one generic simplex loop (exact arithmetic,
method-agnostic). `methods/` = per-method builders/interpreters (Simplex,
Big M). `sensitivity.py` reads the optimal tableau. Contracts:
`docs/contracts.md`.
