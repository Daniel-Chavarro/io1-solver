## Proyecto Final – Investigación de Operaciones 1

Instrucciones · Grupo IO1-82 · Periodo 2026-3 · Ingeniería de Sistemas

## 1. ¿Qué hay que hacer?

- 1. Cada grupo programa un software con los dos métodos que le tocaron (tabla de la Sección 3).

- 2. El software debe resolver cualquier problema que el usuario escriba para esos métodos, no solo el problema del grupo. Los datos nunca van escritos dentro del código.

- 3. El software se prueba con un problema real de una empresa u organización (Sección 5).

- 4. Se entrega un informe en PDF, el código y en cada entrega el grupo hace una sustentación de 10 minutos (Secciones 7 y 8).

- 5. En las Entregas 2 y final el docente da un problema nuevo y pequeño y el software debe resolverlo en vivo.


Usar librerías o programas que resuelvan el problema por ustedes (SciPy, PuLP, OR-Tools, Solver de Excel, etc.). Cada método lo programa el grupo. Esas herramientas solo se pueden usar aparte, para comprobar que sus resultados están bien.



## 2. Qué debe hacer el software con cada método

| Método | Problema que resuelve y | Qué debe mostrar | Casos especiales que |
| --- | --- | --- | --- |
|   | tamaño mínimo |   | debe avisar |
| Gráfico | PL de 2 variables, max o min, | Gráfica con cada restricción, región | Infactible, no acotado, |
|   | restricciones ≤, ≥ y =. Hasta 8 | factible, vértices con su valor de z y el | óptimos alternativos. |
|   | restricciones. | óptimo marcado. |   |
| Simplex | PL max o min con restricciones | Cada tabla, con variable que entra, | No acotado, óptimos |
| (max-min) | ≤. Hasta 8 variables y 8 | variable que sale y pivote; solución | alternativos, degeneración. |
|   | restricciones. | final y z. |   |
| Dos Fases | PL max o min con ≤, ≥ y =. | Tablas de la Fase 1 y de la Fase 2, | Infactible, no acotado, |
| (max-min) | Hasta 8 × 8. | con variables artificiales. | óptimos alternativos. |
| Gran M | PL max o min con ≤, ≥ y =. | Cada tabla con la M visible; solución | Infactible, no acotado, |
| (max-min) | Hasta 8 × 8. | final y z. | óptimos alternativos. |
| Simplex Dual | PL resuelto con el simplex dual. | Cada tabla, fila pivote (b más | Infactible, degeneración. |
|   | Hasta 8 × 8. | negativo) y columna pivote (razón |   |
|   |   | mínima). |   |
| Análisis de | Sobre un PL ya resuelto. Hasta | Precios sombra, costos reducidos, | Rangos infinitos, |
| sensibilidad | 8 × 8. | rango de cada cj y de cada bi, con | restricciones sin holgura. |
|   |   | una frase de interpretación. |   |
| Esquina | Transporte (mín. costo). Hasta | Cada asignación en orden, tabla final | Desbalance (origen o |
| Noroeste | 8 orígenes × 8 destinos, | y costo total. | destino ficticio), |
|   | balanceado o no. |   | degeneración. |


| Método | Problema que resuelve y | Qué debe mostrar | Casos especiales que |
| --- | --- | --- | --- |
|   | tamaño mínimo |   | debe avisar |
| Vogel | Transporte (mín. costo). Hasta | Penalizaciones de filas y columnas en | Desbalance, empates de |
|   | 8 × 8, balanceado o no. | cada paso, celda escogida, tabla final | penalización, |
|   |   | y costo total. | degeneración. |
| Programación | Problema por etapas de un tipo | Tabla de cada etapa (estado, | Estados no factibles, |
| Dinámica | visto en clase (el grupo lo | decisión, valor), cálculo hacia atrás y | empates. |
|   | declara en la Entrega 1). Hasta | política óptima. |   |
|   | 8 etapas. |   |   |

Esquina Noroeste y Vogel solo dan una solución inicial, que no siempre es la óptima. El informe debe comparar su costo con el óptimo calculado aparte (por ejemplo, con el Solver de Excel) y explicar la diferencia.

## 3. Métodos y lenguaje de cada grupo

| Grupo Método 1 |   | Método 2 | Lenguaje | ¿Mismo problema? |
| --- | --- | --- | --- | --- |
| 1 | Simplex | Simplex Dual | Python | Sí |
| 2 | Gráfico | Esquina Noroeste | Python (Gráfico) y Java (Esq. | No, dos modelos |
|   |   |   | Noroeste)* |   |
| 3 | Simplex | Gran M | Python + React | Sí |
| 4 | Simplex | Gran M | Python | Sí |
| 5 | Gráfico | Gran M | Python | Sí |
| 6 | Dos Fases | Gran M | Python | Sí |
| 7 | Gráfico | Simplex Dual | Python | Sí |
| 8 | Gráfico | Análisis de sensibilidad | Python | Sí |
| 9 | Simplex | Vogel | Python | No, dos modelos |
| 10 | Gráfico | Programación Dinámica | Python | No, dos modelos |

- “Mismo problema” (Sí): los dos métodos resuelven el mismo problema real y sus resultados deben coincidir. Si un método no admite el tipo de restricciones del problema, se transforma en uno equivalente (por ejemplo, resolver el dual) y se explica en el informe. El informe compara los métodos: pasos o iteraciones, tiempo y cuál conviene en cada situación.

- “No, dos modelos”: los métodos resuelven tipos de problema distintos. El grupo presenta dos modelos de la misma organización (por ejemplo, qué producir y cómo distribuir). Cada resultado se compara con una verificación aparte, en lugar de comparar un método con el otro.

- *Grupo 2: el sistema es uno solo. Deben escoger un único lenguaje para toda la aplicación (o un módulo en Java llamado desde la interfaz) y decirlo al docente antes de la Entrega 1.

## 4. Todo software debe tener

- Ingreso de datos en la interfaz: el usuario escribe el número de variables, restricciones, orígenes, etapas, etc., con nombres y unidades. Debe funcionar con un problema pequeño y con uno del tamaño máximo, sin tocar el código.

- Validación: si hay campos vacíos, texto en vez de números o datos imposibles, muestra un mensaje claro y el programa no se cierra.

- Paso a paso de cada método (Sección 2) y resultado final con los nombres y unidades del problema, no solo x1, x2.

- Aviso de casos especiales con un mensaje claro (infactible, no acotado, empates, etc.).

- Visualización clara: tablas por iteración y, según el método, la gráfica o las tablas de la Sección 2.

- Ejemplos precargados: el caso real y al menos otros 2 problemas de prueba, incluyendo uno infactible o con un caso especial.


- Entrega ordenada: archivo README con instrucciones para instalar y ejecutar; código con comentarios que digan qué paso del método hace cada parte; al menos 5 pruebas automáticas.

- Análisis de sensibilidad (obligatorio para todos los grupos, sobre su problema de PL): precio sombra de cada restricción, rango de cada cj y rango de cada bi, con una frase que explique qué significa para la decisión. Si el grupo tiene Simplex o Simplex Dual lo calcula desde la tabla óptima; si solo tiene el método gráfico lo calcula con el gráfico, cambiando los datos y volviendo a resolver. El grupo 8 lo presenta como su segundo método, con costos reducidos incluidos y un rango comprobado en el gráfico. En transporte y programación dinámica no se exige.

## 5. El problema real

- Debe venir de una empresa, negocio u organización real (puede ir anónima), con datos y su fuente. Si algún dato es estimado, se dice cómo se estimó.

- Se explica qué se decide, qué se quiere optimizar y qué limita la decisión, y por qué importa (con al menos una cifra).

- Tamaño mínimo: PL con 2 variables (método gráfico) y 4 restricciones; PL sin gráfico, 3 variables y 3 restricciones; transporte 3 × 3; programación dinámica, 4 etapas.

- No se acepta: problemas copiados de libros o internet, datos inventados sin justificación o problemas de juguete.

## 6. Informe escrito (PDF, lenguaje formal)

| Parte | Qué debe tener |
| --- | --- |
| 1. Problema y contexto | Descripción del problema real, contexto, por qué es importante, alcance y al menos 5 |
|   | supuestos. |
| 2. Modelo matemático | Variables de decisión con unidades, función objetivo, restricciones y qué significa cada una |
|   | en el problema. Primero el modelo general del método y luego el del caso real. Para |
|   | programación dinámica: etapas, estados, decisiones y recursión. |
| 3. Software | Esquema de módulos, lenguaje y herramientas, capturas de pantalla con explicación de uso |
|   | y el código comentado (anexo o repositorio). |
| 4. Resultados y | Resultado de cada método, verificación con una herramienta aparte, comparación (Sección |
| análisis | 3) y análisis de sensibilidad explicado en palabras para quien toma la decisión. |
| 5. Conclusiones | Al menos 3 aprendizajes, 3 limitaciones del modelo o del software y 3 mejoras posibles. |
| Anexos | Datos del caso real con su fuente; manual de usuario de máximo 2 |
|   | páginas. |

## 7. Las tres entregas

| Entrega | Qué se sube a la plataforma | Qué se sustenta (10 min) Cómo se califica |   |
| --- | --- | --- | --- |
| 1 | Informe de 4 a 8 páginas: | El problema real y el modelo | Planteamiento 6 % · Justificación y |
| 20 oct 2026 | problema, contexto, por qué | preliminar. Sin software. | alcance 4 % · Formulación preliminar |
| 20 % | importa, alcance, supuestos y |   | 6 % · Redacción 4 % |
|   | modelo preliminar (variables, |   |   |
|   | objetivo, restricciones). |   |   |
| 2 | Informe con el modelo completo, | El modelo, el diseño y el | Modelo completo 8 % · Primer |
| 27 oct 2026 | el diseño del sistema (esquema y | primer método | método 7 % · Diseño 5 % · |
| 30 % | pantallas) y los resultados | funcionando con el caso | Resultados 6 % · Redacción 4 % |
|   | iniciales; código del primer | real y con un problema |   |
|   | método. | nuevo del docente. |   |
| Final | Informe final corregido, código | Todo el proyecto: los dos | Sistema funcional 10 % · Los dos |
| 10 nov 2026 | completo y README. | métodos, la sensibilidad y | métodos 10 % · Sensibilidad 8 % · |
| 50 % |   | un problema nuevo del | Comparación 7 % · Documentación 7 |
|   |   | docente. | % · Conclusiones 5 % · Presentación |
|   |   |   | 3 % |


- Todo se sube a la plataforma del curso antes de que empiece la sesión de ese día.

- Cada entrega incluye la anterior ya corregida.

- La nota de cada entrega se da con el documento y la sustentación juntos: lo que se entrega y lo que el grupo sabe explicar.

## 8. Cómo son las sustentaciones

En las tres entregas la sesión dura 2 horas y sustentan los 10 grupos: 10 minutos por grupo más 1 minuto para el cambio. Quedan 11 minutos de margen al final. El orden es por número de grupo, salvo que el docente avise otro. El “minuto 0” es la hora de inicio de la sesión.

| Grupo | Empieza | Termina | Grupo | Empieza | Termina |
| --- | --- | --- | --- | --- | --- |
| 1 | min 0 | min 10 | 6 | min 55 | min 65 |
| 2 | min 11 | min 21 | 7 | min 66 | min 76 |
| 3 | min 22 | min 32 | 8 | min 77 | min 87 |
| 4 | min 33 | min 43 | 9 | min 88 | min 98 |
| 5 | min 44 | min 54 | 10 | min 99 | min 109 |

| Entrega | Los 10 minutos de cada grupo |
| --- | --- |
| 1 | 0 – 4: problema real, contexto y por qué importa. |
|   | 4 – 8: modelo preliminar: variables, objetivo y restricciones. |
|   | 8 – 10: preguntas del docente. |
| 2 | 0 – 2: modelo completo. |
|   | 2 – 3: diseño del sistema (esquema y pantallas). |
|   | 3 – 5: demostración del primer método con el caso real. |
|   | 5 – 8: problema nuevo del docente: ingresarlo, resolverlo y explicar el resultado. |
|   | 8 – 10: preguntas del docente. |
| Final | 0 – 2: problema real y modelo. |
|   | 2 – 4: demostración con el caso real: los dos métodos y la sensibilidad. |
|   | 4 – 8: problema nuevo del docente: ingresarlo, resolverlo con los dos métodos y explicar el resultado. |
|   | 8 – 10: conclusiones (1 minuto) y preguntas del docente. |

- Diapositivas: máximo 3 por grupo.

- Problema nuevo (pequeño): PL hasta 4 variables y 4 restricciones (2 variables si el método es gráfico); transporte hasta 3 × 4; programación dinámica hasta 4 etapas. Puede traer un caso especial (infactible, empates, etc.).

- Preparación: un computador por grupo con el software ya instalado y probado. El grupo que sigue espera con el programa abierto. Todos los integrantes hablan al menos una vez.

- Tiempo: a los 10 minutos se corta y se califica lo que alcanzó a mostrar. Máximo 2 preguntas, a cualquier integrante.

## Reglas que bajan la nota

- El software solo resuelve el caso real (datos escritos en el código): “Sistema funcional” y “Los dos métodos” valen 0.

- Un método usa una librería que lo resuelve: ese método vale 0.

- No se puede ejecutar con el README: máximo 50 % de “Sistema funcional”.

- Sin verificación aparte o sin interpretación de resultados: máximo 50 % de la nota de resultados.
