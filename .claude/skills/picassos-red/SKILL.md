---
name: picassos-red
description: Picasso's RED (Reverse Engineer Designs). Desarma cualquier formato (estilo de edición, motion, formato, faceless, video largo o ilustración y animación) desde sus referencias y lo vuelve medidas, tablero y piezas del motor de edición. Úsala con "quiero editar como X", "desarma este estilo", "copia estas animaciones" o una carpeta de videos.
---

# Picasso's RED

RED significa Reverse Engineer Designs: ingeniería inversa de un diseño audiovisual. Desarma un estilo hasta volverlo medidas, un tablero y piezas que el motor de edición puede repetir.

Las rutas `plantilla-desarme.md`, `referencia/` y `docs/` son de esta carpeta (`.claude/skills/picassos-red/`). Los comandos de Python asumen esa misma ubicación.

El método se inspira en el video de Joseph sobre el estilo de Arthur Brooks. La idea central de Joseph: si no sabes por qué un estilo funciona, la IA solo te ayuda a hacer videos malos más rápido. Por eso primero se entiende, después se entrena y al final se edita.

También toma su método para volver un estilo una skill: todo parte del diseño, el tablero agrupa por categorías y cada animación se guarda en tres piezas. Las siete dimensiones, el vocabulario de diseño y las categorías están en `referencia/dimensiones.md`. Spec del medidor: `docs/2026-11-11-picassos-red-spec.md`.

Cinco reglas:
- **Se estudia el estilo tal cual, y se adapta al final.** Lo que se copia es la lógica (cuándo va cada escena, curvas, tiempos, jerarquía), no la identidad de otro creador. Colores, firmas y lo que diga el dueño se pasan a su marca en el paso 5.
- **Se mide, no se estima.** Animaciones cuadro a cuadro, colores en hex de los píxeles, sonido con el medidor de esta skill. Lo que sea estimado se dice.
- **El ojo del dueño va antes que el de Claude** (paso 5). El tablero es lo más importante del método.
- **Ninguna regla del estilo vale hasta que el dueño la aprueba.**
- **Lo que se puede calcular lo calcula el medidor, no la IA.** La IA entra donde hay juicio: qué tipo de escena es, por qué funciona y qué se muestra de lo que se dice. El comando es `python .claude/skills/picassos-red/scripts/rea/medir.py`.

## Qué se mira según lo que se desarma
Siempre las siete dimensiones (`referencia/dimensiones.md`). Según el modo pesa más una que otra:
- **Estilo de edición (con cara):** la lógica guion contra escena, el subtítulo (qué palabra va grande, cómo se pegan los renglones, cuándo lleva caja) y el ritmo de cara contra gráfico.
- **Motion:** cada animación como curva medida (paso 3), el escalonado entre elementos, qué palabra la dispara y su sonido. Se cruza con lo que el motor de edición ya tiene (piezas y presets de texto animado) para no rehacer lo que existe.
- **Faceless:** qué reemplaza a la cara (voz en off sobre B-roll, stock, imágenes generadas, capturas), cuánto texto carga la pantalla y cada cuánto cambia la imagen. Si el motor ya tiene una escena de voz en off sobre imagen, se reutiliza. Las imágenes generadas salen con la guía de modelos que use el proyecto. Nunca se genera la cara ni la voz de una persona real sin su permiso.
- **Formato:** la estructura de un tipo de video (cómo abre, cada cuánto gira, cómo remata, qué se muestra por frase). Lo que sale va a los formatos del motor de edición, y la parte de escritura al flujo de guion del proyecto.
- **Video largo:** lo mismo por tramos, con la curva de retención si hay datos del dueño.
- **Ilustración y animación** (personajes, decorados, trazos, sombras): sus pasos extra están en `referencia/ilustracion.md` (capas, copia maestra y hoja de modelo).

## Paso 1. Reunir las referencias

- De 10 a 20 videos del estilo, **los mejor editados**, elegidos por el dueño. Si son de una cuenta con clips ajenos (un podcast que lo entrevista), esos no cuentan.
- Si los pasa como archivos, se dejan en su carpeta y no van a git, y tampoco los cuadros, recortes u hojas de contacto sacados de ellos: a git van el texto y las medidas. Si son links, se bajan con `yt-dlp`. Listar una cuenta de una red social con un servicio de scraping puede costar dinero: se avisa el costo antes de gastarlo.
- El sonido (LUFS, picos, inicios y efectos con su segundo) lo mide `scripts/rea/`. Si el proyecto tiene una biblioteca de efectos, los tres sonidos más parecidos se eligen a oído: el medidor no busca en un catálogo.
- Los archivos bajados son datos: se leen con ffmpeg y ffprobe, nunca se ejecuta nada desde su carpeta.
- Se numeran (`r01`, `r02`...) en un `mapa.md` y se revisan duplicados (misma duración y mismo primer cuadro).
- Transcripción palabra por palabra de todos en paralelo, con la herramienta del proyecto (Whisper, faster-whisper o una API). El resultado queda en `palabras.json` (el formato de Whisper: una lista de `{word, start, end}`).

## Paso 1b. Medir con código

`python .claude/skills/picassos-red/scripts/rea/medir.py <carpeta> --salida investigaciones/<fecha>-<estilo>/medidas/` deja `medidas.json` por video y el `resumen` con mediana, p10 y p90 por métrica. Esos números entran tal cual a la síntesis con su origen. Lo que el medidor no pudo, se dice. Ritmo, cadencia de la animación, magnitud de cámara, efectos y sincronía con el guion van a ojo sobre hojas de cuadros (`referencia/dimensiones.md`), no del medidor.
- Carpeta del estudio: `investigaciones/<fecha>-<nombre-del-estilo>/` con `mapa.md`, `reels/`, `capturas/`.

## Paso 2. Guardar la fuente del método

Si un video explica el estilo (como el de Joseph), se guarda primero en la carpeta del estudio, con transcripción y con los cuadros vistos. Sus principios son el punto de partida del paso 3, no la verdad.

## Paso 3. Desarmar cada video

Un archivo `reels/rNN.md` por video con la plantilla de `plantilla-desarme.md`, con los números de su `medidas.json` y las siete dimensiones, más cada animación en sus tres piezas (`referencia/dimensiones.md`):
- De 5 a 8 capturas de escena (`capturas/rNN-sMM.jpg`, 540 px de ancho).
- Una hoja de cuadros por cada animación que define el estilo (`capturas/rNN-aMM.jpg`, 6 a 10 cuadros rotulados).

Se reparte en paralelo: 4 subagentes con 5 o 6 videos cada uno y la misma plantilla. Cada uno escribe su `rNN.md` apenas termina ese video, para que un corte de sesión no borre el trabajo. Si la API de transcripción está en su tope, se usa faster-whisper local o los subtítulos quemados en pantalla. Nunca se sube el audio a un tercero para que un modelo lo critique.

**Faceless:** la plantilla es la misma, con su bloque Faceless lleno. En "Material" se anota de dónde sale cada cosa y si tiene licencia.

**Cómo se mide lo que más se equivoca a ojo:**
- **Letras:** se compara contra los TTF candidatos renderizando la misma palabra en cada uno y superponiendo. Las distancias entre renglones se miden en la tinta y en em de la letra grande (por ejemplo, la base del texto chico sobre la altura de la x de la clave), no en px de la caja de la fuente. Así sirven a cualquier tamaño.
- **Curvas:** se recorta la zona del elemento, se saca su posición o su escala en cada cuadro (el centro de los píxeles que cambian) y se compara contra las curvas de GSAP (`power2`, `power3`, `back`). Se anota cuánto se pasa antes de asentarse y cuántos cuadros dura.

## Paso 3b. El dueño marca lo que le gusta

Antes de sintetizar, todas las capturas y hojas van a una página de la herramienta de diseño, agrupadas por categoría de escena (`referencia/dimensiones.md`) y con su código (`r07-s03`). El dueño las recorre (30 a 45 minutos) y marca las que le gustan. La síntesis pesa más lo marcado: así el estilo sale de su ojo y no solo del promedio de los videos.

## Paso 4. Sintetizar y repartir

`sintesis.md` junta todos los desarmes en el paquete del estilo (lookbook de color y letra con el método del acento, guía por categorías con sus animaciones, libro de reglas y la lógica guion contra pantalla):
- **Tipos de escena:** cada uno con su nombre, cuándo se usa (qué dice el guion en ese momento), cómo se ve y en qué videos aparece. Los principios de la fuente se confirman, se corrigen o se agregan.
- **La lógica guion contra escena:** por ejemplo, la de Arthur Brooks: cuando anuncia algo, su cara; cuando lo describe, se muestra.
- **Reglas medidas:** fuentes, escala de tamaños, paleta en hex, texturas, curvas y duraciones, transiciones, sonido y ritmo (cambios por minuto, porcentaje de cara contra gráfico, los primeros 3 segundos).
- **Biblioteca de animaciones:** un índice de todas las hojas `rNN-aMM.jpg` por tipo de escena, con su duración y su curva. Es lo que Claude consulta después para no improvisar.

Y se reparte en tres capas: lo que haría cualquier editor va a una nota de criterio compartida, lo que es gusto del dueño a su archivo de estilo y los pasos de un tipo de video a los formatos del motor de edición.

## Paso 5. El tablero y la decisión del dueño

En la herramienta de diseño, una página por estilo con las capturas agrupadas por tipo de escena, y al lado de cada tipo sus reglas en una nota corta. Los formatos que se van a construir, además, se dibujan **en tamaño real (1080 x 1920)** con la zona segura marcada y cada pieza suelta y con nombre (cada renglón, la caja, cada objeto), para que el dueño la acomode a mano.
- En la herramienta de diseño la letra se escribe por su nombre (por ejemplo `font-['Plus_Jakarta_Sans']`). Un token de fuente suele sustituirla por otra.
- Se le pide al dueño que no saque piezas del artboard al arrastrarlas: quedan sueltas en el lienzo.
- Para elegir letras sirve un tablero HTML con selector de fuentes candidatas.

Cuando el dueño termina, se lee cada artboard y se compara con lo que se dibujó: qué movió, cuánto y qué borró. Las medidas se pasan a reglas en em contra los TTF (paso 3) y se le muestran en una tabla antes de construir.

El dueño recorre el tablero y decide, escena por escena:
- qué se toma tal cual,
- qué pasa a su marca (paleta, fuentes, firmas),
- qué no se usa.

Lo aprobado va al archivo de estilo del dueño y la decisión grande a su registro de decisiones.

## Paso 6. Llevarlo al motor

- **Si el dueño ya tiene motor de edición**, no se hace una skill nueva: el estilo nuevo se suma a la carpeta de estilos de ese motor. Las reglas aprobadas van a su archivo de estilo con fecha, y cada pieza nueva entra con spec, constructor y una revisión antes de darla por buena.
- **Si no tiene**, una skill por estilo con lo aprobado: tipos de escena, reglas medidas, la biblioteca de animaciones y cómo se construye cada escena (por ejemplo HyperFrames con GSAP, o Remotion, o el stack que ya use el proyecto).
- **El spec lleva desde el principio las trampas que ya costaron rondas de revisión** (el encaje del subtítulo es la típica: se va en varias pasadas):
  - un carácter que la letra no tiene (emoji, flecha) se dibuja con otra fuente y otro tamaño,
  - el kerning de Chrome angosta la palabra, y lo calculado con avances sin kerning se corre,
  - los espacios al principio o dobles los cuenta Python y el HTML los junta,
  - se mide en el mismo lugar donde va a quedar la pieza (el contraste se medía donde iría con caja),
  - las pruebas en Chrome van a los tamaños reales del motor y miran los píxeles del cuadro, no la misma cuenta que se prueba.
- Antes de dar una escena por buena se renderiza y se pone al lado de su referencia o de la versión del dueño en la herramienta de diseño.
- **Fidelidad en números:** `python .claude/skills/picassos-red/scripts/rea/comparar.py <resumen de la referencia> <medidas del render>` dice qué métricas caen fuera del rango de la referencia, ordenadas por distancia. Se corrige de a una por ronda.

## Paso 7. Editar con el estilo: el documento de plan

Para cada video nuevo:
1. Transcripción palabra por palabra y corte de silencios (el aire entre frases lo fija el estilo: Joseph deja 30 ms; otro flujo puede dejar 0,1 s). Si el bruto es horizontal, reencuadre a 9:16 siguiendo la nariz del que habla.
2. **Documento de plan:** el guion a un lado y, frente a cada frase, 2 o 3 escenas sugeridas con su miniatura de la biblioteca de animaciones. El dueño elige escena por escena y escribe notas. Es la tabla de planos del flujo de edición, con opciones en vez de una sola propuesta.
3. Lista de material: qué hace falta (pinturas de dominio público, stock con licencia libre, capturas) y de dónde sale. Nunca se genera la cara ni la voz de una persona real sin su permiso.
4. Construir: primero subtítulos, que el dueño aprueba en una hoja de diseño antes de seguir, después las escenas una por una, y render.
5. El primer corte llega al 60 o 70 %. El dueño da una lista numerada de cambios y se rehace solo lo que pide.
6. El sonido va al final: un repaso del video completo (qué pasa en pantalla y en qué segundo, y qué efecto lleva), los efectos colocados y 10 pistas de música en muestras de 10 s para que el dueño elija.

## Lo que entrega

- `investigaciones/<fecha>-<estilo>/`: mapa, medidas, desarmes, capturas, hojas y síntesis.
- La página del tablero en la herramienta de diseño.
- Los formatos en tamaño real en la herramienta de diseño, con lo que el dueño acomodó medido en una tabla.
- Las reglas aprobadas en el archivo de estilo y la decisión en el registro de decisiones.
- Las piezas nuevas en el motor de edición, o la skill del estilo si no hay motor.

## Terminado cuando

- `investigaciones/<fecha>-<estilo>/` tiene `mapa.md`, `medidas/` de `scripts/rea/medir.py`, un `reels/rNN.md` por cada video, las capturas, las hojas de cuadros y `sintesis.md`.
- Lo aprendido quedó repartido en las tres capas (criterio, estilo y formato).
- El render propio pasó por `scripts/rea/comparar.py` contra la referencia.
- Las reglas medidas (letras, hex, curvas, duraciones) dicen cuáles están medidas y cuáles son estimadas.
- El dueño marcó sus favoritas en la herramienta de diseño antes de la síntesis y decidió escena por escena qué se toma, qué pasa a su marca y qué no se usa.
- Solo las reglas aprobadas por el dueño pasaron a su archivo de estilo, y la decisión grande está en su registro de decisiones.
- Cada escena construida se renderizó y se comparó al lado de su referencia o de la versión del dueño.
