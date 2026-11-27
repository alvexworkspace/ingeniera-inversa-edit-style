---
name: oficio-de-edicion
description: La puerta de todo video, en tres capas (oficio, formato y estilo). Úsala con "edita este reel", brutos, un faceless, motion, un tutorial, un anuncio, una clase de curso o un video de YouTube, o para probar otro estilo. También con "por qué funcionó este video" o "cómo replico este video": eso está en contenido/. Si no hay estilo, pide Picasso's RED.
---

# Oficio de edición

Esta skill es la puerta de todo video. El oficio y el formato viven aquí y sirven a cualquier proyecto. El estilo lo pone el dueño del video, en `estilos/`. Cada capa vive en un solo lugar:

| Capa | Qué guarda | Dónde |
|---|---|---|
| 0. Reglas de todo video | Zonas seguras, sonido, movimiento y verificación | `reglas.md` |
| 1. Oficio | Lo que haría cualquier editor con cualquier estilo: ritmo, cortes, retención, subtítulos legibles, sonido bajo la voz | `oficio/editor/` y, si el video es animado, `oficio/motion/` |
| 2. Formato | Los pasos para hacer un tipo de video. Sin gustos | `formatos/` |
| 3. Estilo | Cómo se ve y suena: letras, colores, escenas, sonidos y lo que su dueño aprobó | `estilos/` |

Se leen en ese orden. `reglas.md` va antes de las tres capas.

Picasso's RED (`picassos-red`) es quien crea un estilo. Esta skill es quien edita con él.

## Cómo se carga cada capa
1. **Las reglas.** Abre `reglas.md` de esta carpeta.
2. **El oficio.** Abre `oficio/editor/INDICE.md`. Si el video es animado, abre también `oficio/motion/INDICE.md`. Lee solo los principios que tocan. La prueba de qué es oficio: si otro editor con otro estilo lo haría igual, es oficio. Si no, es gusto y va al estilo.
3. **El formato.** Abre de `formatos/` solo el que toca, con la tabla de abajo. Si el usuario no dijo el formato, se pregunta y no se adivina.
4. **El estilo.** Lo busca la sección que sigue.

## El estilo
1. Busca `.claude/skills/oficio-de-edicion/estilos/*.md` desde la raíz del proyecto. Ignora `README.md` y `PLANTILLA.md`.
2. Lee `estilos/README.md` primero. Dice qué estilos hay, de quién es cada uno y si alguno es el de defecto.
3. Carga un solo estilo: el del dueño de este video. "Prueba este video en el estilo X" cambia solo esta capa.
4. **Si no hay estilo**, o no está el de este video, se dice en una línea ("este proyecto no tiene estilo para editar") y se usa Picasso's RED antes de seguir. No se inventa un estilo ni se toma el de otra persona. Picasso's RED pregunta el formato, desarma las referencias en un lienzo y guarda el archivo en `estilos/` con la plantilla.

## Qué formato abrir
| Se pide | Formato | Tamaño de trabajo |
|---|---|---|
| Reel o short vertical, con alguien a cámara | `formatos/reel-hablado.md` | 1080×1920, 9:16 |
| Video de YouTube horizontal | `formatos/largo.md` (modo YouTube) | 1920×1080, 16:9, salvo que el bruto mida otra cosa |
| Faceless, sin cara | `formatos/faceless.md` | El del lugar donde se publica |
| Motion o explicativo animado | `formatos/motion.md` | El del lugar donde se publica |
| Tutorial con pantalla | `formatos/tutorial-pantalla.md` | El del lugar donde se publica |
| Anuncio | `formatos/anuncio.md` | El de la plataforma, medido antes de editar |
| Video largo o clase de curso | `formatos/largo.md` (modo curso o YouTube) | El que dé `ffprobe` del bruto |

La resolución no se fija sin medir el bruto con `ffprobe`. Las zonas seguras están en `reglas.md`.

Si delegas en un subagente, ponle en el brief la ruta de esta skill, del formato y del estilo, porque la puerta no le llega sola.

## Por qué funcionó un video
Si traen uno o más videos que funcionaron y preguntan por qué o cómo replicarlos, se abre `contenido/README.md`. Explica la idea, el empaque, el gancho, la estructura y los comentarios, y entrega un `analisis-video.md` por video que termina en "Cómo replicarlo".
- Solo se analiza para replicar un video **validado**: es un atípico (2x o más de la mediana del canal) y el formato se repite con éxito en ese canal (al menos 3 videos recientes del mismo tipo a 1,5x o más). El detalle y los umbrales están en `contenido/README.md`. Si no pasa, se dice y se pide otro, o el análisis se marca **no validado**.
- Contenido es qué se dice y por qué se vio. Cómo se ve y suena es estilo, y lo desarma Picasso's RED. Si piden las dos cosas, primero contenido y después el RED con los mismos videos, siempre que estén validados.

## El storyboard: la puerta antes del render
Todo video pasa por aquí antes del render completo, en cualquier formato:
- **Primero el look, después el video.** Cuando el estilo es nuevo o cambia (otro set, otro personaje, otra línea), se muestran 2 o 3 cuadros fijos del look final, al lado de la referencia, antes del storyboard completo. No se renderiza ningún video, ni siquiera un clip de prueba, hasta que el dueño apruebe el look en el chat. Si da otra corrección, se vuelve a cuadros fijos.
- **Son cuadros reales del video,** sacados del motor sin renderizar el corte final: uno por toma o por frase, con lo que se dice y lo que se ve. Un texto o una tabla sola no cuenta como storyboard.
- **Se le muestran al dueño en el lienzo** que use el proyecto (Figma, Wonder, Paper, Excalidraw o el que ya tenga), no como archivos sueltos. Si hay un MCP o un conector de esa herramienta, se usa. Si no, se exportan los cuadros y una guía para armar la página a mano.
- **El dueño marca cada cuadro** como bien o cambia. Se corrige y se vuelve a mostrar hasta que lo apruebe. Solo entonces se renderiza. Cada corrección nombra el segundo (o el cuadro), qué está mal y cómo debería verse, o manda una captura de ese instante. No se pide "rehaz el video entero".
- **Antes del render largo** se revisan capturas de los momentos clave. El motor que escribe el código no sustituye esa mirada "viendo" el video a puro screenshot en su propio contexto: eso suele ser caro y flojo. Si hace falta un crítico de visión, es un paso aparte, o el dueño en el lienzo.
- **Si el estilo no tiene un motor que saque cuadros,** el storyboard se arma en el lienzo con el estilo cargado.

## Lo que no es de esta skill
- **Crear el estilo desde referencias:** Picasso's RED.
- **El guion y el texto de publicación:** el flujo de escritura del proyecto. `contenido/` solo entrega el análisis y la lógica que se puede repetir.
- **Publicar:** esta skill entrega el video. Nada se publica sin el OK del dueño en el chat.

## Dónde se guarda lo que se aprende
- **La prueba:** si otro editor con otro estilo lo haría igual, es oficio. Si no, es gusto del dueño y va a su estilo.
- **Gusto del dueño:** va a su estilo, bajo `## Gusto por formato: <formato>` con la fecha y sus palabras. Si vale para todo formato, va a la parte general del estilo.
- **Oficio nuevo:** se escribe como un principio más en `oficio/editor/` o `oficio/motion/`, con el mismo esquema de los que ya están, y se agrega al índice.
- **Un paso de un formato:** si sirve a cualquier marca, se cambia en `formatos/`. Si es solo de este dueño, va a su estilo.

## Terminado cuando
- Se cargaron `reglas.md`, el formato que tocaba y un solo estilo, o se dijo que no hay estilo y se pasó por Picasso's RED.
- El dueño aprobó el look en cuadros fijos y el storyboard de cuadros reales antes de cualquier render.
- El video pasó la verificación de su formato y la de `reglas.md`.
- Lo que el dueño aprobó o corrigió quedó en su estilo, con fecha.
- Nada se publicó sin el OK del dueño en el chat.
