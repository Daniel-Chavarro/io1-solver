# Plan del proyecto — IO1 Grupo 3 (Simplex + Gran M)

Documento consolidado de la planeación arquitectural: decisiones tomadas
(rondas de preguntas), arquitectura resultante, cronograma y reparto de
trabajo. Fuentes: `docs/contracts.md` (contratos exactos), el README (cómo
corre) y las issues (quién hace qué, con DoD).

## 1. Registro de decisiones

Cada pregunta se hizo cuando sus dependencias ya estaban resueltas; la
respuesta define lo que cuelga de ella.

| # | Decisión | Elegido | Alternativas descartadas |
|---|----------|---------|--------------------------|
| Q1 | Cómo se conectan backend y frontend | FastAPI + React (Vite); en producción el backend sirve el build de React (un solo comando) | Pyodide (riesgo en 5 semanas), Flask (sin ventaja) |
| Q2 | Problema real | Estilo plan de producción (max de utilidad, límites de recursos), empresa real por definir | — |
| Q3 | Lenguaje del frontend | TypeScript | JavaScript (sin tipos para el contrato JSON) |
| Q4 | Aritmética de los motores | `fractions.Fraction` + **M simbólica** (`a + bM`) | Flotantes (error de redondeo en pivotes), M como número gigante |
| Q5/Q7 | Organización del equipo | Issues con dueño; el modelo/informe pesa menos que el software, así que el reparto se equilibra en issues, no en roles fijos | Roles cerrados A/B/C/D (P1 quedaba subcargado después de la semana 1) |
| Q7' | Arquitectura de métodos | **1 motor genérico** (bucle simplex) + **constructores/intérpretes por método** — aprobado por la profe | 2 motores separados (código duplicado del pivote) |
| Q8 | Contrato de API | Ver `docs/contracts.md` §5: `POST /api/resolver|sensibilidad|comparar`, `GET /api/ejemplos[/{id}]`; celdas como strings exactas | — |
| Q9 | Fixtures dobles | `examples/*.json` alimentan UI **y** pytest (con `expected`) | Fixtures duplicadas |
| Q10/Q15 | Ejecución | **Ruta A oficial**: `uv sync && uv run uvicorn solver.main:app` con `dist/` commiteado por tag (sin Node para el docente). **Ruta B**: docker compose + Dockerfile dentro de cada app | Solo Docker (dependencia de red/Docker en la sustentación) |
| Q11 | Sensibilidad | Genérica: funciona sobre cualquier PL resuelto en la UI | Solo el caso real |
| Q12 | UI | Tailwind | MUI/AntD (peso innecesario) |
| Q13/Q16 | Navegación de resultados | Stepper ◀ ▶ + "ver todas"; pestañas `Resolver \| Comparación \| Sensibilidad` con selector de método global en el formulario (ver `docs/frontend-plan.md`, que sustituye a las pestañas por método) | Tablas apiladas, acordeón |
| Q14 | Comparación | Sección automática con métricas (`/api/comparar`, `perf_counter`) | — |
| Q17 | Dos Fases | **Fuera de alcance**; solo si alguien es proactivo y todo lo demás está verde | Incluirlo en el alcance |
| Q18 | Endpoint unificado | `POST /api/resolver {problem, method}` — `method` elige el par constructor+intérprete (el motor es el mismo) | Un endpoint por método |
| Q19 | Equipo | P1 Daniel, P2 Jorge Méndez (Dizast3r), P3 Nicolás Velazco (Niko784), P4 sin reportar | — |
| — | Idiomas | Código, comentarios y commits en **inglés**; informe, manual y textos de UI en **español** | — |
| — | Flujo git | GitFlow simplificado: `develop` integra, `main` solo recibe PRs desde `develop` (guardado por CI). Sin nomenclatura de ramas ni commits — solo reglas que evitan perder código | GitFlow completo con release/ y hotfix/ |

## 2. Arquitectura resultante

```
backend/                 paquete solver (uv, src layout)
  src/solver/
    engine/
      frac_m.py          FracM: Fraction + M simbólica, orden lexicográfico
      tableau.py         Tableau inmutable, fila z (z_j − c_j), pivote, razón mínima
      solver.py          bucle genérico → iteraciones + resultado (siempre maximiza)
    methods/
      simplex.py         constructor (solo ≤, holguras) + intérprete
      big_m.py           constructor (≤,≥,= con artificiales −M) + intérprete
    sensitivity.py       precios sombra, costos reducidos, rangos cj/bi + frases
    schemas.py           Pydantic (contrato JSON, espejo en frontend/src/types.ts)
    main.py              FastAPI: /api/* + sirve frontend/dist (ruta A)
  tests/                 pytest parametrizado sobre examples/ (5+ pruebas)
frontend/                React + TS + Tailwind (Vite)
examples/                fixtures JSON dobles (UI + pytest), uno infactible
docs/contracts.md        fuente de verdad de los contratos
```

Decisiones estructurales que sostienen el diseño:

- El motor **nunca sabe** qué método corre: recibe una tabla inicial y
  pivotea. Cada método construye su tabla (construcción) y lee el resultado
  (intérprete: casos especiales, solución con unidades, frases).
- Regla única de pivoteo: entra el costo reducido más negativo con orden
  **lexicográfico** sobre `(m, const)` — en Gran M los términos con M dominan
  automáticamente, sin lógica especial en el bucle.
- Todo número viaja como string decimal (`"2.5"`) y se parsea con
  `Fraction(Decimal(s))`; las celdas se devuelven en forma canónica
  (`"3/4"`, `"-M-30"`). El frontend solo muestra, nunca calcula.
- Validación en dos capas: Pydantic (forma, 422 en español) y por método
  (`MethodNotAdmissibleError` p. ej. Simplex con `>=` → sugerir Gran M).
- `dist/` commiteado solo en tags de entrega (`git add -f`) → el docente
  ejecuta con un solo comando sin Node.

## 3. Cronograma (fechas del PDF §7)

| Hito | Fecha | Qué se entrega | Qué se sustenta |
|------|-------|----------------|-----------------|
| Entrega 1 (20%) | 20-oct | Informe 4–8 págs: problema real, contexto, alcance, supuestos, modelo preliminar. **Sin software** | 0–4 problema, 4–8 modelo, 8–10 preguntas |
| Entrega 2 (30%) | 27-oct | Modelo completo, diseño del sistema, **Simplex funcionando** + código del primer método | Modelo, diseño, demo con caso real y problema nuevo del docente |
| Final (50%) | 10-nov | Informe corregido + código completo: **ambos métodos, sensibilidad, comparación** | Demo con caso real, problema nuevo del docente, conclusiones, preguntas |

Semana 1 (7–19 oct): problema real y modelo preliminar (issues #1, #2).
Semana 2 (20–26): Simplex + formulario + stepper (#4–#11) para la entrega 2.
Semanas 3–4 (27-oct–8-nov): Gran M + sensibilidad (#12–#15), comparación
(#14), tests, README, informe final (#16, #17). 8–9 nov: ensayos con
cronómetro y problema nuevo de práctica.

Riesgo activo: el problema real debe estar definido **antes del ~14-oct**
o el margen del informe de la entrega 1 se come.

## 4. Reparto de trabajo (por issues, con dueño)

- **Daniel (P1)**: #1 problema real, #2 modelo + informe E1, #3 verificación
  Excel Solver, #8 capa API/validación, #11 ejemplos, #14 comparación,
  #16 comparación + tests + README, #17 informe final.
- **Nicolás (P3)**: #4 FracM, #5 Tableau, #6 solver, #7 Simplex (método 1).
- **Jorge (P2)**: #9 formulario, #10 stepper/tabs, #15 sección sensibilidad.
- **P4 (sin reportar)**: #12 Gran M (método 2), #13 sensibilidad.

Si P4 no aparece: #12 → Nicolás (constructor, ya conoce el motor) y #13 →
Daniel o Jorge (intérprete + frases). Decisión abierta.

Cada issue lleva su DoD y la sección de `docs/contracts.md` que le
corresponde; el PR a `develop` con CI verde es la única puerta de entrada.

## 5. Reglas del curso → dónde se cumplen

| Regla del PDF | Dónde vive |
|---|---|
| Datos nunca en el código | Todo entra por la UI/API; ejemplos en `examples/*.json` |
| Sin librerías que resuelvan | Motor propio en `engine/` (solo stdlib `fractions`/`decimal`) |
| Paso a paso + casos especiales | Contrato §2/§3: cada tabla con entra/sale/pivote; avisos de infactible/no acotado/alternativos/degeneración |
| ≥5 pruebas automáticas | `backend/tests/` parametrizado sobre `examples/` (CI las exige verdes) |
| README ejecutable | Ruta A con un comando (verificado: `uv sync && uv run uvicorn solver.main:app`) |
| Verificación aparte | Excel Solver sobre el caso real (issue #3, anexo del informe) |
| Declaración de IA | Sección del informe final (issue #17): herramienta, uso, verificación |
| Resultado con nombres y unidades | `solution[]` del contrato lleva `name`, `unit`, `value` |
