---
id: los-numeros-detectan-deriva-y-la-calidad-se-mira-en-el-cuadro
principio: Las comprobaciones automáticas solo detectan deriva y la calidad se juzga mirando el cuadro junto a la referencia, en vez de dar por buena una pieza porque pasó todas las pruebas
capa: oficio
fuentes: make animated shorts with claude code full workflow
fecha: 2026-11-05
---
## Qué decide quien lo enseña

Decide mantener las dos cosas y no confundirlas. Una compuerta automática revisa archivos faltantes, tamaño de salida, saturación y brillo después de cada render, y es útil. Pero antes de aprobar se abre la imagen y se mira al lado de la referencia. Además, al inicio se hace una auditoría numérica de proporciones (altura de cabeza, grosor de contorno, ritmo de cortes), porque un revisor general no las detecta.

## Por qué

En la fuente el primer render pasó 37 de 37 pruebas y se veía mal: suelo rojo, personajes enterrados hasta la cintura, una noche magenta. Las pruebas medían lo que alguien pensó medir y no lo que se ve. Y tras siete rondas de revisión nadie había señalado que los cuerpos eran más cortos y los cortes más rápidos que en la referencia: eso lo encontró la medición.

## Funciona

- Correr la compuerta tras cada render y además abrir la hoja de contacto con un cuadro por plano.
- Medir proporciones y ritmo de la referencia y de la pieza al empezar, no solo puntuar al final.
- Antes de culpar el último cambio, buscar la causa raíz: un rojo de suelo vino de un realce de saturación del integrador y no del arreglo reciente.

## No funciona

- Aprobar porque el verificador sale en verde.
- Cambiar las proporciones de los personajes tarde: rompe toda cámara puesta a mano.
- Subir la saturación de noche para que tenga color: se vuelve chillón. El color nocturno sale del contraste entre azul y naranja.

## Cuándo no aplica

- En una pieza de pantallas de producto o de texto, donde lo que importa es si se lee o no y basta mirar.
- Si el motor ya tiene cientos de pruebas que cubren el aspecto, la compuerta pesa más, aunque mirar el cuadro nunca se omite del todo.
