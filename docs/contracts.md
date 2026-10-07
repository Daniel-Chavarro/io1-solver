# Contratos internos y de API — Grupo 3 · proyecto `solver`

> Versión 0.1 — base para los issues. Código en inglés; mensajes mostrados al usuario en español.
> Regla del curso que este documento respeta: los datos NUNCA van escritos en el código (todo entra por la interfaz/API), y ningún método usa una librería que resuelva por él.

## 0. Convención numérica (transversal)

- **Entradas:** todo número llega como **string decimal** (`"2.5"`, `"-40"`, `"0.1"`). Se parsea con `Fraction(Decimal(s))` → aritmética exacta. Ningún float JSON toca el dominio.
- **Salidas:** strings canónicos:
  - Sin M: `"5"`, `"3/4"`, `"-7/2"`
  - Con M: `"M"`, `"-3M"`, `"-M-30"`, `"2M+1/3"` (término en M primero, constante con signo explícito)
- Validación de entrada: regex `^-?\d+(\.\d+)?$` → 422 si falla.
- El frontend **nunca calcula ni parsea**: solo muestra strings.

## 1. Esquema de entrada (`schemas.py`, Pydantic)

```python
Sense = Literal["max", "min"]
Op = Literal["<=", ">=", "="]

class Variable(BaseModel):
    name: str        # "pandesal" — unico, no vacio
    unit: str        # "lotes" — para frases y tablas

class Constraint(BaseModel):
    name: str                  # "horas_horno"
    coefficients: list[str]     # len == len(variables)
    op: Op
    rhs: str                   # decimal string (puede ser negativo)

class Objective(BaseModel):
    sense: Sense
    coefficients: list[str]

class Problem(BaseModel):
    name: str
    variables: list[Variable]       # 1..8
    objective: Objective
    constraints: list[Constraint]   # 1..8
```

Validaciones (→ 422 en español): nombres únicos y no vacíos; `len(coefficients) == len(variables)`; números parseables; máximo 8 variables y 8 restricciones.

## 2. Núcleo (`engine/`) — no sabe que existe un método

### `frac_m.py`

```python
@dataclass(frozen=True)
class FracM:
    const: Fraction   # termino independiente
    m: Fraction = 0  # coeficiente de M

    # ops exactas: add, sub, mul(Fraction), neg
    # orden TOTAL lexicografico: primero m, luego const
    #   (-M - 30) < (-40)   <- M domina constantes
    # to_str(): "3/4" | "M" | "-3M" | "-M-30" | "2M+1/3" | "-2"
    # parse_decimal(s) -> FracM  (exacto, via Decimal)
```

### `tableau.py`

```python
class Row:
    basic: str          # "x1" | "s1" | "e1" | "a1" | "z"
    cells: list[FracM]  # len == len(columns)

class Tableau:
    columns: list[str]   # variables originales + auxiliares + "rhs"
    rows: list[Row]     # rows[0] es SIEMPRE la fila z

    def pivot(self, basic_row: str, col: str) -> Tableau   # inmutable: devuelve nuevo
    def z_row(self) -> Row
    def most_negative_z_entry(self) -> str | None          # columna que entra (orden FracM)
    def is_optimal(self) -> bool                           # fila z sin negativos
    def min_ratio(self, col: str) -> tuple[str | None, list[str]]
        # (fila saliente | None si columna sin positivos, razones como strings)
```

Convenciones:
- **Fila z almacena `z_j − c_j`; entra el más negativo; `rhs` de la fila z = valor actual de z.**
- Nombres de auxiliares: `s_i` holgura (de `≤`), `e_i` exceso (de `≥`), `a_i` artificial (de `≥` y `=`).
- `pivot` devuelve un Tableau nuevo → los snapshots para el stepper salen gratis.
- **Nunca se eliminan columnas (artificiales incluidas):** B⁻¹ final vive en las columnas de la identidad inicial; la sensibilidad la necesita.

### `solver.py`

```python
@dataclass
class Iteration:
    number: int            # 0 = tabla inicial, ANTES del primer pivote
    tableau: Tableau       # snapshot DESPUES del pivote n (n >= 1)
    entering: str | None
    leaving: str | None
    pivot: str | None      # "2/3"
    ratios: list[str]      # razones del paso; "-" si celda <= 0
    ties: list[str]        # filas empatadas en razon minima (degeneracion)

@dataclass
class EngineResult:
    status: Literal["optimal", "unbounded"]
    iterations: list[Iteration]
    final: Tableau

def solve(initial: Tableau, max_iter: int = 200) -> EngineResult
```

Reglas del bucle (FIJAS, idénticas para todo método):
1. entra = `most_negative_z_entry` (orden lexicográfico de FracM → en Gran M prioriza automáticamente los términos con M).
2. sin negativos → `optimal`.
3. razón mínima; columna sin positivos → `unbounded` (se registra la iteración).
4. pivote → snapshot → siguiente. `max_iter` excedido → RuntimeError (bug de implementación, no un caso del método).

**El motor siempre maximiza.** La normalización max/min vive en los constructores.

## 3. Métodos (`methods/`) — protocolo uniforme

```python
class Method(Protocol):
    id: str                    # "simplex" | "big_m"
    display_name: str          # "Simplex" | "Gran M"
    def build(self, problem: Problem) -> Tableau
    def interpret(self, result: EngineResult, problem: Problem) -> MethodResult
```

`MethodResult` (lo que devuelve `POST /api/resolver`):

```python
class SpecialCase(BaseModel):
    type: Literal["degenerate_pivot", "alternative_optima", "unbounded",
                  "infeasible", "normalized_constraint"]
    iteration: int | None
    detail: str                      # frase en espanol

class VariableValue(BaseModel):
    name: str; unit: str; value: str

class MethodResult(BaseModel):
    method: str
    status: Literal["optimal", "unbounded", "infeasible"]
    solution: list[VariableValue]    # SOLO variables originales (artificiales/holguras excluidas)
    objective: dict                  # {"sense": "max", "value": "1550"}
    special_cases: list[SpecialCase]
    iterations: list[Iteration]
    final_table: Tableau
    elapsed_ms: float                # medido en la capa API alrededor de build+solve+interpret
```

### `methods/simplex.py`

- **build** — valida y si no pasa lanza `MethodNotAdmissibleError` (→ 422 con mensaje español):
  - toda restricción debe ser `<=` ("El método Simplex solo admite restricciones ≤ … usa Gran M")
  - `rhs >= 0` en todas (forma estándar; RHS negativo → sugerir Gran M)
  - ≤ 8 variables / ≤ 8 restricciones
  - normaliza min→max (niega c, lo registra internamente para revertir al reportar)
  - agrega `s_1..s_m`; base inicial = holguras; fila z desde el objetivo
- **interpret**:
  - `unbounded` → frase + iteración donde se detectó
  - degeneración (empate en razón mínima o básica en 0) → `degenerate_pivot` con frase
  - óptimos alternativos → no básica con costo reducido 0 en la tabla final → `alternative_optima`
  - solución: variables originales desde la base final (0 si no básicas), z en el sentido original

### `methods/big_m.py`

- **build**:
  - normaliza min→max
  - `rhs < 0` → multiplica la fila por -1 (volteando `op`) y agrega `normalized_constraint` al resultado
  - `<=` → holgura `s_i`; `>=` → exceso `e_i` (coeficiente -1) + **artificial `a_i` con costo -M**; `=`` → **artificial `a_i` con costo -M**
  - fila z con FracM → los `-M` quedan visibles en las tablas
- **interpret**: todo lo de simplex **más**:
  - artificial en base final con valor > 0 → `infeasible` ("el problema no tiene solución factible: la artificial a_i quedó en la base")
  - artificial en base final en 0 → nota degenerada (no es infactible)
  - excluye artificiales/holguras de `solution`

## 4. Sensibilidad (`sensitivity.py`)

```python
def analyze(problem: Problem, method: Method) -> SensitivityReport
```

- La API recibe `{method, problem}` (NO el tableau) → re-resuelve internamente (exacto y barato), sin estado ni round-trip de strings.
- Usa la tabla final: precios sombra desde la fila z (columnas de holgura/exceso/artificial), B⁻¹ desde las columnas de la identidad.

```python
class ShadowPrice(BaseModel):     # por restriccion
    constraint: str; unit: str
    value: str                    # "5/2"; 0 si no activa
    binding: bool
    phrase: str                   # "Una hora mas de horno aumentaria la utilidad en 2.5"

class ReducedCost(BaseModel):     # por variable NO basica
    variable: str; unit: str; value: str; phrase: str

class ObjRange(BaseModel):        # rango de cada cj
    variable: str; current: str; range: tuple[str, str]   # "-inf" permitido
    phrase: str                   # "mientras la utilidad por lote este entre A y B, el plan optimo no cambia"

class RhsRange(BaseModel):        # rango de cada bi
    constraint: str; current: str; range: tuple[str, str] # "+inf" permitido
    phrase: str                   # "entre A y B horas de horno, la base optima se mantiene"

class SensitivityReport(BaseModel):
    shadow_prices: list[ShadowPrice]
    reduced_costs: list[ReducedCost]
    objective_ranges: list[ObjRange]
    rhs_ranges: list[RhsRange]
```

Casos especiales exigidos por el curso, cada uno con su frase: **rangos infinitos** (lado `"-inf"`/`"+inf"`), **restricción sin holgura** (binding → precio sombra > 0), **restricción con holgura** (precio 0, rango unilateral).

## 5. API (`main.py`)

| Endpoint | Request | Response |
|---|---|---|
| `POST /api/resolver` | `{"method": "simplex"\|"big_m", "problem": Problem}` | `MethodResult` |
| `POST /api/sensibilidad` | `{"method": ..., "problem": Problem}` | `SensitivityReport` |
| `POST /api/comparar` | `{"problem": Problem}` | `Comparison` |
| `GET /api/ejemplos` | — | `[{id, name, description, kind}]` |
| `GET /api/ejemplos/{id}` | — | `{problem}` (sin `expected`) |

`Comparison`:

```python
class MethodSummary(BaseModel):
    method: str
    status: str        # "optimal" | "unbounded" | "infeasible" | "not_admissible"
    iterations: int | None
    elapsed_ms: float | None
    tableau_shape: str | None     # "3x6"

class Comparison(BaseModel):
    results: dict[str, MethodSummary]   # {"simplex": ..., "big_m": ...}
    same_objective: bool | None         # z igual si ambos optimal; None si no comparable
    verdict: str                        # frase en espanol
```

### Ejemplo `POST /api/resolver`

Request:
```json
{
  "method": "big_m",
  "problem": {
    "name": "Plan de produccion - panaderia",
    "variables": [
      {"name": "pandesal", "unit": "lotes"},
      {"name": "hojaldre", "unit": "lotes"}
    ],
    "objective": {"sense": "max", "coefficients": ["40", "30"]},
    "constraints": [
      {"name": "horno", "coefficients": ["1", "1"], "op": "<=", "rhs": "40"},
      {"name": "demanda_hojaldre_min", "coefficients": ["0", "1"], "op": ">=", "rhs": "5"}
    ]
  }
}
```

Response (fragmento):
```json
{
  "method": "big_m",
  "status": "optimal",
  "solution": [
    {"name": "pandesal", "unit": "lotes", "value": "35"},
    {"name": "hojaldre", "unit": "lotes", "value": "5"}
  ],
  "objective": {"sense": "max", "value": "1550"},
  "special_cases": [],
  "iterations": [
    {"number": 0, "entering": null, "leaving": null, "pivot": null, "ratios": [], "ties": [],
     "tableau": {
       "columns": ["pandesal", "hojaldre", "s1", "e1", "a1", "rhs"],
       "rows": [
         {"basic": "z",  "cells": ["-40", "-M-30", "0", "M", "0", "-5M"]},
         {"basic": "s1", "cells": ["1", "1", "1", "0", "0", "40"]},
         {"basic": "a1", "cells": ["0", "1", "0", "-1", "1", "5"]}
       ]}},
    {"number": 1, "entering": "hojaldre", "leaving": "a1", "pivot": "1",
     "ratios": ["40", "5"], "ties": [],
     "tableau": { "...": "..." }}
  ],
  "final_table": {"...": "..."},
  "elapsed_ms": 0.42
}
```

Nota: en la iteración 0 la fila z de Gran M muestra `-M-30` en hojaldre — el orden lexicográfico hace que el motor lo elija antes que `-40`; es exactamente la regla del Gran M.

## 6. Errores / validación

- 422 con cuerpo `{"code": "...", "message": "<español>"}`. Códigos: `INVALID_NUMBER`, `EMPTY_FIELD`, `DUPLICATE_NAME`, `SIZE_LIMIT` (> 8), `METHOD_NOT_ADMISSIBLE` (simplex con `>=`/`=` o RHS negativo).
- El frontend muestra `message` tal cual; el programa nunca se cierra por datos malos.
- `not_admissible` dentro de `comparar` NO es error: se reporta como estado de ese método.

## 7. `examples/*.json` (fixtures dobles: UI + pytest)

```json
{
  "id": "bakery-real",
  "name": "Plan de produccion - panaderia",
  "description": "Caso real del grupo (fuente en docs/informe)",
  "kind": "real",
  "problem": { "...": "como el schema Problem" },
  "expected": {
    "simplex": {"status": "optimal", "objective_value": "1550"},
    "big_m":   {"status": "optimal", "objective_value": "1550"}
  }
}
```

- `kind`: `real` | `test` | `infeasible` (mínimo uno infactible, exigido por el curso).
- pytest parametriza sobre estos archivos y afirma `expected` por método → las 5+ pruebas automáticas salen del mismo material.
- `GET /api/ejemplos` sirve la lista sin `expected`; `GET /api/ejemplos/{id}` devuelve el `problem` para cargarlo en el formulario.
