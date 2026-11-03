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
docs/       contracts.md (contratos de API) + informe/informe-comparativo.md
```

El contrato de cada módulo (qué recibe, qué devuelve, casos especiales) está
en **`docs/contracts.md`**.

## Opciones de ejecución

Puedes levantar el proyecto de dos formas:
1. **Ruta A (local con `uv`, recomendada/oficial)**: todo en un solo puerto y sin contenedor.
2. **Ruta B (con Docker Compose)**: alternativa contenerizada para levantar frontend y backend en servicios separados sin configurar entornos locales.

---

### Ruta A — Local sin Docker (oficial)
Desde la raíz del repositorio con un solo comando (con `uv`):

```bash
uv run --directory backend uvicorn solver.main:app
# → http://127.0.0.1:8000
```

O desde la carpeta `backend/`:

```bash
cd backend
uv sync
uv run uvicorn solver.main:app
```

Con `frontend/dist` presente (precompilado y commiteado en los tags de entrega),
el backend sirve la app completa (SPA estática + API) en un solo comando y un
solo puerto (**http://127.0.0.1:8000**), **sin requerir Node.js**.

Para compilar `frontend/dist` en desarrollo (requiere Node):

```bash
cd frontend && npm ci && npm run build
```

### Ruta B — Alternativa con Docker Compose

Si prefieres no instalar `uv` ni `Node.js` localmente, puedes levantar la aplicación completa en contenedores con Docker Compose:

```bash
docker compose up --build
```

Una vez levantado:
- **Frontend (UI)**: [http://localhost:5173](http://localhost:5173)
- **Backend (API / Docs)**: [http://localhost:8000](http://localhost:8000) (salud en `/health`, docs en `/docs`)

Para detener los servicios:
```bash
docker compose down
```

---

## Desarrollo (dos terminales)

- Backend: `cd backend && uv run uvicorn solver.main:app --reload`
- Frontend: `cd frontend && npm run dev` (proxy de `/api` → `:8000`)

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
- Verificación aparte (Excel Solver) → [informe en docs/informe/informe-comparativo.md](docs/informe/informe-comparativo.md).
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

Daniel Chavarro (P1) · Jorge Méndez (P2) · Nicolás Velazco (P3) · Santiago Vargas (P4)
