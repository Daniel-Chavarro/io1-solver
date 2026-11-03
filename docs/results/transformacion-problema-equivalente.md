# Transformación al Problema Equivalente para Simplex — Caso Real Procafecol S.A.

> **Proyecto:** `solver` (Investigación de Operaciones 1)  
> **Grupo:** 3 — Métodos: Simplex Primal (con Problema Equivalente), Gran M y Simplex Dual  
> **Lineamiento del curso:** "¿Mismo problema?: Sí"  
> **Fecha:** Noviembre 2026  
> **Estado:** Implementado, verificado y validado contra Gran M y Simplex Dual (`150 passed`).

---

## 1. Contexto y Lineamiento del Curso

El lineamiento del curso para los grupos clasificados con **“¿Mismo problema?: Sí”** establece:

> *“Los dos métodos resuelven el mismo problema real y sus resultados deben coincidir. Si un método no admite el tipo de restricciones del problema, se transforma en uno equivalente (por ejemplo, resolver el dual o cambio de variables) y se explica en el informe. El informe compara los métodos: pasos o iteraciones, tiempo y cuál conviene en cada situación.”*

En nuestro proyecto, el problema real de la organización corresponde al **Plan de producción mensual de café empacado de Procafecol S.A. (Juan Valdez)** (`examples/bakery-real.json`, Documento Entrega 1, sección 6), compuesto por 5 líneas de producto ($x_1, \dots, x_5$) y 13 restricciones operativas, de calidad y comerciales.

Dado que el modelo contiene restricciones de cota inferior y de demanda mínima de tipo mayor o igual ($\ge$), el método de la **Gran M** las resuelve incorporando variables de exceso $e_i$ y variables artificiales $a_i$ penalizadas con $-M$. Sin embargo, el método **Simplex Primal estándar** exige que todas las restricciones sean de tipo menor o igual ($\le$) con lados derechos no negativos ($b_i \ge 0$) para poder iniciar en el origen trivial $\mathbf{x} = \mathbf{0}$ con holguras puras $\mathbf{s} = \mathbf{b}$.

Para cumplir estrictamente con el lineamiento sin alterar el problema ni recurrir a un modelo artificial distinto, se implementó en `backend/src/solver/methods/simplex.py` una **transformación algebraica automática al problema equivalente mediante cambio afín de variables** ($\mathbf{x} = \mathbf{x}^0 + \mathbf{T}\mathbf{y}$), resolviendo el problema transformado con Simplex estándar y reconstruyendo tanto el vector de solución como el tableau canónico óptimo en las variables originales.

---

## 2. Definición del Problema Real (Procafecol S.A.)

### 2.1 Variables de Decisión
- $x_1$: Café Tradicional empacado a producir en el mes (ton/mes).
- $x_2$: Café Premium Balanceado empacado a producir en el mes (ton/mes).
- $x_3$: Café Orgánico empacado a producir en el mes (ton/mes).
- $x_4$: Café Origen Regional empacado a producir en el mes (ton/mes).
- $x_5$: Café Mujeres Cafeteras empacado a producir en el mes (ton/mes).

### 2.2 Función Objetivo
Maximizar la contribución marginal total mensual (en millones de COP):
$$\max Z = 14.20\,x_1 + 18.50\,x_2 + 22.20\,x_3 + 24.50\,x_4 + 26.00\,x_5$$

### 2.3 Restricciones Operativas y de Mercado
1. **Tostión:** $3.20 x_1 + 3.60 x_2 + 4.20 x_3 + 4.40 x_4 + 4.50 x_5 \le 720$ (horas/mes)
2. **Molienda:** $2.50 x_1 + 2.20 x_2 + 1.50 x_3 + 1.60 x_4 + 1.80 x_5 \le 420$ (horas/mes)
3. **Envasado:** $2.80 x_1 + 3.00 x_2 + 3.40 x_3 + 3.50 x_4 + 3.60 x_5 \le 600$ (horas/mes)
4. **Café verde total:** $1.18 x_1 + 1.18 x_2 + 1.18 x_3 + 1.18 x_4 + 1.18 x_5 \le 236$ (ton/mes)
5. **Café verde especial:** $1.18 x_3 + 1.18 x_4 + 1.18 x_5 \le 76.7$ (ton/mes)
6. **Mínimo retail:** $x_1 + x_2 \ge 95$ *(restricción $\ge$ comercial)*
7. **Mínimo 25% especial:** $-\frac{1}{4}x_1 - \frac{1}{4}x_2 + \frac{3}{4}x_3 + \frac{3}{4}x_4 + \frac{3}{4}x_5 \ge 0$ *(restricción $\ge$ de mezcla de ventas)*
8. **Cota mín Tradicional:** $x_1 \ge 35$ *(contrato institucional vigente)*
9. **Cota mín Premium Balanceado:** $x_2 \ge 30$ *(pedido mínimo tiendas propias)*
10. **Cota máx Orgánico:** $x_3 \le 35$ *(disponibilidad de grano verde certificado)*
11. **Cota máx Origen Regional:** $x_4 \le 40$ *(cupo asociativo regional)*
12. **Cota mín Mujeres Cafeteras:** $x_5 \ge 10.5$ *(compromiso de equidad de género)*
13. **Cota máx Mujeres Cafeteras:** $x_5 \le 30$ *(capacidad de acopio especializada)*
14. **No negatividad:** $x_j \ge 0 \quad \forall j \in \{1, \dots, 5\}$.
---

## 3. Fundamentación Matemática del Problema Equivalente

### 3.1 El problema primal con restricciones generales
Sea el problema primal en forma matricial:
$$\begin{aligned}
\max_{\mathbf{x}} \quad & Z = \mathbf{c}^T \mathbf{x} \\
\text{s.a.} \quad & \mathbf{A}_1 \mathbf{x} \le \mathbf{b}_1 \quad (\text{restricciones } \le) \\
& \mathbf{A}_2 \mathbf{x} \ge \mathbf{b}_2 \quad (\text{restricciones } \ge) \\
& \mathbf{x} \ge \mathbf{0}
\end{aligned}$$

Multiplicando las restricciones $\ge$ por $-1$, el sistema completo se expresa como $\mathbf{A} \mathbf{x} \le \mathbf{b}$, donde las filas provenientes de restricciones $\ge$ tienen $-\mathbf{A}_{2, i} \mathbf{x} \le -\mathbf{b}_{2, i}$. En el punto $\mathbf{x} = \mathbf{0}$, el lado derecho transformado es negativo ($-\mathbf{b}_{2, i} < 0$), lo que impide usar el origen como base factible inicial de holguras.

### 3.2 Cambio Afín de Variables ($\mathbf{x} = \mathbf{x}^0 + \mathbf{T}\mathbf{y}$)
Buscamos un punto base factible $\mathbf{x}^0 \ge \mathbf{0}$ y una matriz de cambio de base invertible $\mathbf{T} \in \mathbb{Q}^{n \times n}$ con $\mathbf{T}^{-1}$ exacta, de modo que en las nuevas variables $\mathbf{y} \ge \mathbf{0}$:
$$\mathbf{x} = \mathbf{x}^0 + \mathbf{T}\mathbf{y} \iff \mathbf{y} = \mathbf{T}^{-1}(\mathbf{x} - \mathbf{x}^0)$$

Sustituyendo en la función objetivo:
$$Z = \mathbf{c}^T (\mathbf{x}^0 + \mathbf{T}\mathbf{y}) = \underbrace{\mathbf{c}^T \mathbf{x}^0}_{Z_0} + \underbrace{(\mathbf{c}^T \mathbf{T})}_{\mathbf{c}_y^T} \mathbf{y} = Z_0 + \mathbf{c}_y^T \mathbf{y}$$

Sustituyendo en las restricciones $\mathbf{A}\mathbf{x} \le \mathbf{b}$:
$$\mathbf{A}(\mathbf{x}^0 + \mathbf{T}\mathbf{y}) \le \mathbf{b} \iff (\mathbf{A}\mathbf{T})\mathbf{y} \le \mathbf{b} - \mathbf{A}\mathbf{x}^0$$

Definiendo:
$$\mathbf{A}_y = \mathbf{A}\mathbf{T}, \qquad \mathbf{b}_y = \mathbf{b} - \mathbf{A}\mathbf{x}^0$$

Si el punto $\mathbf{x}^0$ es **factible** para el sistema original $\mathbf{A}\mathbf{x} \le \mathbf{b}$, entonces:
$$\mathbf{b}_y = \mathbf{b} - \mathbf{A}\mathbf{x}^0 \ge \mathbf{0}$$

Por tanto, el problema en variables $\mathbf{y}$:
$$\begin{aligned}
\max_{\mathbf{y}} \quad & Z_y = \mathbf{c}_y^T \mathbf{y} \\
\text{s.a.} \quad & \mathbf{A}_y \mathbf{y} \le \mathbf{b}_y \\
& \mathbf{y} \ge \mathbf{0}
\end{aligned}$$
se encuentra en **forma estándar estricta de Simplex**: todas sus restricciones son $\le$, sus lados derechos $\mathbf{b}_y$ son no negativos, y el punto $\mathbf{y} = \mathbf{0}$ constituye una solución básica factible inicial con variables de holgura $\mathbf{s} = \mathbf{b}_y \ge \mathbf{0}$.

---

## 4. Algoritmo de Construcción en Procafecol S.A.

El módulo `_build_affine_transform(problem: Problem)` implementa la siguiente secuencia constructiva:

### Paso 1: Cotas inferiores directas de una variable
Identifica restricciones $\ge$ cuyo soporte no nulo corresponda a una única variable $k$ ($x_k \ge \text{lb}_k$):
- Restricción 8: $x_1 \ge 35 \implies x^0_1 = 35$
- Restricción 9: $x_2 \ge 30 \implies x^0_2 = 30$
- Restricción 12: $x_5 \ge 10.5 = \frac{21}{2} \implies x^0_5 = \frac{21}{2}$
- Variables sin cota inferior directa: $x^0_3 = 0$, $x^0_4 = 0$.

Punto intermedio:
$$\mathbf{x}^0 = \left(35,\, 30,\, 0,\, 0,\, \frac{21}{2}\right)$$

### Paso 2: Eliminación de excesos en restricciones $\ge$ multivariables activas
Para cada restricción $\ge$ donde $\mathbf{x}^0$ aún presenta déficit ($\sum A_{i, r} x^0_r > b_i$ en forma $\le$):

1. **Restricción 6 (Mínimo retail: $x_1 + x_2 \ge 95$):**
   - En el punto intermedio: $x^0_1 + x^0_2 = 35 + 30 = 65 < 95$.
   - Déficit: $95 - 65 = 30$.
   - Coordenadas de exceso: $y_2 = x_1 + x_2 - 95$.
   - Seleccionando $x_2$ como variable de ajuste libre:
     $$x_2 = 95 - x_1 + y_2 = 60 - y_1 + y_2$$
   - Se actualiza $x^0_2 = 60$ y se sustituye en la columna correspondiente de $\mathbf{T}$.

2. **Restricción 7 (Mínimo 25% especial: $-\frac{1}{4}x_1 - \frac{1}{4}x_2 + \frac{3}{4}x_3 + \frac{3}{4}x_4 + \frac{3}{4}x_5 \ge 0$):**
   - En el punto con $x_1=35, x_2=60, x_3=0, x_5=10.5$:
     $$\text{Suma} = -\frac{1}{4}(35) - \frac{1}{4}(60) + \frac{3}{4}(10.5) = -\frac{95}{4} + \frac{63}{8} = -\frac{127}{8} < 0$$
   - Déficit: $\frac{127}{8}$.
   - Coeficiente de $x_4$ (Origen Regional) en la restricción: $\frac{3}{4}$.
   - Incremento necesario en $x^0_4$: $\frac{127/8}{3/4} = \frac{127}{6} \approx 21.167$.
   - Se fija $x^0_4 = \frac{127}{6}$ y se pivota en $\mathbf{T}$.

### 4.1 Punto base factible y matrices exactas
El vértice inicial resultante en variables originales es:
$$\mathbf{x}^0 = \begin{pmatrix} 35 \\ 60 \\ 0 \\ \frac{127}{6} \\ \frac{21}{2} \end{pmatrix}, \qquad Z_0 = \mathbf{c}^T \mathbf{x}^0 = \frac{28783}{12} \approx 2398.583$$

La matriz de transformación $\mathbf{T}$ y su inversa $\mathbf{T}^{-1}$ son:
$$\mathbf{T} = \begin{pmatrix}
1 & 0 & 0 & 0 & 0 \\
-1 & 1 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 \\
0 & \frac{1}{3} & -1 & \frac{4}{3} & -1 \\
0 & 0 & 0 & 0 & 1
\end{pmatrix}, \qquad
\mathbf{T}^{-1} = \begin{pmatrix}
1 & 0 & 0 & 0 & 0 \\
1 & 1 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 \\
-\frac{1}{4} & -\frac{1}{4} & \frac{3}{4} & \frac{3}{4} & \frac{3}{4} \\
0 & 0 & 0 & 0 & 1
\end{pmatrix}$$

Nótese que $\mathbf{T} \mathbf{T}^{-1} = \mathbf{I}_5$.

Los lados derechos transformados $\mathbf{b}_y = \mathbf{b} - \mathbf{A}\mathbf{x}^0$ son todos $\ge 0$:
$$\mathbf{b}_y = \left(\frac{15097}{60},\, \frac{2216}{15},\, \frac{12607}{60},\, \frac{1298}{15},\, \frac{118}{3},\, 0,\, 0,\, 0,\, 30,\, 35,\, \frac{113}{6},\, 0,\, \frac{39}{2}\right)^T \ge \mathbf{0}$$

Los coeficientes de la función objetivo en coordenadas $\mathbf{y}$ son:
$$\mathbf{c}_y = \mathbf{c}^T \mathbf{T} = \left(-\frac{43}{10},\, \frac{80}{3},\, -\frac{23}{10},\, \frac{98}{3},\, \frac{3}{2}\right)$$

---

## 5. Reconstrucción Canónica del Tableau y Solución Óptima

El motor Simplex resuelve el problema estándar transformado en $\mathbf{y}$ en **4 iteraciones de pivoteo** (5 tablas contando la tabla inicial). En el óptimo de $\mathbf{y}$:
$$\mathbf{y}^* = \begin{pmatrix} 0 \\ \frac{515}{18} \\ 0 \\ \frac{1285}{72} \\ \frac{39}{2} \end{pmatrix}, \qquad Z_y^* = \frac{12377}{9}$$

El método `SimplexMethod.restore_tableau` realiza la restitución:
1. **Reconstrucción del vector original $\mathbf{x}^*$:**
   $$\mathbf{x}^* = \mathbf{x}^0 + \mathbf{T}\mathbf{y}^* = \begin{pmatrix} 35 + 0 \\ 60 - 0 + \frac{515}{18} \\ 0 \\ \frac{127}{6} + \frac{1}{3}\left(\frac{515}{18}\right) - 0 + \frac{4}{3}\left(\frac{1285}{72}\right) - \frac{39}{2} \\ \frac{21}{2} + \frac{39}{2} \end{pmatrix} = \begin{pmatrix} 35 \\ \frac{1595}{18} \\ 0 \\ 35 \\ 30 \end{pmatrix}$$
2. **Valor óptimo de la función objetivo:**
   $$Z^* = Z_0 + Z_y^* = \frac{28783}{12} + \frac{12377}{9} = \frac{135857}{36} \approx 3773.80556 \text{ millones de COP}$$
3. **Canonicalización del Tableau:**
   Se aplican las transformaciones de fila usando $\mathbf{T}^{-1}$ y se pivotan las columnas de las variables de decisión originales ($x_1, x_2, x_4, x_5$) sobre las holguras asociadas para que la tabla óptima final exprese directamente la base canónica en las variables naturales del problema de Procafecol.

---

## 6. Comparación Numérica: Simplex vs. Gran M vs. Simplex Dual en el Caso Real

Los tres métodos fueron ejecutados sobre la misma instancia `examples/bakery-real.json`:

| Criterio | Simplex (Problema Equivalente) | Gran M (Penalización Simbólica) | Simplex Dual (Normalización Dual) | Concordancia |
|---|---|---|---|---|
| **Estado de terminación** | `optimal` | `optimal` | `optimal` | Idéntico |
| **Valor óptimo $Z$** | $\mathbf{\frac{135857}{36}}$ (3773.80556) | $\mathbf{\frac{135857}{36}}$ (3773.80556) | $\mathbf{\frac{135857}{36}}$ (3773.80556) | Exactamente igual |
| **$x_1$ (Tradicional)** | $35$ ton/mes | $35$ ton/mes | $35$ ton/mes | Idéntico |
| **$x_2$ (Premium Balanceado)** | $\frac{1595}{18} \approx 88.611$ ton/mes | $\frac{1595}{18} \approx 88.611$ ton/mes | $\frac{1595}{18} \approx 88.611$ ton/mes | Idéntico |
| **$x_3$ (Orgánico)** | $0$ ton/mes | $0$ ton/mes | $0$ ton/mes | Idéntico |
| **$x_4$ (Origen Regional)** | $35$ ton/mes | $35$ ton/mes | $35$ ton/mes | Idéntico |
| **$x_5$ (Mujeres Cafeteras)** | $30$ ton/mes | $30$ ton/mes | $30$ ton/mes | Idéntico |
| **Tablas en el Stepper** | **5 tablas** (4 pivotes) | **10 tablas** (9 pivotes) | **13 tablas** (12 pivotes: 4 duales + 8 primales) | Simplex usa menos tablas |
| **Dimensión de tablas** | $\mathbf{13 \times 19}$ (13 filas, 5 vars, 13 holguras, $b_j$) | $13 \times 24$ (13 filas, 5 vars, 8 holguras, 5 excesos, 5 artificiales, $b_j$) | $\mathbf{13 \times 19}$ (13 filas, 5 vars, 13 holguras, $b_j$) | Simplex y Simplex Dual son más compactos |
| **Tiempo de cálculo** | $\mathbf{\approx 16}$ ms | $\approx 23$ ms | $\approx 24$ ms | Simplex es $\approx 30\%$ más rápido |
| **Variables artificiales** | **0** (ninguna variable artificial) | $5$ variables artificiales ($a_1, \dots, a_5$) con $-M$ | **0** (ninguna variable artificial) | Ventaja estructural de Simplex y Dual |

### Análisis Comparativo de Rendimiento y Conveniencia
1. **Por qué Simplex requiere menos pasos (5 vs. 10 de Gran M y 13 de Simplex Dual):**
   En Gran M, cada restricción $\ge$ introduce una variable artificial con coeficiente $-M$ en la función objetivo, gastando 6 de sus 9 pivotes exclusivamente en expulsar las artificiales. En Simplex Dual, al iniciar en el origen con coeficientes de beneficio positivos en una maximización, la tabla no es dual-factible, por lo que primero gasta 4 pivotes duales para lograr factibilidad primal y luego 8 pivotes primales. En contraste, la transformación afín de Simplex arranca directamente desde un vértice factible $\mathbf{x}^0$ de la región acotada, avanzando de inmediato hacia el óptimo en solo 4 pivotes primales.
2. **Cuándo conviene cada método:**
   - **Simplex con problema equivalente:** Conviene cuando el sistema de restricciones $\ge$ proviene de cotas inferiores o demandas mínimas con un punto base factible derivable algebraicamente. Es el más rápido en este escenario y no requiere variables artificiales ni aritmética simbólica.
   - **Simplex Dual:** Conviene en problemas de minimización con restricciones $\ge$ y costos positivos (donde el origen ya es dual-factible y converge en tabla mínima sin artificiales), en análisis post-óptimo para reoptimizar ante nuevas restricciones y para detección temprana de infactibilidad.
   - **Gran M:** Conviene cuando el modelo contiene restricciones de igualdad ($=$) rígidas, donde preserva $m$ filas frente al desdoblamiento de filas de Simplex Dual.
   *(Para el análisis cuantitativo completo y formal de los 6 escenarios de prueba, consultar [`docs/results/comparacion-metodos.md`](./comparacion-metodos.md)).*
---

## 7. Trazabilidad en la API y en la Interfaz de Usuario

### 7.1 Indicador de Caso Especial en `POST /api/resolver`
Cuando Simplex utiliza la transformación afín, `MethodResult.special_cases` incluye en la iteración 0 el evento `normalized_constraint`:
```json
{
  "type": "normalized_constraint",
  "iteration": 0,
  "detail": "Se aplicó transformación al problema equivalente por cambio de variables (x = x⁰ + T·y) para resolver restricciones >= con Simplex estándar: vértice inicial (Tradicional=35, Premium Balanceado=60, Orgánico=0, Origen Regional=127/6, Mujeres Cafeteras=21/2) y Z inicial = 28783/12."
}
```

### 7.2 Veredicto Comparativo en `POST /api/comparar`
El endpoint de comparación emite veredictos diferenciados según si se requirió o no transformación:
- **En Procafecol (`bakery-real`):**
  > *"Los tres métodos alcanzaron el mismo óptimo (Z = 135857/36): Simplex usó transformación al problema equivalente por cambio de variables en 5 tablas (13x19, 16.342 ms), Gran M usó variables artificiales en 10 tablas (13x24, 24.4 ms) y Simplex Dual normalizó restricciones ≥ sin artificiales en 13 tablas (13x19, 24.035 ms)."*
- **En problemas puramente $\le$ (`simplex-grupo1`):**
  > *"Los tres métodos alcanzaron el mismo óptimo (Z = 1575) en 4 tablas (4x8); no se requirió transformación al problema equivalente (todas las restricciones son ≤ con RHS ≥ 0) y ni Gran M ni Simplex Dual requirieron pasos adicionales, por lo que conviene Simplex por simplicidad."*

### 7.3 Visualización en Frontend
- `frontend/src/components/SolutionSummary.tsx`: la tarjeta de solución óptima indica explícitamente:
  `"Resuelto con Simplex (usando transformación al problema equivalente por cambio de variables) en 18 ms."`
  o `"Resuelto con Simplex (forma estándar directa, sin transformación equivalente) en 3 ms."`
- `frontend/src/components/ProblemForm.tsx`: el texto de ayuda del selector de método aclara el soporte de restricciones $\ge$ vía problema equivalente.
