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

Puedes levantar el proyecto de tres formas:
1. **Ruta A (con Docker Compose, recomendada)**: levanta el frontend y el backend contenerizados en un solo paso, sin necesidad de instalar Python, `uv` ni Node.js.
2. **Ruta B (local en un solo puerto sin Docker)**: backend con `uv` sirviendo la interfaz precompilada (`frontend/dist`) en `http://127.0.0.1:8000`.
3. **Ruta C (servidores separados con `npm run dev`)**: fallback si la Ruta B falla o si necesitas recarga en caliente durante el desarrollo.
---

### Ruta A — Con Docker Compose (recomendada)

Levanta la aplicación completa (backend y frontend en contenedores listos para usar):

```bash
docker compose up --build
```

Una vez levantado:
- **Frontend (UI)**: [http://localhost:5173](http://localhost:5173)
- **Backend (API / Docs)**: [http://localhost:8000](http://localhost:8000) (salud en `/health`, docs OpenAPI en `/docs`)

Para detener los servicios:

```bash
docker compose down
```

---

### Ruta B — Local sin Docker (con `uv`)

Permite correr el backend y servir la interfaz gráfica directamente desde el host:

1. **Compilar la interfaz (requiere Node.js)**:
   ```bash
   cd frontend && npm ci && npm run build && cd ..
   ```
   *(Si ya cuentas con la carpeta `frontend/dist` precompilada, puedes omitir este paso).*

2. **Iniciar el servidor** desde la raíz con `uv`:
   ```bash
   uv run --directory backend uvicorn solver.main:app
   ```
   *(O entrando a `backend/`: `cd backend && uv sync && uv run uvicorn solver.main:app`).*

3. **Acceso a la aplicación**:
   Al detectar `frontend/dist`, el backend unifica todo en un solo puerto:
   - **Frontend (UI visual completa)**: abre tu navegador en [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **API y Documentación OpenAPI**: disponible en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

> **Nota**: Si ejecutas el backend sin compilar `frontend/dist`, solo responderán los endpoints de la API (`/api/...`, `/docs`, etc.) en el puerto `:8000`, sin la interfaz gráfica web.

---

### Ruta C — Servidores separados con `npm run dev` (fallback / desarrollo)

Si la compilación de `frontend/dist` en la Ruta B falla, o prefieres levantar ambos entornos por separado con recarga en vivo (hot-reload), abre dos terminales:

1. **Terminal 1 — Backend (FastAPI)**:
   ```bash
   cd backend
   uv sync
   uv run uvicorn solver.main:app --reload
   ```
   *(Queda disponible en [http://127.0.0.1:8000](http://127.0.0.1:8000))*.

2. **Terminal 2 — Frontend (Vite Dev Server)**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *(Vite inicia en [http://localhost:5173](http://localhost:5173) y reenvía automáticamente las peticiones de `/api` hacia el backend en el puerto `:8000`)*.

3. **Acceso a la aplicación**:
   - **Frontend (UI con recarga en vivo)**: abre [http://localhost:5173](http://localhost:5173)
   - **Backend (API / Docs)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

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
etiqueta (para que la Ruta B local funcione desde el tag sin Node):

```bash
cd frontend && npm ci && npm run build
git add -f frontend/dist
git commit -m "release: entrega N"
git tag entrega-N && git push origin main --tags
```

## Equipo

Daniel Chavarro (P1) · Jorge Méndez (P2) · Nicolás Velazco (P3) · Santiago Vargas (P4)
