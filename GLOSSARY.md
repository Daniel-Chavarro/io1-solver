# Solver de Programación Lineal — IO1 Grupo 3

Vocabulario del dominio (programación lineal y método simplex) usado en el
informe, la UI y los contratos. Sin detalles de implementación.

## Modelo

**Problema**:
Instancia de PL que el usuario captura: nombre, variables de decisión,
función objetivo y restricciones.
_Avoid_: modelo, ejercicio, caso.

**Variable de decisión**:
Magnitud que se decide cuánto llevar (con nombre propio y unidad, p. ej.
`pandesal` en `lotes`).
_Avoid_: incógnita, x1.

**Unidad**:
Medida de una variable de decisión (lotes, horas, kg) que acompaña a sus
valores en todo resultado.
_Avoid_: medida, dimensión.

**Función objetivo**:
Expresión lineal que se maximiza o minimiza.
_Avoid_: objetivo, Z (el símbolo solo en fórmulas).

**Restricción**:
Desigualdad o igualdad lineal (`≤`, `≥`, `=`) con nombre propio que limita
las variables.
_Avoid_: condición, límite.

**Solución**:
Valores finales de las variables de decisión, con su nombre y unidad, junto
al valor de la función objetivo.
_Avoid_: resultado, respuesta.

**Forma estándar**:
Versión normalizada del problema que exige RHS ≥ 0 y solo restricciones `≤`
(requerida por el método Simplex).
_Avoid_: forma normal, forma canonical.

## El método

**Método**:
Procedimiento paso a paso que resuelve un problema (Simplex, Gran M).
_Avoid_: algoritmo, librería, motor.

**Tableau**:
Tabla que el método transforma por pivoteos; su primera fila es la fila z.
_Avoid_: matriz, tabla de datos, tabulador.

**Iteración**:
Un pivote del tableau, caracterizado por la variable que entra, la que sale
y el elemento pivote. La iteración 0 es el tableau inicial.
_Avoid_: paso, vuelta, ronda.

**Variable que entra**:
Variable no básica que se hace básica en la iteración (costo reducido más
negativo de la fila z).
_Avoid_: entrante, variable entrante.

**Variable que sale**:
Variable básica que deja la base en la iteración (razón mínima).
_Avoid_: saliente, variable saliente.

**Elemento pivote**:
Celda en la intersección de la variable que entra y la que sale, sobre la
que se pivotea.
_Avoid_: pivote (ambiguo con el proceso de pivoteo).

**Razón mínima**:
Criterio de salida: menor razón entre RHS y coeficiente positivo de la
columna que entra. Un empate produce degeneración.
_Avoid_: razón mínima de factibilidad, test de la razón.

**Holgura / Exceso / Artificial**:
Variables auxiliares `s_i` (de `≤`), `e_i` (de `≥`) y `a_i` (de `≥` y `=`)
que llevan el problema a forma de tableau.

**Gran M**:
Método para restricciones `≤`, `≥` y `=` que penaliza las artificiales con
un costo −M, visible en las tablas.
_Avoid_: método de la gran M, penalización.

## Casos especiales

**Caso especial**:
Situación que el método debe avisar explícitamente: infactible, no acotado,
óptimos alternativos o degeneración.
_Avoid_: excepción, error.

**Infactible**:
No existe solución que satisfaga todas las restricciones.
_Avoid_: sin solución (ambiguo con no acotado).

**No acotado**:
La función objetivo puede mejorar sin límite; se detecta cuando la columna
que entra no tiene positivos.
_Avoid_: infinito, ilimitado.

**Óptimos alternativos**:
Existe más de una solución con el mismo valor óptimo de la función
objetivo (una variable no básica con costo reducido 0 en la tabla final).
_Avoid_: múltiples soluciones, empate de óptimos.

**Degeneración**:
Empate en la razón mínima o variable básica en cero; el método avanza pero
puede ciclar.
_Avoid_: empate (ambiguo con óptimos alternativos).

## Sensibilidad

**Análisis de sensibilidad**:
Estudio de cómo cambia el óptimo ante cambios en los coeficientes $c_j$ y
en los lados derechos $b_i$, sobre un problema ya resuelto.
_Avoid_: análisis post-óptimo.

**Precio sombra**:
Cuánto mejoraría la función objetivo con una unidad adicional del lado
derecho de una restricción.
_Avoid_: valor dual, sombra.

**Costo reducido**:
Cuánto debería mejorar el coeficiente de una variable no básica para que
entre a la base.
_Avoid_: penalización, oportunidad.

**Rango de $c_j$ / Rango de $b_i$**:
Intervalo en el que puede variar un coeficiente del objetivo / un lado
derecho sin que cambie la base óptima. Puede ser infinito por un lado.
_Avoid_: intervalo de validez.

**Restricción activa**:
Restricción cumplida con igualdad (sin holgura); su precio sombra puede ser
distinto de cero.
_Avoid_: binding, restrictiva.

**Comparación**:
Cotejo de los dos métodos sobre el mismo problema (iteraciones, tiempo,
mismo valor de z) para decir cuál conviene en cada situación.
_Avoid_: benchmark, contraste.
