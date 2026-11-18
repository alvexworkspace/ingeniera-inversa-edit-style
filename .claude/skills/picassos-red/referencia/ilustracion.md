# Modo ilustración y animación

Para un estilo donde lo que lo define es el dibujo: personajes, decorados, trazos, sombras y luz. Es lo más difícil de
destilar porque lo que se siente "de ese creador" está en detalles finos. Se estudia la lógica del estilo, nunca sus
personajes ni su mundo: el dueño tiene los suyos.

## 1. Separar en capas
Cada capa se estudia por su lado: decorado, personajes, objetos, trazo, color plano, sombras y luz, cámara y tiempo
de la animación. Un caso típico: decorado 3D con luz y personaje 2D plano encima, dos niveles de acabado.

## 2. Medir cada capa
`scripts/rea/medir.py` da contorno (grosor y color), razón de oscuridad de la sombra, nitidez del borde, negros, paleta
por plano, cámara y cuadros sostenidos. A ojo, y dicho como estimado: dirección de la luz (de dónde caen todas las
sombras), proporciones del personaje (cuántas cabezas mide, ojos y manos), el lado del contorno que va más grueso.

## 3. Copia maestra antes de animar
Se eligen de 5 a 10 cuadros clave de la referencia y se recrean uno por uno, quietos, con el motor del dueño. Cada
recreación se superpone sobre el original y se comparan las medidas de las dos con `scripts/rea/comparar.py`: sombra
más clara, trazo más fino, cabeza más grande. Solo cuando el cuadro quieto pasa, se anima. Corrige una cosa por ronda
en vez de cinco a la vez.

## 4. Hoja de modelo
Como en la animación de verdad: el personaje de frente, de lado y de espaldas, sus expresiones y sus poses, con las
medidas del paso 2 escritas al lado (grosor del contorno, color de la sombra, proporciones). Va en el lienzo,
junto al tablero. Sin ese lienzo no se sintetiza.

## 5. Las reglas del porqué
Además de los números, las reglas que dejan crear escenas nuevas: "la luz viene de un solo lado y el contorno engorda
del lado contrario", "la sombra es el mismo tono más oscuro, nunca gris", "lo que importa del chiste se dibuja más
grande y entra en su palabra".
