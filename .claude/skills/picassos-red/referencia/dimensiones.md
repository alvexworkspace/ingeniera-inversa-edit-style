# Las siete dimensiones y el vocabulario de diseño

Todo desarme describe cada escena con estas siete dimensiones y con las mismas palabras, para que dos estilos se puedan
comparar. Lo que mide el código sale de `scripts/rea/medir.py` (columna "Código"); lo de juicio lo escribe la IA en el
desarme y lo confirma el dueño (columna "Juicio"). La columna "A ojo" se mide sobre hojas de cuadros (abajo): el
código de esas métricas existe, pero no es confiable en estilos con barridos, desenfoque o dibujo sobre decorado 3D
y `comparar.py` las saca del ranking.

| Dimensión | Código (`scripts/rea/`) | A ojo (hojas de cuadros) | Juicio |
|---|---|---|---|
| 1. Diseño | paleta por plano, reparto 60-30-10 real, saturación, negros y blancos, texto en pantalla y su tamaño | | composición, foco, equilibrio, contraste, familias de letra y su uso, forma de las esquinas |
| 2. Animación | cuadros estáticos y cuánto cambia el cuadro (con cuidado) | en uno, dos o tres: se cuentan los dibujos distintos de una parte del personaje en 12 cuadros seguidos | qué se anima, curva, escalonado, qué la dispara |
| 3. Cámara | tiempo quieta, en empuje, alejamiento o paneo, velocidad del paneo y paralaje (con cuidado) | magnitud del empuje y su curva (regla sobre la hoja); escala del personaje (% del ancho) y altura de cámara | intención: tensión, revelación, seguir al personaje |
| 4. Ilustración (si hay dibujo) | grosor y color del contorno, razón de oscuridad de la sombra, nitidez del borde (con cuidado) | grosor y color de línea por capa (personaje, utilería en mano, utilería del set, fondo) | dirección de la luz, proporciones del personaje, nivel de acabado por capa |
| 5. Sonido | volumen y pico | efectos por minuto y en qué palabra, de oído | qué evento lleva sonido y cuál no, música por tramo |
| 6. Ritmo | | cortes duros, transiciones y su tipo, duración de plano, primeros 3 s | dónde respira y dónde acelera |
| 7. Guion contra pantalla | | qué cambio cae en qué palabra: cuadros a -0,25, 0 y +0,25 s de la palabra clave | qué se muestra de lo que se dice: literal, metáfora, texto, gráfico o la cara; antes, en o después de la palabra |

## Hojas de cuadros (lo que va a ojo)
`ffmpeg -ss <inicio> -t <seg> -i video.mp4 -vf "fps=<n>,scale=270:-1,drawtext=fontfile='<fuente>':text='%{pts\:hms\:<inicio>}':x=4:y=4:fontsize=18:fontcolor=white:box=1:boxcolor=black,tile=6x4" -frames:v 1 hoja.jpg`

`<fuente>` es una fuente del sistema. En Windows, `C\:/Windows/Fonts/arial.ttf`. En Linux, por ejemplo
`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`. En macOS, `/System/Library/Fonts/Supplemental/Arial.ttf`.
- Ritmo: una hoja cada 5 cuadros del video entero; se marca cada cambio de plano y si cabe en 2 cuadros (corte) o
  necesita 3 o más (transición, con su tipo). En una pasada a mano sobre un estilo de animación con muchos barridos,
  30 de 33 cambios coincidieron con el ojo: sirve de calibración, no de verdad automática.
- Animación: hoja de 12 cuadros seguidos (fps del video) recortada sobre el personaje.
- Guion: las palabras clave salen de `palabras.json` y se mira la hoja de tres cuadros alrededor de cada una.
- Se mide en 3 a 5 videos de la referencia, no en todos, y el dato lleva `origen: a ojo`.

## El vocabulario de diseño (Joseph: 17 tips y el estilo premium)
- **Composición:** regla de tercios. El centro es la zona de foco (lo principal) y los bordes son secundarios
  (subtítulos, relleno). En vertical con cara: la cara en el tercio de arriba y el texto en el de abajo.
- **Equilibrio:** con dos elementos, cada uno en una mitad: horizontal, vertical o diagonal. En diagonal, uno grande y
  otro chico, y el de atrás menos saturado.
- **Contraste:** se lleva la mirada con color, tamaño, textura o forma.
- **Color:** 60-30-10 (primario, secundario, acento). El acento sale del propio material: se elige un color de la toma
  (la lámpara, la camisa), se saca su versión brillante y su versión oscura, y un blanco y un negro teñidos hacia él.
  Así el estilo se lleva a cualquier grabación en vez de copiar un hex.
- **Letra:** una sans para casi todo (peso 300 a 400) y una especial (serif, script o la misma sans en 600 a 700) para
  la palabra que importa.
- **Forma:** esquinas rectas, apenas redondas o muy redondas, siempre las mismas.
- **La escena sale del guion:** ¿la frase habla de un objeto, de dos, de un número, de algo real que hay que ver, o es
  una transición? Eso decide el tipo de escena.
- **Fórmula para desarmar una escena:** elementos (fondo, objeto, forma, texto), efectos sobre cada uno (desenfoque,
  desaturar, textura) y la animación con que entra.

## Las categorías de escena
Se parte de estas y se suman las nuevas que traiga cada estilo, en `referencia/categorias.md` cuando exista la primera
nueva. Cada estilo dice cuáles usa.
- Texto del gancho · texto del cuerpo (subtítulos)
- B-roll de video (completo con texto, con flecha y texto, con caja que sigue al objeto, líneas con paneo)
- B-roll de imagen (lado a lado con texto, texto detrás del sujeto)
- Pantalla completa: dos objetos · gráficos y números · elementos reales dentro de la animación · un objeto al centro
- Transiciones · faceless (lo que reemplaza a la cara) · ilustración (personaje, decorado, reacción)

## Cada animación se guarda en tres piezas
1. **La imagen fija** del momento más claro (`capturas/rNN-aMM-fija.jpg`).
2. **La hoja de cuadros clave** (6 a 10 cuadros rotulados, `capturas/rNN-aMM.jpg`).
3. **La ficha** en `reels/rNN.md`: elementos, efectos, animación (curva y cuadros), qué la dispara en el guion y su
   categoría.

Tope: si un estilo tiene muchas, se desarman hasta 15 por categoría, las que el dueño marcó primero.
