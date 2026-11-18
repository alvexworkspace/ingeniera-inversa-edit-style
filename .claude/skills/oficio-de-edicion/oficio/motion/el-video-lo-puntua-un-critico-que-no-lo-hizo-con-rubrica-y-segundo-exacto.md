---
id: el-video-lo-puntua-un-critico-que-no-lo-hizo-con-rubrica-y-segundo-exacto
principio: Un video animado lo puntúa un revisor fresco que no lo construyó, con rúbrica y el segundo exacto de cada punto descontado, y su queja se comprueba antes de actuar, en vez de que quien lo hizo se califique
capa: oficio
fuentes: make animated shorts with claude code full workflow
fecha: 2026-11-05
---
## Qué decide quien lo enseña

Decide que quien construye nunca se pone nota. Un subagente nuevo, sin el contexto de la obra, compara el render con la referencia, llena una rúbrica (actuación, tamaño de cara, nitidez, beat en pantalla, mundo, color, tiempo cómico, cámara, subtítulos, sonido) y nombra el segundo de cada descuento. Después quien construye abre ese segundo a resolución completa y solo corrige lo confirmado. A ese revisor se le entregan las sospechas propias para que las verifique.

## Por qué

Quien construye se ve con cariño: en la fuente el mismo render recibió 6,5 de quien lo hizo y 4,2 del revisor fresco, y la regla que sacó es que quien construye se califica unos dos puntos de más. Pero el revisor también falla: una ronda midió miniaturas y leyó mal el tamaño de los subtítulos, y otra dio notas distintas al mismo archivo (6 y 5,4). Por eso el puntaje es un juicio y no una medida.

## Funciona

- Rúbrica con criterios numerados, una prueba medible por criterio y un umbral de aprobación (los primeros cuatro criterios en 7 o más y el promedio en 8).
- Pedir los 3 arreglos principales por rango de cuadros y no por id de plano, porque los ids cambian.
- Abrir el cuadro señalado antes de mandar a arreglar.

## No funciona

- Que el constructor revise su propio render y declare que está listo.
- Aceptar la nota del revisor sin mirar la evidencia.
- Un revisor sin la referencia al lado: no sabe contra qué compara.

## Cuándo no aplica

- En una pieza de 10 a 15 segundos que se hace una sola vez para probar el motor, donde basta la revisión de ojo del dueño.
- Si no hay referencia con la que comparar, la rúbrica pierde su ancla y el revisor solo opina.
- Cada ronda de revisión y arreglo consume uso del modelo; con presupuesto cerrado se limita el número de rondas.
