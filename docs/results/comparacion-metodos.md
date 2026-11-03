# Comparación Integral de Métodos: Simplex, Gran M y Simplex Dual

> **Proyecto:** `solver` (Investigación de Operaciones 1)  
> **Grupo:** 3 — Métodos: Simplex Primal (con Problema Equivalente), Gran M y Simplex Dual  
> **Lineamiento del curso:** *"¿Mismo problema?: Sí. El informe compara los métodos: pasos o iteraciones, tiempo y cuál conviene en cada situación."*  
> **Fecha:** Noviembre 2026  
> **Estado:** Implementado, verificado y validado contra suite completa de pruebas (`150 passed`).

---

## 1. Resumen Ejecutivo y Lineamiento del Curso

El lineamiento formal de la asignatura establece para los grupos clasificados bajo la modalidad **“¿Mismo problema?: Sí”**:

> *“Los dos métodos resuelven el mismo problema real y sus resultados deben coincidir. Si un método no admite el tipo de restricciones del problema, se transforma en uno equivalente (por ejemplo, resolver el dual o cambio de variables) y se explica en el informe. El informe compara los métodos: pasos o iteraciones, tiempo y cuál conviene en cada situación.”*

En nuestro sistema (`solver`), este requisito no solo se cumple para dos métodos, sino que se extiende a **tres métodos canónicos de programación lineal**:

1. **Simplex Primal estándar con Transformación al Problema Equivalente (`simplex`)**:
   - Para problemas en forma canónica directa ($\le$ con $\mathbf{b} \ge \mathbf{0}$), opera de forma estándar iniciando en el origen $\mathbf{x} = \mathbf{0}$ con holguras puras $\mathbf{s} = \mathbf{b}$.
   - Para problemas con restricciones $\ge$ y cotas inferiores (como el modelo real de Procafecol S.A.), aplica de manera automática una **transformación algebraica afín al problema equivalente** ($\mathbf{x} = \mathbf{x}^0 + \mathbf{T}\mathbf{y}$). Resuelve el modelo transformado en variables $\mathbf{y} \ge \mathbf{0}$ mediante el bucle primal de Simplex estándar y reconstruye la base canónica final en las variables naturales del problema mediante `restore_tableau`. No requiere variables artificiales ni aritmética simbólica.
2. **Método de la Gran M (`big_m`)**:
   - Normaliza cualquier lado derecho negativo multiplicando la fila por $-1$.
   - Agrega holguras $+s_i$ en restricciones $\le$, excesos $-e_i$ y artificiales $+a_i$ en restricciones $\ge$, y artificiales $+a_i$ en igualdades $=$.
   - Penaliza las variables artificiales con un costo simbólico exacto $\pm M$ utilizando la estructura `FracM(const, m)` con orden lexicográfico estricto, garantizando convergencia sin aproximaciones numéricas ni errores de desbordamiento.
3. **Método Simplex Dual (`dual_simplex`)**:
   - Normaliza todo el conjunto de restricciones a formato $\le$ multiplicando las restricciones $\ge$ por $-1$ (lo que genera lados derechos negativos en la tabla inicial) y desdoblando las igualdades $=$ en dos desigualdades opuestas ($\le$ con $b_i$ y $\le$ con $-b_i$).
   - Añade **exclusivamente variables de holgura $+s_1, \dots, +s_m$**, prescindiendo en su totalidad de variables de exceso y de variables artificiales.
   - Ejecuta el algoritmo `solve_dual`:
     - **Fase Dual:** mientras existan filas básicas con $b_r < 0$, selecciona la fila saliente más negativa ($b_r = \min_i b_i$) y la columna entrante mediante la razón mínima dual $\min_{j: a_{rj} < 0} |(C_j - Z_j) / a_{rj}|$, restaurando la factibilidad primal ($\mathbf{b} \ge \mathbf{0}$).
     - **Fase Primal:** una vez lograda la factibilidad primal, si todavía existen columnas que mejoran la función objetivo ($C_j - Z_j > 0$ en maximización o $C_j - Z_j < 0$ en minimización), ejecuta pivotes primales hasta alcanzar la optimalidad.

---

## 2. Configuración Experimental y Metodología de Medición

Para asegurar la rigurosidad científica y la reproducibilidad de los resultados, las pruebas se ejecutaron bajo las siguientes condiciones controladas:

- **Aritmética Exacta:** Todas las operaciones de pivoteo, razones y cálculos de función objetivo utilizan `fractions.Fraction` (fracciones exactas sin redondeo de punto flotante) y `FracM` (álgebra simbólica de dos componentes exactos: parte real constante y coeficiente de $M$).
- **Límite de Iteraciones:** 200 iteraciones máximas para evitar ciclos en casos patológicos.
- **Entorno de Ejecución:** Python 3.13 en entorno Windows 11 x64.
- **Protocolo de Medición de Tiempo:**
  - Se utilizó `time.perf_counter()` con resolución de nanosegundos.
  - El tiempo reportado cubre el ciclo de vida completo del método: **construcción del tableau inicial (`build`) + resolución (`solve` / `solve_dual`) + interpretación y extracción de solución (`interpret`)**.
  - Se realizaron **5 corridas de calentamiento (warmup)** para mitigar el impacto de importaciones dinámicas y optimizaciones JIT de Python, seguidas de **50 corridas consecutivas**, reportando tanto la **media aritmética** como la **mediana** en milisegundos (ms).
- **Distinción Métrica:**
  - **Tablas en el Stepper (`len(iterations)`):** Cuenta el tableau inicial (iteración 0) más todas las tablas intermedias y final.
  - **Pivotes Efectivos (`len(iterations) - 1`):** Número de transformaciones de Gauss-Jordan realizadas.

---

## 3. Comparación Detallada en el Caso Real: Procafecol S.A. (`bakery-real.json`)

### 3.1 Descripción del Modelo Real
El problema real corresponde a la optimización mensual de mezcla de producción de café empacado para **Procafecol S.A. (Juan Valdez)**, con 5 variables de decisión ($x_1$: Tradicional, $x_2$: Premium Balanceado, $x_3$: Orgánico, $x_4$: Origen Regional, $x_5$: Mujeres Cafeteras) y 13 restricciones (5 capacidades de procesamiento y recursos $\le$, 2 requerimientos comerciales y de mezcla $\ge$, y 6 cotas operativas de mercado $\ge$ y $\le$):

$$\max Z = 14.20\,x_1 + 18.50\,x_2 + 22.20\,x_3 + 24.50\,x_4 + 26.00\,x_5$$

### 3.2 Tabla Comparativa de Rendimiento en `bakery-real`

| Criterio | Simplex (`simplex`) | Gran M (`big_m`) | Simplex Dual (`dual_simplex`) |
|---|---|---|---|
| **Mecanismo inicial** | Cambio afín $\mathbf{x} = \mathbf{x}^0 + \mathbf{T}\mathbf{y}$ | +5 excesos ($e_1..e_5$) y +5 artificiales ($a_1..a_5$) con $-M$ | Multiplicación de las 5 restricciones $\ge$ por $-1$ |
| **Estado de terminación** | `optimal` | `optimal` | `optimal` |
| **Valor óptimo $Z^*$** | $\mathbf{\frac{135857}{36} \approx 3773.8056}$ | $\mathbf{\frac{135857}{36} \approx 3773.8056}$ | $\mathbf{\frac{135857}{36} \approx 3773.8056}$ |
| **Solución óptima $\mathbf{x}^*$** | $(35,\, \frac{1595}{18},\, 0,\, 35,\, 30)$ | $(35,\, \frac{1595}{18},\, 0,\, 35,\, 30)$ | $(35,\, \frac{1595}{18},\, 0,\, 35,\, 30)$ |
| **Pivotes totales** | **4 pivotes** (0 duales + 4 primales) | **9 pivotes** (6 expulsión $a_i$ + 3 primales) | **12 pivotes** (4 duales + 8 primales) |
| **Tablas en Stepper** | **5 tablas** | **10 tablas** | **13 tablas** |
| **Dimensión de la tabla** | $\mathbf{13 \times 19}$ (5 vars, 13 $s_i$, 1 RHS) | $13 \times 24$ (5 vars, 8 $s_i$, 5 $e_i$, 5 $a_i$, 1 RHS) | $\mathbf{13 \times 19}$ (5 vars, 13 $s_i$, 1 RHS) |
| **Variables artificiales** | **0** | 5 ($a_1, \dots, a_5$) | **0** |
| **Tiempo medio (50 corridas)** | **16.17 ms** | 23.39 ms | 23.76 ms |
| **Tiempo mediana** | **16.06 ms** | 23.10 ms | 23.59 ms |
| **Tiempo por pivote** | $\approx 4.04$ ms / pivote (incluye `restore_tableau`) | $\approx 2.60$ ms / pivote (tabla grande $13 \times 24$ con $M$) | $\approx 1.98$ ms / pivote (tabla compacta $13 \times 19$ sin $M$) |

### 3.3 Trazabilidad Paso a Paso: Secuencia de Pivotes y Evolución de $Z$

#### A. Simplex con Transformación al Problema Equivalente (4 pivotes)
Inicia en el vértice factible interior $\mathbf{x}^0 = (35,\, 60,\, 0,\, \frac{127}{6},\, \frac{21}{2})$ con $Z_0 = \frac{28783}{12} \approx 2398.58$:
- **Iteración 0:** $Z = \frac{28783}{12}$. Todas las holguras son no negativas ($\mathbf{b}_y \ge \mathbf{0}$).
- **Iteración 1:** Entra `Origen Regional` ($y_4$), sale $s_{11}$, pivote $= \frac{4}{3} \implies Z = 2860$.
- **Iteración 2:** Entra `Mujeres Cafeteras` ($y_5$), sale $s_5$ (Café verde especial), pivote $= \frac{59}{50} \implies Z = 3237$.
- **Iteración 3:** Entra `Premium Balanceado` ($y_2$), sale $s_1$ (Tostión), pivote $= \frac{18}{5} \implies Z = \frac{30151}{8} = 3768.875$.
- **Iteración 4:** Entra $s_{11}$, sale $s_{13}$ (Cota superior Mujeres Cafeteras), pivote $= 1 \implies Z^* = \frac{135857}{36} \approx 3773.8056$.

#### B. Gran M con Penalización Simbólica (9 pivotes)
Inicia en el origen artificial con costo penalizado por las 5 variables artificiales:
- **Iteración 0:** $Z = -\frac{341}{2}M$.
- **Iteraciones 1 a 6 (Expulsión de artificiales):**
  - Iter 1: Entra `Mujeres Cafeteras`, sale $a_2$, pivote $= \frac{3}{4} \implies Z = -\frac{341}{2}M$.
  - Iter 2: Entra `Premium Balanceado`, sale $a_4$, pivote $= 1 \implies Z = -\frac{201}{2}M + 815$.
  - Iter 3: Entra `Tradicional`, sale $a_5$, pivote $= \frac{1}{3} \implies Z = -97M + \frac{8493}{10}$.
  - Iter 4: Entra $a_2$, sale $a_3$, pivote $= 4 \implies Z = -\frac{307}{8}M + 1325$.
  - Iter 5: Entra $e_5$, sale $a_2$, pivote $= \frac{3}{4} \implies Z = -30M + \frac{4846}{3}$.
  - Iter 6: Entra $e_4$, sale $s_8$, pivote $= \frac{1}{3} \implies Z = -5M + \frac{4589}{2}$.
- **Iteración 7:** Entra `Origen Regional`, sale la última artificial $a_1$, pivote $= 3 \implies Z = \frac{14567}{6} \approx 2427.83$ (Se alcanza la región factible primal).
- **Iteraciones 8 a 9 (Optimización Primal):**
  - Iter 8: Entra $e_2$, sale $s_5$, pivote $= \frac{118}{75} \implies Z = \frac{6489}{2} = 3244.5$.
  - Iter 9: Entra $e_1$, sale $s_1$, pivote $= \frac{18}{5} \implies Z^* = \frac{135857}{36} \approx 3773.8056$.

#### C. Simplex Dual (12 pivotes = 4 duales + 8 primales)
Inicia en el origen $\mathbf{x} = \mathbf{0}$ con $Z = 0$, teniendo 4 holguras negativas en el RHS: $s_6 = -95$, $s_8 = -35$, $s_9 = -30$, $s_{12} = -\frac{21}{2}$:
- **Fase Dual (Iteraciones 1 a 4 — Búsqueda de factibilidad primal):**
  - Iter 1: Sale $s_6$ ($b = -95$), entra `Tradicional`, pivote $= -1 \implies Z = 1349$.
  - Iter 2: Sale $s_9$ ($b = -30$), entra `Premium Balanceado`, pivote $= -1 \implies Z = 1478$.
  - Iter 3: Sale $s_7$ ($b = -\frac{95}{4}$), entra `Orgánico`, pivote $= -\frac{3}{4} \implies Z = 2181$.
  - Iter 4: Sale $s_{12}$ ($b = -\frac{21}{2}$), entra `Mujeres Cafeteras`, pivote $= -1 \implies Z = \frac{22209}{10} = 2220.9$.  
    *(En este punto, todos los lados derechos son $\ge 0$; se ha recuperado la factibilidad primal).*
- **Fase Primal (Iteraciones 5 a 12 — Optimización del margen):**
  - Como el origen no era dual-factible al ser un problema de maximización con costos de beneficio positivos, el vector $C_j - Z_j$ aún presenta indicadores positivos tras la fase dual.
  - Iter 5: Entra $s_7$, sale $s_{10}$, pivote $= \frac{4}{3} \implies Z = 2528$.
  - Iter 6: Entra $s_{12}$, sale $s_5$, pivote $= \frac{59}{50} \implies Z = 3035$.
  - Iter 7: Entra $s_6$, sale $s_2$, pivote $= \frac{5}{2} \implies Z = \frac{17589}{5} = 3517.8$.
  - Iter 8: Entra $s_9$, sale $s_3$, pivote $= \frac{67}{125} \implies Z = \frac{480091}{134} \approx 3582.77$.
  - Iter 9: Entra $s_2$, sale $s_1$, pivote $= \frac{24}{67} \implies Z = \frac{22039}{6} \approx 3673.17$.
  - Iter 10: Entra $s_3$, sale $s_8$, pivote $= \frac{15}{2} \implies Z = \frac{67127}{18} \approx 3729.28$.
  - Iter 11: Entra $s_{10}$, sale $s_{13}$, pivote $= 1 \implies Z = \frac{67127}{18}$ *(paso degenerado)*.
  - Iter 12: Entra `Origen Regional`, sale `Orgánico`, pivote $= 1 \implies Z^* = \frac{135857}{36} \approx 3773.8056$.

### 3.4 Concordancia Exacta en el Análisis de Sensibilidad
Los tres métodos arrojan exactamente los mismos precios sombra, costos reducidos y holguras finales sobre la instancia de Procafecol:

| Restricción / Variable | Tipo | Estado | Precio Sombra ($\pi_i$) / Costo Reducido ($r_j$) | Interpretación Económica |
|---|---|---|---|---|
| **Tostión** | $\le 720$ | **Activa** | $\mathbf{\frac{185}{36} \approx 5.139}$ | Cada hora adicional de tostación incrementa la utilidad en \$5.139 millones. |
| **Café verde especial** | $\le 76.7$ | **Activa** | $\mathbf{\frac{850}{531} \approx 1.601}$ | Cada tonelada extra de grano verde especial aporta \$1.601 millones. |
| **Cota mín Tradicional** | $\ge 35$ | **Activa** | $\mathbf{-\frac{101}{45} \approx -2.244}$ | Forzar 1 tonelada más de Tradicional reduce la utilidad en \$2.244 millones. |
| **Cota máx Mujeres Cafeteras** | $\le 30$ | **Activa** | $\mathbf{\frac{71}{72} \approx 0.986}$ | Ampliar la capacidad de acopio de Mujeres Cafeteras en 1 ton rinde \$0.986 millones. |
| **Orgánico ($x_3$)** | Variable | **No básica** ($x_3 = 0$) | Costo Reducido: $\mathbf{-\frac{229}{180} \approx -1.272}$ | El margen de Orgánico debería aumentar en \$1.272 M para ser rentable producirlo. |

---

## 4. Comparación en los 6 Escenarios Canónicos y de Prueba

Para contrastar el comportamiento de los tres métodos bajo distintas geometrías del poliedro (infactibilidad, no acotamiento, minimización, cotas e igualdades), se evaluaron seis escenarios canónicos:

### Caso 1: `bakery-real` (Maximización con restricciones $\le$ y $\ge$, Caso Real Procafecol)
- **Simplex (Problema Equivalente):** 5 tablas, 4 pivotes, $13 \times 19$, **16.17 ms** (**Ganador en tiempo y pasos**).
- **Gran M:** 10 tablas, 9 pivotes, $13 \times 24$, 23.39 ms.
- **Simplex Dual:** 13 tablas, 12 pivotes (4 duales + 8 primales), $13 \times 19$, 23.76 ms.

### Caso 2: `simplex-grupo1` (Maximización puramente $\le$ con lados derechos $\ge 0$, Contenedores en la Nube)
- Modelo: 3 variables de decisión, 4 restricciones de capacidad de infraestructura en la nube ($\le$).
- **Simplex:** 4 tablas (3 pivotes), $4 \times 8$, **1.44 ms**, $Z^* = 1575$.
- **Gran M:** 4 tablas (3 pivotes), $4 \times 8$, **1.44 ms**, $Z^* = 1575$.
- **Simplex Dual:** 4 tablas (3 pivotes), $4 \times 8$, **1.46 ms**, $Z^* = 1575$.
- *Comportamiento:* Al no existir lados derechos negativos en la tabla inicial, Simplex Dual entra de inmediato a su bucle primal; los tres métodos ejecutan la misma secuencia de pivotes (`Procesamiento` $\to s_3$, `Base de datos` $\to s_2$, `Web` $\to s_1$) con tiempos virtualmente idénticos.

### Caso 3: `test-infeasible` ($x_1 \le 2,\, x_1 \ge 5$, Región Factible Vacía)
- **Simplex:** `not_admissible` (**0.021 ms**). Detecta de forma inmediata que el cambio afín genera lados derechos negativos en el problema transformado ($\mathbf{b}_y \not\ge \mathbf{0}$) sin admitir base factible.
- **Gran M:** `infeasible` en 2 tablas (1 pivote), $2 \times 5$, **0.375 ms**. La variable artificial $a_1$ queda en la base óptima con valor $3 > 0$ ($Z = -3M + 2$).
- **Simplex Dual:** `infeasible` en 2 tablas (1 pivote dual), $2 \times 4$, **0.302 ms** (**20% más rápido que Gran M** y con una columna menos). Detecta que la fila básica $s_1$ tiene RHS $= -3 < 0$ y todos sus coeficientes tecnológicos son $\ge 0$, demostrando infactibilidad primal sin construir variables artificiales ni requerir optimización previa.

### Caso 4: `test-unbounded` ($\max x_1 + x_2 \text{ s.a. } x_1 - x_2 \le 2$)
- **Simplex:** `unbounded` en 2 tablas (1 pivote), $1 \times 4$, **0.243 ms**.
- **Gran M:** `unbounded` en 2 tablas (1 pivote), $1 \times 4$, **0.248 ms**.
- **Simplex Dual:** `unbounded` en 2 tablas (1 pivote), $1 \times 4$, **0.249 ms**.
- *Comportamiento:* Los tres métodos detectan no acotamiento cuando la variable candidata a entrar ($x_2$) no tiene coeficientes estrictamente positivos en su columna, impidiendo calcular una razón de salida.

### Caso 5: Minimización canónica con restricciones $\ge$ (`dual-classic-min`)
$$\min Z = 3x_1 + 2x_2 \quad \text{s.a.} \quad 3x_1 + x_2 \ge 3, \quad 4x_1 + 3x_2 \ge 6, \quad x_1 + 2x_2 \le 3$$
- En este modelo de minimización con costos positivos, el origen $\mathbf{x} = \mathbf{0}$ es **dual-factible** ($C_j - Z_j = [3, 2, 0, 0, 0] \ge 0$).
- **Simplex Dual:** **3 tablas (2 pivotes duales)**, $3 \times 6$, **0.731 ms** (**Ganador indiscutible en tiempo y dimensiones**). Elimina los RHS negativos en 2 pivotes puramente duales (sale $s_2 \to$ entra $x_2$; sale $s_1 \to$ entra $x_1$) y termina directamente en el óptimo ($Z^* = 21/5$) con 0 pivotes primales.
- **Gran M:** 3 tablas (2 pivotes), $3 \times 8$, **0.954 ms** (30% más lento debido al cálculo simbólico con 2 excesos y 2 artificiales).
- **Simplex:** 2 tablas (1 pivote), $3 \times 6$, **1.218 ms** (a pesar de requerir solo 1 pivote tras el cambio afín, el overhead de cálculo matricial de `restore_tableau` lo hace 66% más lento que Simplex Dual).

### Caso 6: Restricción de igualdad estricta (`equality-min`)
$$\min Z = 2x_1 + 3x_2 \quad \text{s.a.} \quad x_1 + x_2 = 10, \quad x_1 \le 4$$
- **Simplex:** `not_admissible` (0.001 ms, Simplex estándar rechaza igualdades $=$).
- **Gran M:** **3 tablas (2 pivotes)**, dimensión compacta **$2 \times 5$**, **0.518 ms** (**Ganador en tiempo y tamaño de tabla**). Añade solo 1 variable artificial para la igualdad.
- **Simplex Dual:** 3 tablas (2 pivotes duales), dimensión **$3 \times 6$**, **0.696 ms**. Desdobla la igualdad en dos desigualdades ($x_1 + x_2 \le 10$ y $-x_1 - x_2 \le -10$), sumando una fila y una columna adicional de holgura.

---

### 4.1 Tabla Maestra Consolidada de los 6 Escenarios

| Caso | Tipo de Problema | Dimensiones | Simplex (P. Eq.) | Gran M | Simplex Dual | Ganador y Razón |
|---|---|---|---|---|---|---|
| **`bakery-real`** | Max con $\le$ y $\ge$ (Procafecol) | 5 vars, 13 restr | 5 tab / 4 piv ($13 \times 19$)<br>**16.17 ms** | 10 tab / 9 piv ($13 \times 24$)<br>23.39 ms | 13 tab / 12 piv ($13 \times 19$)<br>23.76 ms | **Simplex**: Vértice inicial $\mathbf{x}^0$ ahorra 8 pivotes frente a Dual y 5 frente a Gran M. |
| **`simplex-grupo1`** | Max puramente $\le$, RHS $\ge 0$ | 3 vars, 4 restr | 4 tab / 3 piv ($4 \times 8$)<br>**1.44 ms** | 4 tab / 3 piv ($4 \times 8$)<br>**1.44 ms** | 4 tab / 3 piv ($4 \times 8$)<br>1.46 ms | **Simplex / Gran M**: Empate técnico; Simplex es conceptualmente más simple. |
| **`test-infeasible`** | Región vacía ($\le 2$ y $\ge 5$) | 1 var, 2 restr | `not_admissible`<br>0.021 ms | 2 tab / 1 piv ($2 \times 5$)<br>0.375 ms | 2 tab / 1 piv ($2 \times 4$)<br>**0.302 ms** | **Simplex Dual**: 20% más rápido que Gran M y sin variables artificiales. |
| **`test-unbounded`** | No acotado ($\max x_1+x_2$) | 2 vars, 1 restr | 2 tab / 1 piv ($1 \times 4$)<br>**0.243 ms** | 2 tab / 1 piv ($1 \times 4$)<br>0.248 ms | 2 tab / 1 piv ($1 \times 4$)<br>0.249 ms | **Empate general**: Los tres identifican columna sin cota positiva en el primer paso. |
| **`dual-classic-min`** | Min con $\ge$ (costos $\ge 0$) | 2 vars, 3 restr | 2 tab / 1 piv ($3 \times 6$)<br>1.218 ms | 3 tab / 2 piv ($3 \times 8$)<br>0.954 ms | 3 tab / 2 piv ($3 \times 6$)<br>**0.731 ms** | **Simplex Dual**: Tabla mínima, convergencia dual pura directa (30% más rápido que Gran M). |
| **`equality-min`** | Min con igualdad ($=$) | 2 vars, 2 restr | `not_admissible`<br>0.001 ms | 3 tab / 2 piv ($2 \times 5$)<br>**0.518 ms** | 3 tab / 2 piv ($3 \times 6$)<br>0.696 ms | **Gran M**: 1 fila menos que Dual al no requerir desdoblamiento de la igualdad. |

---

## 5. Análisis Comparativo Transversal

### 5.1 Complejidad Espacial y Dimensión del Tableau

La memoria requerida y el ancho de las filas están determinados por la cantidad de variables auxiliares añadidas:

$$\begin{aligned}
\text{Columnas Simplex:} \quad & C_{\text{simplex}} = n + m + 1 \\
\text{Columnas Simplex Dual:} \quad & C_{\text{dual}} = n + m + m_{=} + 1 \\
\text{Columnas Gran M:} \quad & C_{\text{big\_m}} = n + m_{\le} + 2m_{\ge} + m_{=} + 1
\end{aligned}$$

- **Simplex Dual vs. Gran M:** En problemas con restricciones $\ge$ y sin igualdades, Simplex Dual ahorra **2 columnas por cada restricción $\ge$** (ahorra la variable de exceso $e_i$ y la variable artificial $a_i$). En Procafecol, esto reduce la tabla de 24 a 19 columnas (**-21% de columnas**).
- **Simplex Dual vs. Simplex:** Cuando no hay igualdades, Simplex Dual y Simplex tienen exactamente las mismas dimensiones ($m \times (n + m + 1)$). Sin embargo, si existen igualdades ($m_{=} > 0$), Simplex Dual añade 1 fila y 1 columna adicional por cada igualdad desdoblada, mientras que Gran M mantiene $m$ filas agregando solo 1 columna artificial.

### 5.2 Costo por Pivote vs. Número de Iteraciones

- **Costo unitario por pivote:**
  - En Simplex Dual, cada pivote sobre tabla $13 \times 19$ sin términos $M$ toma aproximadamente **$1.98$ ms**, mientras que en Gran M toma **$2.60$ ms** (un **24% más rápido por pivote** gracias a la ausencia de aritmética simbólica $M$ y al menor número de columnas).
- **Número de pivotes y Factibilidad Dual Inicial:**
  - La ventaja en el número de pivotes depende críticamente de la **orientación del problema** y del signo de los coeficientes de la función objetivo:
    - En **Minimización con costos no negativos y restricciones $\ge$** (`dual-classic-min`), el origen es dual-factible ($C_j - Z_j \ge 0$). Simplex Dual requiere solo pivotes duales para factibilizar $\mathbf{b} \ge \mathbf{0}$, convergiendo inmediatamente en el óptimo con el menor tiempo del benchmark.
    - En **Maximización con coeficientes de beneficio positivos y restricciones $\ge$** (`bakery-real`), el origen no es dual-factible ($C_j - Z_j > 0$). Por ende, Simplex Dual debe realizar 4 pivotes duales para eliminar las holguras negativas y luego 8 pivotes primales para maximizar la función objetivo (12 pivotes en total). En este caso, **Simplex con transformación afín resulta superior** porque arranca directamente desde un vértice interior factible $\mathbf{x}^0$, requiriendo únicamente 4 pivotes primales.

---

## 6. ¿Cuál Método Conviene en Cada Situación? (Guía de Decisión)

| Escenario Operativo | Método Recomendado | Justificación Técnica |
|---|---|---|
| **Problemas estándar ($\le$ con $\text{RHS} \ge 0$)** | **Simplex Estándar** | No requiere verificar fase dual ni manejar variables artificiales. Es la implementación más directa y con menor consumo computacional. |
| **Minimización con restricciones $\ge$ y costos $c_j \ge 0$** | **Simplex Dual** | **Ganador absoluto.** El origen es dual-factible. Resuelve sin variables artificiales, en menos tiempo que Gran M y con tabla mínima. |
| **Maximización con restricciones $\ge$ y cotas inferiores** | **Simplex con Problema Equivalente** | **Ganador en iteraciones.** Si es factible derivar un punto base $\mathbf{x}^0 \ge \mathbf{0}$, converge en una fracción de las iteraciones de Gran M y Simplex Dual (4 vs. 9 vs. 12). |
| **Problemas con restricciones de igualdad ($=$)** | **Gran M** (o Simplex Dual) | Gran M añade solo 1 fila y 1 artificial por igualdad ($2 \times 5$ vs $3 \times 6$), siendo 25% más rápido que desdoblar la igualdad en Simplex Dual. Si se desea evitar la constante $M$, Simplex Dual es la mejor alternativa sin penalización simbólica. |
| **Detección temprana de Infactibilidad** | **Simplex Dual** | Detecta la infactibilidad en el primer pivote dual cuando una fila tiene $b_r < 0$ y coeficientes tecnológicos $\ge 0$, sin necesidad de completar un proceso de optimización artificial. |
| **Análisis Post-óptimo y Nuevas Restricciones** | **Simplex Dual** | Si se agrega una nueva restricción que viola la solución óptima actual, Simplex Dual re-optimiza desde el tableau óptimo anterior en 1 o 2 pivotes duales sin re-resolver desde cero. |

---

## 7. Conclusiones y Recomendaciones del Sprint

1. **Equivalencia Numérica Absoluta:** Los tres métodos implementados convergen al mismo valor óptimo ($Z^* = \frac{135857}{36} \approx 3773.8056$) y al mismo vector de decisión en el caso real de Procafecol, validando completamente la corrección matemática de los tres algoritmos.
2. **Complementariedad Primal-Dual:**
   - La **Transformación al Problema Equivalente** es la estrategia más eficiente cuando se conoce o puede despejarse un vértice inicial admisible en problemas de maximización con cotas inferiores.
   - **Simplex Dual** es el método óptimo para minimización con restricciones $\ge$ y análisis de sensibilidad post-óptimo, eliminando la necesidad de variables artificiales.
   - **Gran M** proporciona la máxima universalidad estructural, manejando igualdades estrictas de manera compacta mediante penalización simbólica exacta `FracM`.
