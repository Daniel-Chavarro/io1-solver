# Informe Comparativo: Simplex, Gran M y Simplex Dual

> **Grupo 3 · IO1 · Entrega 2 — Noviembre 2026**  
> Daniel Chavarro (P1) · Jorge Méndez (P2) · Nicolás Velazco (P3)

---

## 1. Objetivo

Comparar cuantitativamente los tres métodos de programación lineal implementados en el motor del proyecto: el **método Simplex Primal** (incorporando la transformación algebraica afín al problema equivalente para restricciones $\ge$), el **método de la Gran M** y el **método Simplex Dual**, evaluando su comportamiento sobre el caso real de Procafecol S.A. y escenarios canónicos del curso mediante:

- **Número de iteraciones y pivotes** (pivotes primales vs. pivotes duales vs. expulsión de variables artificiales).
- **Tiempo de cómputo** (mediana y promedio de 50 ejecuciones consecutivas con warmup, en ms).
- **Dimensiones del tableau** (filas $\times$ columnas de variables y holguras).
- **Guía de decisión técnica**: cuál método conviene en cada situación operativa.
- **Verificación del caso real** contra la solución óptima y análisis de sensibilidad de **Excel Solver**.

---

## 2. Motor y Configuración Experimental

El motor de optimización (`backend/src/solver/`) opera de manera exacta y desacoplada mediante tres adaptadores especializados:

| Parámetro | Valor y Mecanismo |
|---|---|
| **Aritmética** | Exacta — `fractions.Fraction` (sin error de redondeo) y `FracM` (álgebra simbólica $c + mM$ con orden lexicográfico). |
| **Bucle Primal (`solve`)** | Criterio de entrada de Dantzig (mayor $C_j - Z_j > 0$ en max, menor en min) y criterio de salida por razón mínima positiva $b_i / a_{ij} > 0$. |
| **Bucle Dual (`solve_dual`)** | **Fase dual:** selecciona fila saliente con $b_r < 0$ más negativo y columna entrante mediante $\min_{j: a_{rj} < 0} |(C_j - Z_j) / a_{rj}|$ hasta lograr $\mathbf{b} \ge \mathbf{0}$. **Fase primal:** pivoteo primal si restan $C_j - Z_j$ de mejora. |
| **Problema Equivalente (`simplex.py`)** | Transformación afín $\mathbf{x} = \mathbf{x}^0 + \mathbf{T}\mathbf{y}$ desde un vértice factible derivado $\mathbf{x}^0$, resolviendo en $\mathbf{y} \ge \mathbf{0}$ con Simplex estándar y canonicalizando la base con `restore_tableau`. |
| **Límite de iteraciones** | 200 iteraciones máximas. |
| **Entorno de ejecución** | Python 3.13, Windows 11 x64 (tiempos medidos con `time.perf_counter()` cubriendo `build + solve + interpret`). |

---

## 3. Resultados Experimentales por Caso

### 3.1 Caso Real — Plan de Producción Procafecol S.A. (`bakery-real.json`)
Modelo real de mezcla óptima mensual de café empacado para Procafecol (Juan Valdez): **5 variables de decisión**, **13 restricciones** (8 de tipo $\le$ y 5 de tipo $\ge$):

$$\max Z = 14.20\,x_1 + 18.50\,x_2 + 22.20\,x_3 + 24.50\,x_4 + 26.00\,x_5$$

| Método | Estado | Pivotes Totales | Desglose Pivotes | Tablas Stepper | Tiempo Medio (Mediana) | Dimensión Tableau | Valor Óptimo $Z^*$ |
|---|---|---|---|---|---|---|---|
| **Simplex (P. Eq.)** | `optimal` | **4** | 4 primales | **5** | **16.17 ms** (16.06 ms) | $\mathbf{13 \times 19}$ | $\mathbf{\frac{135857}{36} \approx 3773.81}$ |
| **Gran M** | `optimal` | **9** | 6 expulsión $a_i$ + 3 primales | **10** | 23.39 ms (23.10 ms) | $13 \times 24$ | $\mathbf{\frac{135857}{36} \approx 3773.81}$ |
| **Simplex Dual** | `optimal` | **12** | 4 duales + 8 primales | **13** | 23.76 ms (23.59 ms) | $\mathbf{13 \times 19}$ | $\mathbf{\frac{135857}{36} \approx 3773.81}$ |

- **Convergencia idéntica:** Los tres métodos obtienen la misma solución óptima: $\mathbf{x}^* = (35,\, 1595/18,\, 0,\, 35,\, 30)$ con $Z^* = 135857/36 \approx 3773.8056$ millones de COP.
- **Simplex (Problema Equivalente) es el más rápido y eficiente:** Al arrancar en el vértice interior factible $\mathbf{x}^0 = (35, 60, 0, 127/6, 21/2)$ con $Z_0 \approx 2398.58$, optimiza directamente el margen en 4 pivotes primales.
- **Gran M requiere 9 pivotes:** Introduce 5 holguras, 5 excesos y 5 artificiales ($13 \times 24$). Gasta 6 pivotes únicamente en expulsar las variables artificiales de la base.
- **Simplex Dual requiere 12 pivotes:** Normaliza las 5 restricciones $\ge$ multiplicando por $-1$ (tableau $13 \times 19$ sin artificiales). Al ser una maximización con beneficios positivos, el origen no es dual-factible; ejecuta 4 pivotes duales para factibilizar lados derechos y 8 pivotes primales posteriores.

---

### 3.2 Contenedores en la Nube — `simplex-grupo1.json`
Modelo de optimización de contenedores en infraestructura cloud: **3 variables de decisión**, **4 restricciones de capacidad puramente $\le$ con lados derechos no negativos**:

| Método | Estado | Pivotes Totales | Tablas Stepper | Tiempo Medio (Mediana) | Dimensión Tableau | Valor Óptimo $Z^*$ |
|---|---|---|---|---|---|---|
| **Simplex** | `optimal` | **3** | **4** | **1.44 ms** (1.41 ms) | $4 \times 8$ | **1 575** |
| **Gran M** | `optimal` | **3** | **4** | **1.44 ms** (1.39 ms) | $4 \times 8$ | **1 575** |
| **Simplex Dual** | `optimal` | **3** | **4** | 1.46 ms (1.43 ms) | $4 \times 8$ | **1 575** |

- En ausencia de lados derechos negativos, Simplex Dual entra de inmediato a su bucle primal.
- Los tres métodos ejecutan la misma secuencia de pivotes (`Procesamiento` $\to s_3$, `Base de datos` $\to s_2$, `Web` $\to s_1$) con tiempos virtualmente idénticos.

---

### 3.3 Región Factible Vacía (Infactible) — `test-infeasible.json`
Modelo con 1 variable y restricciones mutuamente excluyentes: $x_1 \le 2$ y $x_1 \ge 5$:

| Método | Estado | Pivotes Totales | Tablas Stepper | Tiempo Medio (Mediana) | Dimensión Tableau | Diagnóstico de Parada |
|---|---|---|---|---|---|---|
| **Simplex** | `not_admissible` | — | — | **0.021 ms** (0.020 ms) | — | Rechaza al detectar que no existe transformación factible $\mathbf{b}_y \ge \mathbf{0}$. |
| **Gran M** | `infeasible` | 1 | 2 | 0.375 ms (0.373 ms) | $2 \times 5$ | Artificial $a_1$ permanece en base con valor $3 > 0$ ($Z = -3M + 2$). |
| **Simplex Dual** | `infeasible` | **1 (dual)** | **2** | **0.302 ms** (0.290 ms) | $\mathbf{2 \times 4}$ | Fila $s_1$ tiene $b_1 = -3 < 0$ y todos sus coeficientes son $\ge 0$ (sin pivote dual posible). |

- **Simplex Dual es 20% más rápido que Gran M** y opera con una columna menos ($2 \times 4$ vs $2 \times 5$), diagnosticando infactibilidad en el primer paso dual sin requerir variables artificiales.

---

### 3.4 Problema No Acotado — `test-unbounded.json`
Modelo con 2 variables: $\max x_1 + x_2 \text{ s.a. } x_1 - x_2 \le 2$:

| Método | Estado | Pivotes Totales | Tablas Stepper | Tiempo Medio (Mediana) | Dimensión Tableau | Diagnóstico de Parada |
|---|---|---|---|---|---|---|
| **Simplex** | `unbounded` | 1 | 2 | **0.243 ms** (0.237 ms) | $1 \times 4$ | Variable entrante $x_2$ sin cota positiva en su columna ($a_{i2} \le 0$). |
| **Gran M** | `unbounded` | 1 | 2 | 0.248 ms (0.240 ms) | $1 \times 4$ | Idéntico criterio de columna no acotada. |
| **Simplex Dual** | `unbounded` | 1 | 2 | 0.249 ms (0.235 ms) | $1 \times 4$ | Idéntico criterio en la fase primal. |

---

### 3.5 Minimización Canónica con Restricciones $\ge$ — `dual-classic-min`
Modelo de minimización donde el origen $\mathbf{x} = \mathbf{0}$ es **dual-factible** ($C_j - Z_j \ge 0$):  
$$\min Z = 3x_1 + 2x_2 \quad \text{s.a.} \quad 3x_1 + x_2 \ge 3, \quad 4x_1 + 3x_2 \ge 6, \quad x_1 + 2x_2 \le 3$$

| Método | Estado | Pivotes Totales | Desglose | Tablas Stepper | Tiempo Medio (Mediana) | Dimensión Tableau | Valor Óptimo $Z^*$ |
|---|---|---|---|---|---|---|---|
| **Simplex Dual** | `optimal` | **2** | **2 duales puros** | **3** | **0.731 ms** (0.711 ms) | $\mathbf{3 \times 6}$ | **21/5** |
| **Gran M** | `optimal` | 2 | 2 primales/art | 3 | 0.954 ms (0.930 ms) | $3 \times 8$ | 21/5 |
| **Simplex (P. Eq.)** | `optimal` | 1 | 1 primal | 2 | 1.218 ms (1.191 ms) | $3 \times 6$ | 21/5 |

- **Simplex Dual es el ganador absoluto:** 30% más rápido que Gran M y 40% más rápido que Simplex. Resuelve el problema en 2 pivotes duales sin pasar por fase primal y con tabla compacta ($3 \times 6$ vs $3 \times 8$).

---

### 3.6 Restricción de Igualdad Estricta — `equality-min`
Modelo de minimización con restricción de igualdad: $\min 2x_1 + 3x_2 \text{ s.a. } x_1 + x_2 = 10, x_1 \le 4$:

| Método | Estado | Pivotes Totales | Tablas Stepper | Tiempo Medio (Mediana) | Dimensión Tableau | Comportamiento Estructural |
|---|---|---|---|---|---|---|
| **Simplex** | `not_admissible` | — | — | 0.001 ms | — | Simplex estándar rechaza restricciones de igualdad ($=$). |
| **Gran M** | `optimal` | **2** | **3** | **0.518 ms** (0.494 ms) | $\mathbf{2 \times 5}$ | **Ganador en tiempo y filas.** Agrega 1 artificial para la igualdad ($Z^* = 26$). |
| **Simplex Dual** | `optimal` | 2 | 3 | 0.696 ms (0.683 ms) | $3 \times 6$ | Desdobla la igualdad en dos filas $\le$ ($x_1+x_2 \le 10$ y $-x_1-x_2 \le -10$). |

---

## 4. Tabla Consolidada de Métodos (6 Escenarios)

| Caso de Prueba | Tipo de Restricciones | Variables / Restricciones | Simplex (P. Eq.) | Gran M | Simplex Dual | Ganador y Criterio Clave |
|---|---|---|---|---|---|---|
| **Procafecol (`bakery-real`)** | Max $\le$ y $\ge$ | 5 vars / 13 restr | **4 piv** (5 tab)<br>**16.17 ms** | 9 piv (10 tab)<br>23.39 ms | 12 piv (13 tab)<br>23.76 ms | **Simplex**: Vértice inicial $\mathbf{x}^0$ ahorra 8 pivotes frente a Dual y 5 frente a Gran M. |
| **Contenedores (`simplex-grupo1`)** | Max puramente $\le$ | 3 vars / 4 restr | **3 piv** (4 tab)<br>**1.44 ms** | **3 piv** (4 tab)<br>**1.44 ms** | **3 piv** (4 tab)<br>1.46 ms | **Simplex / Gran M**: Empate técnico; Simplex es conceptualmente más simple. |
| **Infactible (`test-infeasible`)** | Región vacía ($\le$ y $\ge$) | 1 var / 2 restr | `not_admissible`<br>0.021 ms | 1 piv (2 tab)<br>0.375 ms | **1 piv** (2 tab)<br>**0.302 ms** | **Simplex Dual**: 20% más rápido que Gran M y sin variables artificiales. |
| **No acotado (`test-unbounded`)** | Max no acotado | 2 vars / 1 restr | **1 piv** (2 tab)<br>**0.243 ms** | **1 piv** (2 tab)<br>0.248 ms | **1 piv** (2 tab)<br>0.249 ms | **Empate general**: Detección inmediata de columna sin cota en la primera tabla. |
| **Minimización $\ge$ (`dual-classic-min`)** | Min con $\ge$ (costos $\ge 0$) | 2 vars / 3 restr | 1 piv (2 tab)<br>1.218 ms | 2 piv (3 tab)<br>0.954 ms | **2 piv** (3 tab)<br>**0.731 ms** | **Simplex Dual**: Tabla mínima, convergencia dual pura directa (30% más rápido que Gran M). |
| **Igualdad estricta (`equality-min`)** | Min con $=$ | 2 vars / 2 restr | `not_admissible`<br>0.001 ms | **2 piv** (3 tab)<br>**0.518 ms** | 2 piv (3 tab)<br>0.696 ms | **Gran M**: 1 fila menos que Dual al no desdoblar la igualdad ($2 \times 5$ vs $3 \times 6$). |

---

## 5. Análisis Comparativo Transversal

### 5.1 Tamaño de la Tabla y Consumo de Memoria
El número de columnas del tableau viene dado por la naturaleza de las variables auxiliares:

$$\begin{aligned}
C_{\text{simplex}} &= n + m + 1 \\
C_{\text{dual}} &= n + m + m_{=} + 1 \\
C_{\text{big\_m}} &= n + m_{\le} + 2m_{\ge} + m_{=} + 1
\end{aligned}$$

- **Ventaja de Simplex Dual:** En problemas sin igualdades, Simplex Dual elimina las $m_{\ge}$ variables de exceso y las $m_{\ge}$ variables artificiales de Gran M, reduciendo el ancho del tableau en **$2m_{\ge}$ columnas** (de 24 a 19 columnas en Procafecol, un ahorro del 21%).
- **Crecimiento en Igualdades:** Si el modelo contiene restricciones de igualdad ($=$), Gran M es más compacto en filas ya que mantiene $m$ filas con 1 artificial por igualdad, mientras que Simplex Dual desdobla cada igualdad en dos filas $\le$, aumentando filas y holguras.

### 5.2 Dinámica de Iteraciones y Factibilidad Inicial
- **Gran M:** Debe invertir entre el 50% y el 70% de sus iteraciones en expulsar las variables artificiales antes de iniciar la optimización primal real.
- **Simplex Dual:** Su desempeño depende del estado dual inicial:
  - En **minimización con costos no negativos y restricciones $\ge$**, la tabla es dual-factible desde el origen ($C_j - Z_j \ge 0$), convergiendo únicamente con pivotes duales sin necesidad de fase primal.
  - En **maximización con cotas inferiores**, la tabla no es dual-factible, requiriendo una fase dual para factibilizar $\mathbf{b} \ge \mathbf{0}$ y una fase primal posterior para optimizar $Z$.
- **Simplex con Problema Equivalente:** Al calcular un vértice factible inicial $\mathbf{x}^0$, evita completamente tanto la fase artificial de Gran M como la fase dual de Simplex Dual, logrando la convergencia en el menor número de tablas en problemas de maximización con cotas inferiores.

### 5.3 ¿Cuándo Conviene Cada Método? (Guía de Decisión)

| Situación Operativa del Problema | Método Recomendado | Razón Técnica y Justificación |
|---|---|---|
| **Problemas estándar ($\le$ con $\text{RHS} \ge 0$)** | **Simplex Estándar** | Tabla mínima, sin artificiales, sin fase dual previa y flujo algorítmico directo. |
| **Minimización con restricciones $\ge$ y costos $c_j \ge 0$** | **Simplex Dual** | **Ganador absoluto.** Tabla mínima ($3 \times 6$), sin artificiales ni $M$, convergencia puramente dual y menor tiempo de cómputo. |
| **Maximización con restricciones $\ge$ y cotas conocidas** | **Simplex con Problema Equivalente** | **Ganador en pasos.** Si se puede despejar un punto base $\mathbf{x}^0 \ge \mathbf{0}$, converge en una fracción de las iteraciones (4 vs. 9 vs. 12). |
| **Problemas con restricciones de igualdad estricta ($=$)** | **Gran M** (o Simplex Dual) | Gran M preserva $m$ filas agregando solo 1 artificial por igualdad ($2 \times 5$ vs $3 \times 6$). Si se desea evitar la penalización $M$, usar Simplex Dual. |
| **Detección rápida de Infactibilidad** | **Simplex Dual** | Demuestra infactibilidad en el primer pivote dual cuando $b_r < 0$ y $a_{rj} \ge 0$, sin gastar tiempo optimizando artificiales. |
| **Análisis Post-óptimo y Nuevas Restricciones** | **Simplex Dual** | Permite incorporar una nueva restricción que viole el óptimo actual y re-optimizar desde la tabla previa en 1 o 2 pivotes duales. |

---

## 6. Verificación del Caso Real con Excel Solver

El modelo del caso real Procafecol (`bakery-real.json`) fue resuelto y validado contra **Excel Solver (método Simplex LP)** y contra el motor del proyecto:

### 6.1 Concordancia de Solución Óptima

| Variable de Decisión | Línea de Café | Valor Excel Solver | Valor Motor Exacto (Fracción) | Valor Decimal Exacto | Diferencia Absoluta |
|---|---|---|---|---|---|
| $x_1$ | Tradicional | 35.0000 | $35$ | 35.0000 | 0.0000 |
| $x_2$ | Premium Balanceado | 88.6111 | $1595/18$ | $\approx 88.61111$ | $< 10^{-6}$ |
| $x_3$ | Orgánico | 0.0000 | $0$ | 0.0000 | 0.0000 |
| $x_4$ | Origen Regional | 35.0000 | $35$ | 35.0000 | 0.0000 |
| $x_5$ | Mujeres Cafeteras | 30.0000 | $30$ | 30.0000 | 0.0000 |
| **Función Objetivo $Z$** | **Margen Total (M\$)** | **3 773.8056** | $\mathbf{\frac{135857}{36}}$ | $\mathbf{\approx 3773.80556}$ | $< 10^{-6}$ |

> [!NOTE]
> Las diferencias menores a $10^{-6}$ corresponden exclusivamente al truncamiento de punto flotante de Excel (precisión doble de 64 bits). El motor del proyecto calcula la solución analítica exacta $\mathbf{Z^* = 135857/36}$ mediante aritmética de fracciones irreducibles.

### 6.2 Verificación de Restricciones Activas y Precios Sombra
El análisis de sensibilidad ejecutado desde el tableau óptimo final coincide de manera exacta en los tres métodos y con el informe de sensibilidad de Excel Solver:

1. **Tostión ($\le 720$ h/mes):** **Activa** ($s_1 = 0$), con precio sombra $\pi_1 = \mathbf{185/36 \approx 5.139}$ M\$/hora.
2. **Café verde especial ($\le 76.7$ ton/mes):** **Activa** ($s_5 = 0$), con precio sombra $\pi_5 = \mathbf{850/531 \approx 1.601}$ M\$/ton.
3. **Cota mín Tradicional ($\ge 35$ ton/mes):** **Activa** ($e_3 = 0$), con precio sombra $\pi_8 = \mathbf{-101/45 \approx -2.244}$ M\$/ton.
4. **Cota máx Mujeres Cafeteras ($\le 30$ ton/mes):** **Activa** ($s_{13} = 0$), con precio sombra $\pi_{13} = \mathbf{71/72 \approx 0.986}$ M\$/ton.
5. **Cota mín Mujeres Cafeteras ($\ge 10.5$ ton/mes):** No vinculante operativamente ($x_5 = 30 > 10.5$), con holgura degenerada en cero en la base canónica ($s_{10} = 0$).
6. **Variable no básica Orgánico ($x_3 = 0$):** Presenta un costo reducido de $r_3 = \mathbf{-229/180 \approx -1.272}$ M\$/ton (su contribución unitaria debería subir al menos \$1.272 M para justificar su producción).

---

## 7. Conclusiones

1. **Cumplimiento Integral del Lineamiento:** El sistema demuestra que los tres métodos resuelven el mismo problema real de Procafecol S.A. alcanzando idéntico óptimo ($Z^* = 135857/36$) y la misma asignación de producción, satisfaciendo el requerimiento *"¿Mismo problema?: Sí"*.
2. **Simplex con Problema Equivalente Optimiza Pasos:** Mediante el cambio afín de variables ($\mathbf{x} = \mathbf{x}^0 + \mathbf{T}\mathbf{y}$), Simplex reduce a la mitad las iteraciones de Gran M (4 vs. 9) y a un tercio las de Simplex Dual (4 vs. 12) en el caso real.
3. **Simplex Dual Domina en Minimización:** En problemas de minimización con restricciones $\ge$ y costos positivos, Simplex Dual es 30% más rápido que Gran M y 40% más rápido que Simplex, convergiendo con 0 variables artificiales y tableau compacto.
4. **Gran M Proporciona Universalidad:** Es el método más adecuado para sistemas con restricciones de igualdad estricta ($=$), evitando el desdoblamiento de filas requerido por Simplex Dual.

---

## 8. Declaración de Uso de Asistencia de IA

Este informe y las pruebas asociadas fueron desarrollados con asistencia de herramientas avanzadas de inteligencia artificial (modelos Gemini / Antigravity) como soporte de ingeniería y pair programming. Los desarrollos matemáticos, la formulación del problema equivalente, las mediciones experimentales y las conclusiones técnicas fueron implementados y validados por los integrantes del Grupo 3.
