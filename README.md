# io1-solver — Simplex y Gran M (PL) · IO1 Grupo 3

Software para resolver problemas de programación lineal con los métodos
**Simplex** y **Gran M** sobre un motor común de aritmética exacta
(`fractions.Fraction` + **M simbólica**). Los datos siempre se ingresan por la
interfaz — nunca van escritos dentro del código.

Stack: FastAPI (Python 3.13, gestionado con `uv`) + React/TypeScript/Tailwind (Vite).

## Estructura

```
backend/    paquete `solver` (uv): engine/ (motor genérico), methods/ (adaptadores
            Simplex y Gran M), sensitivity.py, schemas.py, tests/
frontend/   React + TS + Tailwind (Vite); sirve el stepper de tablas
examples/    fixtures JSON compartidos: UI (/api/ejemplos) y pytest
docs/       contracts.md (fuente de verdad de los contratos) + informe/
```

El contrato de cada módulo (qué recibe, qué devuelve, casos especiales) está
en **`docs/contracts.md`**.

## Ejecución — Ruta A (oficial, sin Docker)

```bash
cd backend
uv sync
uv run uvicorn solver.main:app
# → http://127.0.0.1:8000
```

Con `frontend/dist` presente, el backend sirve la app completa (un solo
comando, un solo puerto). Para generarlo una vez:

```bash
cd frontend && npm ci && npm run build
```

## Desarrollo (dos terminales)

- Backend: `cd backend && uv run uvicorn solver.main:app --reload`
- Frontend: `cd frontend && npm run dev` (proxy de `/api` → `:8000`)

## Ruta B — Docker Compose

```bash
docker compose up --build
# frontend: http://localhost:5173 · API: http://localhost:8000/health
```

## Tests

```bash
cd backend && uv run pytest
```

Las pruebas automáticas del curso viven en `backend/tests/` y se parametrizan
sobre `examples/*.json` (los mismos ejemplos precargados de la UI, incluido
uno infactible).

## Reglas del curso ↔ dónde se cumplen

- Datos nunca escritos en el código → todo entra por la API/UI; ejemplos en JSON.
- Sin librerías que resuelvan el problema → motor propio en `engine/`.
- Paso a paso + casos especiales → `docs/contracts.md` (§2, §3).
- Verificación aparte (Excel Solver) → informe en `docs/informe/`.
- Declaración de uso de IA → informe final.

## Flujo de trabajo

Objetivo: **que no se pierda código**. Solo hay reglas de flujo — sin
convención obligatoria de nombres de ramas ni de commits (decisión del grupo).

- `main` = entregables (tags por entrega). **Solo recibe PRs desde `develop`**
  (lo exige el job `guard-main-base` del CI).
- `develop` = rama de integración: todo el trabajo se integra aquí con PR.
- El flujo es siempre: rama propia → PR a `develop` → PR a `main`.

Lo que evita perder código (ya configurado en el repo):

- `main` y `develop` protegidas: sin push directo, sin force-push, sin borrar
  la rama; historia lineal (squash al mergear).
- Todo merge exige CI verde + 1 aprobación: nadie pisa el trabajo de otro
  sin que se vea en el diff del PR.

## Tags de entrega

`frontend/dist` va ignorado en desarrollo; en cada entrega se fuerza y se
etiqueta (para que la Ruta A funcione desde el tag sin Node):

```bash
cd frontend && npm ci && npm run build
git add -f frontend/dist
git commit -m "release: entrega N"
git tag entrega-N && git push origin main --tags
```

## Equipo

Daniel Chavarro (P1) · Jorge Méndez (P2) · Nicolás Velazco (P3) · [P4 por confirmar]
