---
id: todo-error-se-vuelve-regla-escrita-y-los-estancamientos-piden-una-palanca-de-base
principio: Cada error se escribe como regla en un archivo de lecciones que se lee antes de construir, y cuando el puntaje sube solo unas décimas por ronda se busca una palanca de base, en vez de seguir arreglando plano por plano
capa: oficio
fuentes: make animated shorts with claude code full workflow
fecha: 2026-11-05
---
## Qué decide quien lo enseña

Decide que la memoria del proyecto es un archivo de lecciones obligatorio, de una línea cada una (qué encontró el revisor, qué lo arregló), que se lee antes de construir y antes de cada ronda de arreglos. Cuando la mejora cae a unas 0,3 por ronda, deja de pulir y busca la causa sistémica. Así la siguiente pieza arranca más arriba: una nueva de 15 segundos empezó en 6,2 en media hora, contra el 4,2 del primer intento tras un día entero.

## Por qué

Los errores se repiten si solo viven en la cabeza de una sesión. Y en la fuente el estancamiento tenía una causa de base: se renderizaba a menor resolución y se escalaba, lo que limitaba el detalle, y pasar a la resolución final dio un 43 % más de energía de bordes. Un cambio grande de rig mueve el puntaje solo si se revisan los efectos secundarios en todos los planos.

## Funciona

- Una lección numerada por hallazgo, copiada de vuelta a la plantilla para la siguiente pieza.
- Renderizar a la resolución de entrega desde el primer día y archivar cada ronda: la del 4,2 se perdió y hacía falta como el antes.
- Tras un cambio grande, volver a renderizar los planos aprobados y compararlos con los anteriores.

## No funciona

- Dar un tiempo estimado sin mirar el reloj: los plazos de los agentes se pasaron cerca de un 50 %.
- Culpar al último cambio sin buscar el origen.

## Cuándo no aplica

- Si la pieza es de una sola vez y no habrá una siguiente, el archivo de lecciones no se amortiza.
- Si el puntaje ya alcanzó el umbral de aprobación, no se busca más palanca.
