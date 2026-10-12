# Formato tabular $C_j - Z_j$ sin normalización min→max

El curso y el algoritmo de referencia del docente usan el tableau clásico con
filas $Z_j$ y $C_j - Z_j$ separadas, columnas $V_B$ y $C_B$, y criterios de
optimalidad distintos para max y min. Adoptamos esa representación como la
estructura interna y de API del motor, en vez del enfoque simplificado con una
sola fila z unificada ($z_j - c_j$) y normalización automática min→max.

**Alternativa rechazada — fila z unificada con normalización min→max:**
un solo vector $z_j - c_j$ y el motor siempre maximiza (negando coeficientes
para min). Más simple de implementar, pero produce tablas que no corresponden
a lo que el estudiante resuelve a mano ni a lo que el docente espera ver.
Además obliga a revertir signos al reportar la solución, añadiendo una capa
de traducción propensa a errores de signo.

**Consecuencias:**
- El motor tiene dos ramas de lógica para entrada y optimalidad (max vs min),
  pero el pivoteo Gauss-Jordan es idéntico.
- `pivot()` y `evaluate()` son funciones separadas: el pivoteo modifica filas
  de restricciones y $V_B/C_B$; la evaluación recalcula $Z_j$ y $C_j - Z_j$.
- Cada snapshot del Tableau es autosuficiente (incluye `sense`, `cj`, `zj`,
  `cj_zj`) y el frontend lo renderiza tal cual, sin cálculos.
