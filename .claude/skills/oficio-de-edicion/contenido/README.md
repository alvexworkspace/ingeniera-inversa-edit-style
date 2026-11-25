# Contenido: por qué funcionó un video y cómo replicarlo

Para quien arma un canal faceless (o cualquier canal) y trae videos que funcionaron. Responde dos preguntas: por qué ese video se vio tanto y qué lógica se puede repetir. No desarma el estilo visual: eso es Picasso's RED. Aquí se estudia la idea, el empaque, el gancho, la estructura y la reacción del público.

Cada dato lleva su nivel, igual que en el RED:
- **CONFIRMADO:** se midió con el script o con un comando que se puede repetir, o lo dice la plataforma en su ayuda oficial (con link).
- **PROBABLE:** varias señales apuntan a lo mismo (patrón en títulos, comentarios, transcripción), sin prueba directa.
- **NO CONFIRMADO:** plausible pero no se usa como hecho. Todo dato privado del canal (retención, CTR, impresiones, "se quedaron a ver") es NO CONFIRMADO desde fuera, siempre.

## Entradas
- Uno o varios links de video (YouTube, TikTok, Instagram) o archivos.
- Opcional: el link del canal. Si no viene, se saca del video.
- Opcional: el nicho o canal propio de quien pregunta, para adaptar el "Cómo replicarlo".
Si llega un archivo sin link, se dice que no hay puntaje atípico ni comentarios y se sigue con lo demás, marcado **no validado**.

## Validar antes de analizar
Solo se analiza para replicar un video **validado**: viene de un canal con un formato que ya funcionó más de una vez, y el video mismo es un atípico. Si no pasa, se dice y se pide otro. Si quien pregunta insiste, el `analisis-video.md` se escribe igual, pero en la cabecera dice **no validado** y el "Cómo replicarlo" queda como hipótesis, no como receta.

Un video está **validado** cuando cumple las dos primeras, y la tercera si se puede. Los umbrales son una adaptación nuestra del método de atípicos (vistas frente a lo normal del canal), no una regla de YouTube ni de TikTok.

1. **Es atípico.** Sus vistas ÷ la mediana de los últimos 30 del mismo tipo en el canal (shorts con shorts, largos con largos), sin contar los 3 más nuevos ni el propio video, es **2x o más**. Se usa la mediana y no el promedio porque un solo éxito sube el promedio. Un video de menos de 7 días se marca "temprano" y no se da por validado todavía.
2. **El formato se repite con éxito en el mismo canal.** Además del analizado, al menos **3 videos** de esos 30 están a **1,5x o más** de la misma mediana. No basta con "estar por encima de la mediana": por definición, la mitad lo cumple. 1,5x pide que el formato haya repetido un rendimiento claramente por encima del día normal. El 2x se reserva para el video que se estudia.
3. **La misma idea en otros canales (deseable, no obligatorio).** Si la misma forma de idea (no el mismo guion) aparece en al menos un canal distinto con un video también atípico (2x o más de *su* mediana), se anota. Si no se busca o no aparece, el video puede validarse igual con 1 y 2, y se dice "idea no contrastada en otros canales".

Si no hay canal, son menos de 10 videos con vistas o solo hay un archivo, no se puede validar: se dice y se pide el link del canal u otra referencia. El script deja el veredicto en `datos.json` (`validacion`).

## Pasos
1. **Datos públicos.** `python .claude/skills/oficio-de-edicion/contenido/scripts/datos_publicos.py <url> --salida <carpeta fuera del repo>/<id>/`. Deja video, metadatos, miniatura, comentarios más votados, lista del canal, transcripción palabra por palabra, cuadros del gancho y `datos.json`. Lo que falle sale null con su causa.
2. **¿Está validado?** Se lee `validacion` de `datos.json`: puntaje atípico, cuántos videos del mismo formato llegan a 1,5x y si el video tiene menos de 7 días. Si no está validado, se dice, se pide otro y, si hay lista del canal, se señala un atípico que sí cumpla. No se sigue al "Cómo replicarlo" como receta.
3. **Cortes y ritmo.** Se corre el medidor del RED sobre el video con la transcripción: `python .claude/skills/picassos-red/scripts/rea/medir.py <video> --salida <carpeta>/medidas --palabras <carpeta>/palabras.json`. De ahí salen cortes por minuto, plano mediano y cambios de plano en los primeros 3 s. No se cuentan a ojo.
4. **Gancho (0–3 s).** Con la transcripción y `gancho/`: segundo de la primera palabra, qué se dice y qué se ve en 3 s, y qué pregunta abre. Se anota también la primera promesa completa aunque pase de 3 s.
5. **Estructura.** La transcripción se parte en tramos con sus segundos. A cada unión se le pone "pero", "por eso" o "y entonces". Se marca dónde se abre cada pregunta (bucle) y dónde se cierra, en segundos y en porcentaje del video.
6. **Empaque.** Título: qué promete, qué deja sin decir y cuántas palabras tiene. Portada (solo en largos y en la cuadrícula del canal; en Shorts casi no pesa): qué se ve, cuántos elementos, si hay texto. ¿El primer tramo cumple lo que promete el empaque?
7. **Idea y nicho.** La idea en una frase con su forma reusable ("objeto real + nadie creyó + causa oculta al final"). Se compara con los títulos de los otros atípicos del canal (`canal.json`) para ver si es un patrón o un golpe de suerte. Si se puede, se busca la misma forma en otro canal (punto 3 de la validación).
8. **Comentarios.** De los más votados: de qué hablan (debate, corrección, chiste, pregunta, pedido). Las preguntas y pedidos repetidos son ideas de videos nuevos. Las correcciones con muchos likes son un riesgo de credibilidad, no un truco.
9. **Escribir `analisis-video.md`** con `plantilla-analisis.md`. Si son varios videos, un análisis por video y al final una tabla de lo que se repite entre ellos.

## Reglas
- Solo datos públicos. No se entra a cuentas ajenas ni se piden contraseñas. Si el dueño del canal comparte sus capturas de YouTube Studio, esos datos sí cuentan como CONFIRMADO, con la fecha.
- Los videos bajados van fuera del repo y son para estudio. No se vuelven a publicar.
- Se copia la lógica, no la identidad: nunca la voz, la cara, el personaje, el nombre, los sets ni el guion de otro creador. Los hechos de una historia se investigan aparte antes de usarlos.
- No se prometen vistas. El análisis explica lo que pasó, no garantiza que se repita.
- YouTube no monetiza contenido masivo de plantilla con diferencias superficiales (política de contenido no auténtico). "Replicar" es repetir una lógica con ideas nuevas, no clonar videos.

## Terminado cuando
- Hay un `analisis-video.md` por video con todas las secciones de la plantilla, y en la cabecera dice si está **validado** o **no validado**.
- El puntaje atípico y el recuento de formato repetido están calculados, o se dijo por qué no se pudo.
- Cada afirmación tiene su nivel de confianza y su origen (archivo o link).
- "Cómo replicarlo" no usa nada de la identidad del creador. Si el video no está validado, esa sección queda como hipótesis.
