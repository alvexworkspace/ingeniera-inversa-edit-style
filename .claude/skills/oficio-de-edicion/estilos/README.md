# Estilos

La puerta es la skill `oficio-de-edicion`. Trae las reglas de todo video, el oficio y los formatos. Aquí queda solo el gusto de cada dueño: letras, colores, escenas, sonidos y lo que esa persona aprobó o corrigió. La puerta lee este README antes que cualquier estilo.

Un paso de un formato que sirve a cualquier marca se cambia en `formatos/`. Si es gusto de una persona, va a su estilo, bajo `## Gusto por formato: <formato>`.

## Cómo se relacionan las capas
1. **Reglas** (`reglas.md`): zonas seguras, sonido, movimiento y verificación. Valen para todo video.
2. **Oficio** (`oficio/editor/` y `oficio/motion/`): lo que haría cualquier editor con cualquier estilo.
3. **Formato** (`formatos/`): los pasos de un tipo de video. Sin gustos.
4. **Estilo** (esta carpeta): cómo se ve y suena un dueño. Se carga uno solo por video.

## Esta carpeta empieza vacía
No hay un estilo de fábrica. Un estilo se crea con Picasso's RED (`picassos-red`): se pregunta el formato, se desarman las referencias, el dueño marca en el lienzo y lo aprobado se guarda aquí, copiando `PLANTILLA.md`.

| Estilo | Dueño | Archivo | Motor |
|---|---|---|---|
| | | | |

Cuando se suma uno, se agrega una fila. El de defecto, si lo hay, se dice en la fila.

## Lo que va en un estilo
- Lo que es gusto, no oficio: si otro editor con otro estilo no lo haría igual, va aquí.
- El gusto de un solo formato va bajo `## Gusto por formato: <formato>` (Reel, YouTube, Curso, Faceless, Motion, Anuncio, Tutorial), con fecha y las palabras del dueño.

## Sumar un estilo
1. Picasso's RED desarma los videos de referencia del formato que se preguntó al inicio y saca las reglas medidas.
2. El dueño marca el tablero en el lienzo y acomoda los formatos a tamaño real. Sin eso no hay síntesis.
3. Se copia `PLANTILLA.md` a `<nombre>.md`, se llena con lo aprobado y se agrega una fila a la tabla.
4. Si se renderiza con un motor, cada pieza nueva entra con spec, constructor y una revisión antes de darla por buena. El motor no se impone: lo dice el estilo.
