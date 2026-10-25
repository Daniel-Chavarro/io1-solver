# Documentación de Cambios — Motor Simplex (`engine`)

> **Rama:** `engine`  
> **Fecha:** Octubre 2026  
> **Estado:** Implementado, verificado y pasando suite de pruebas unitarias (`62 passed`).

---

## 1. Resumen Ejecutivo

Durante el desarrollo en la rama `engine` se implementó el núcleo matemático completo del método Simplex para el proyecto `solver`. El motor es completamente **agnóstico al método** (desconoce si el problema es Simplex estándar o Gran M), opera con **aritmética exacta** y mantiene una representación inmutable tabular basada en el formato $C_j - Z_j$ (según lo dispuesto en el [ADR 0001](../adr/0001-formato-tabular-cj-zj.md)).

### Principales logros:
1. **Aritmética exacta y simbólica (`FracM`):** Manejo de coeficientes exactos con `Fraction` y constante simbólica $M$, dotada de orden lexicográfico total donde $M$ domina sobre cualquier constante.
2. **Estructura tabular pura e inmutable (`Tableau` & `Row`):** Transformaciones de Gauss-Jordan exactas en `pivot()`, cálculo desacoplado de $Z_j$ y $C_j - Z_j$ mediante `evaluate()`, y búsqueda de variables entrantes/salientes con detección de empates de degeneración.
3. **Bucle de resolución (`solver.py`):** Ejecución del algoritmo simplex iterativo, preservando snapshots inmutables para el stepper interactivo del frontend y control de ciclado mediante límite de iteraciones.
4. **Cobertura exhaustiva de pruebas:** 57 pruebas unitarias nuevas cubriendo aritmética, orden, pivoteo, optimalidad, degeneración, no acotamiento y regresión.

---

## 2. Inventario de Cambios Realizados (Inspección Git)

La rama introduce 20 commits sobre `develop` con más de 1000 líneas de código y pruebas. Los archivos afectados son:

| Archivo | Tipo de cambio | Descripción |
|---|---|---|
| `backend/src/solver/engine/frac_m.py` | Modificado (+63, -5) | Implementación de `FracM`: aritmética, `@total_ordering`, multiplicación bidireccional, formateo `__str__` y `parse_decimal`. |
| `backend/src/solver/engine/tableau.py` | Modificado (+141, -23) | Definición de `Row` (`cells: list[Fraction]`), `@dataclass(frozen=True) Tableau`, métodos `pivot`, `evaluate`, `get_entering_variable`, `get_leaving_variable`, `is_optimal`, `get_pivot_value`. |
| `backend/src/solver/engine/solver.py` | Modificado (+39, -2) | Función `solve(initial, max_iter)` y estructuras `Iteration` y `EngineResult`. |
| `docs/contracts.md` | Modificado (+2, -2) | Ajustes en las firmas de `Row.cells` y `Tableau.cj_zj` para reflejar la realidad matemática del modelo. |
| `backend/tests/test_frac_m.py` | Modificado (+138, -13) | 22 tests unitarios de operaciones de `FracM`, parseo decimal y orden lexicográfico. |
| `backend/tests/test_tableau.py` | Creado (+389) | 27 tests unitarios de evaluación, pivote Gauss-Jordan, reglas de entrada/salida y manejo de errores. |
| `backend/tests/test_solver.py` | Creado (+242) | 8 tests integrales del bucle de resolución (2 pasos, degeneración, no acotado, snapshots inmutables). |

---

## 3. Discrepancias y Adaptaciones respecto a los Contratos (`docs/contracts.md`)

A continuación se detallan las diferencias entre la especificación inicial de `docs/contracts.md` (v0.2) y la implementación final en código, junto con la justificación técnica de cada variación:

| Elemento / Método | Contrato Inicial (`docs/contracts.md`) | Implementación en `engine` | Razón técnica / Decisión de diseño |
|---|---|---|---|
| **`Row.cells`** | `list[FracM]` | `list[Fraction]` | **Simplificación y consistencia matemática.** Los coeficientes tecnológicos de las restricciones ($a_{ij}$) y los lados derechos ($b_i$) son números reales racionales exactos, nunca expresiones en términos de $M$. Restringir a `Fraction` evita overhead innecesario y previene que términos en $M$ contaminen la matriz de restricciones durante el pivoteo Gauss-Jordan. |
| **Dimensión de `cj_zj`** | `len(columns)` (incluyendo columna `bj` como `""`) | `len(columns) - 1` (excluye `bj`) | **Corrección conceptual.** En el tableau $C_j - Z_j$, la columna $b_j$ no posee un $C_j$ en la función objetivo; el valor correspondiente en la fila $Z_j$ ya representa el valor actual de $Z$. No tiene sentido calcular $C_j - Z_j$ en $b_j$. Excluirlo previene accesos inválidos al buscar variables entrantes candidatas. |
| **Nombre: Variable entrante** | `entering_variable(self) -> str \| None` | `get_entering_variable(self) -> str \| None` | Convención estándar de nombres de acceso (`get_*`) dentro del módulo. |
| **Nombre y retorno: Razón mínima** | `min_ratio(self, col: str) -> tuple[str \| None, list[str]]` | `get_leaving_variable(self, col: str) -> tuple[str \| None, list[str], list[str]]` | Retorna una 3-tupla `(leaving_variable, ratios, ties)`. Calcular y retornar `ties` (empates en la razón mínima) en este punto permite detectar degeneración directamente en el paso donde ocurre. |
| **Ratios devueltos** | `ratios: list[str]` con `"-"` si celda $\le 0$ para cada fila | `ratios: list[str]` con razones de celdas válidas ($> 0$) | La implementación actual en `Tableau.get_leaving_variable` filtra directamente celdas positivas para calcular las razones reales. Las capas superiores o el formateador de la API pueden mapear a `"-"` las celdas no elegibles. |
| **Obtención del pivote** | No especificado en la interfaz de `Tableau` | `get_pivot_value(self, leaving: str, entering: str) -> Fraction` | Incorporado en commit `c1ed406` para permitir al bucle `solve()` consultar el escalar del pivote antes de transformar las filas y almacenarlo como string en el objeto `Iteration`. |
| **Multiplicación en `FracM`** | Comentario `mul(Fraction)` (solo escalar) | `__mul__`/`__rmul__` aceptan `FracM`, `Fraction` o `int` | Cubre el contrato (`FracM * Fraction`) y además admite multiplicar dos `FracM` siempre que no ambas contengan $M \neq 0$ (evita $M^2$ lanzando `ValueError`). `evaluate()` calcula $C_B \cdot a_{ij}$ directamente como `row.cb * row.cells[j]`. |
| **Serialización de `FracM`** | Método `to_str()` | Método especial `__str__(self) -> str` | Más idiomático en Python: permite usar `str(x)` nativo, f-strings e interoperabilidad con plantillas sin requerir llamadas explícitas a métodos no estándar. |
| **Numeración de `Iteration` en `solve()`** | Contrato indicaba `number = 0` para la tabla inicial antes del 1er pivote | `number = 1, 2, ...` para los snapshots resultantes de cada pivote | El bucle de `solve()` guarda las iteraciones que representaron un paso de pivoteo. Si el problema ya es óptimo de entrada, `iterations` retorna lista vacía `[]` y el resultado óptimo se encuentra en `final`. La iteración 0 puede ser inyectada por el constructor/intérprete del método (`methods/`) para la visualización del stepper. |
| **Parada por `unbounded`** | Contrato indicaba "se registra la iteración" | Retorno directo sin agregar iteración con `leaving=None` | Si no hay variable saliente, `solve()` retorna inmediatamente `EngineResult(status="unbounded", iterations=iterations, final=tableau)`. Los datos del intento de pivoteo no se añaden a la lista de iteraciones completadas. |
| **Inmutabilidad del `Tableau`** | Inmutabilidad descriptiva en texto | `@dataclass(frozen=True)` en `Tableau` | Garantiza rigurosamente que los snapshots históricos no sean alterados por mutaciones de punteros en pasos posteriores. |

---

## 4. Detalles de Implementación por Módulo

### 4.1. `backend/src/solver/engine/frac_m.py`
- **Aritmética:**
  - Suma y resta término a término de constantes y coeficientes de $M$.
  - Negación unaria directa (`-self.const`, `-self.m`).
  - Multiplicación distributiva exacta:
    $$(a + bM)(c + 0M) = ac + bcM$$
    Lanza `ValueError` si $b \neq 0$ y $d \neq 0$ ($M^2$ no admisible).
- **Orden lexicográfico (`@total_ordering`):**
  - Si `self.m != other.m`: el orden lo decide `self.m < other.m`.
  - Si `self.m == other.m`: el orden lo decide `self.const < other.const`.
  - Esto garantiza que $-M - 30 < -40$ y que $M > 1000000$, esencial para que el motor seleccione la variable entrante correcta sin heurísticas numéricas.
- **Formateo canónico:**
  - Cumple con la especificación de salida del contrato §0: términos sin $M$ (`"5"`, `"3/4"`, `"-7/2"`), con $M$ (`"M"`, `"-M"`, `"-3M"`, `"2M+1/3"`, `"-M-30"`), y caso nulo (`"0"`).

### 4.2. `backend/src/solver/engine/tableau.py`
- **Separación de roles:**
  - `pivot(leaving, entering)` ejecuta exclusivamente el pivoteo Gauss-Jordan sobre `rows`:
    - Normaliza la fila entrante dividiendo entre el elemento pivote.
    - Actualiza el coeficiente $C_B$ de la nueva variable básica usando $C_j$.
    - Elimina la variable entrante en las demás filas mediante combinación lineal.
    - No calcula $Z_j$ ni $C_j - Z_j$ en este paso.
  - `evaluate()` calcula las filas derivadas:
    - $Z_j = \sum (C_{B_i} \cdot a_{ij})$ para todas las columnas (incluyendo $b_j$).
    - $C_j - Z_j$ para todas las columnas de variables (excluyendo $b_j$).
- **Reglas por sentido del objetivo:**
  - **Maximizando:**
    - Variable entrante: columna con $C_j - Z_j > 0$ más positivo (máximo bajo orden lexicográfico de `FracM`).
    - Optimalidad: todos los $C_j - Z_j \le 0$.
  - **Minimizando:**
    - Variable entrante: columna con $C_j - Z_j < 0$ más negativo (mínimo bajo orden lexicográfico de `FracM`).
    - Optimalidad: todos los $C_j - Z_j \ge 0$.
- **Prueba de la razón mínima:**
  - Considera únicamente filas donde el coeficiente en la columna entrante sea estrictamente positivo ($a_{ij} > 0$).
  - Calcula la razón $b_i / a_{ij}$ usando división exacta de `Fraction`.
  - Detecta empates (`ties`) para el diagnóstico de degeneración.

### 4.3. `backend/src/solver/engine/solver.py`
- Controla el ciclo principal:
  1. Verifica `tableau.is_optimal()` $\to$ `status="optimal"`.
  2. Obtiene `tableau.get_entering_variable()`. Si es `None` $\to$ `status="optimal"`.
  3. Obtiene `tableau.get_leaving_variable(entering)`. Si es `None` $\to$ `status="unbounded"`.
  4. Extrae `pivot_value = tableau.get_pivot_value(leaving, entering)`.
  5. Ejecuta `tableau.pivot(leaving, entering).evaluate()`.
  6. Registra la iteración con snapshots y metadata.
  7. Si supera `max_iter` (por defecto 200) $\to$ lanza `RuntimeError` para advertir ciclado o error de entrada.

---

## 5. Verificación y Resultados de Pruebas

Toda la suite de pruebas del backend se ejecutó exitosamente con `pytest`:

```text
backend\tests\test_api_contract.py .....                                 [  7%]
backend\tests\test_frac_m.py ......................                      [ 39%]
backend\tests\test_methods_fixtures.py ssssss                            [ 48%]
backend\tests\test_solver.py ........                                    [ 60%]
backend\tests\test_tableau.py ...........................                [100%]
======================== 62 passed, 6 skipped in 1.26s =========================
```

- **62 pruebas aprobadas** (incluyendo 57 pruebas del engine y 5 de contratos de API generales).
- **6 pruebas skipped** correspondientes a `test_methods_fixtures.py`, las cuales dependen de la implementación de los adaptadores de métodos (`methods/simplex.py` y `methods/big_m.py`), que constituyen el siguiente hito del proyecto.

---

## 6. Recomendaciones para las Siguientes Fases

1. **Implementación de `methods/simplex.py` y `methods/big_m.py`:**
   - Recordar que `Tableau.cj_zj` tiene tamaño `len(columns) - 1`. Al formatear o iterar columnas en la API, mapear $C_j - Z_j$ únicamente sobre las variables.
   - En la construcción del tableau inicial, inyectar `Row.cells` como listas de `Fraction` (parseadas a partir de los strings de entrada mediante `Fraction(Decimal(s))`).
2. **Presentación en el Stepper (Iteración 0):**
   - Dado que `solver.solve()` genera iteraciones a partir del primer pivote ($1..k$), la capa del método o endpoint `/api/resolver` debe anteponer la iteración 0 (`Iteration(number=0, tableau=initial_tableau, ...)`) si el frontend requiere visualizar la tabla antes del primer paso.
3. **Casos especiales (`SpecialCase`):**
   - El motor ya provee `ties` en cada iteración, facilitando al intérprete de cada método registrar el caso especial `degenerate_pivot` cuando `len(iteration.ties) > 1`.
