# Guion: las dos skills, en un video

Video de unos 11 minutos. Tono casual, en español latino, como quien le explica el paquete a un amigo que edita. En pantalla se ve la carpeta del repo, un lienzo vacío y, cuando haga falta, un recorte de un video de referencia. No se nombra ninguna empresa. No se muestra la cara ni la voz de una persona real generada.

Quien habla puede ser quien graba el tutorial, en cámara o en voz en off. Los tiempos son aproximados.

## 0:00 a 0:50. Qué es esto

**Se dice.** "Esto son dos skills para Claude Code, y trabajan juntas. Una se llama Picasso's RED. RED quiere decir Reverse Engineer Designs: ingeniería inversa de un diseño. La otra es el oficio de edición. RED aprende un estilo. El oficio edita con ese estilo. Si no tienes estilo, el oficio no inventa uno: te manda a RED."

**Se muestra.** El título en grande: Picasso's RED + oficio de edición. Abajo, la frase "primero se entiende, después se edita". Corte al árbol de carpetas: `picassos-red` y `oficio-de-edicion`.

## 0:50 a 1:40. Instalación

**Se dice.** "La instalación es copiar dos carpetas. En el proyecto donde trabajas con Claude Code, las pegas dentro de `.claude/skills/`. Una es `picassos-red`. La otra, `oficio-de-edicion`. Para medir videos hace falta Python: `pip install -r requirements.txt`. Y en el sistema, ffmpeg y ffprobe. Si vas a medir caras, bajas el modelo una vez con `medir.py --descargar-modelos`. Los videos de referencia no van a git. A git van las medidas y el texto."

**Se muestra.** La terminal con los dos `cp`. Luego `pip install`. Un resalte sobre `requirements.txt` y sobre la frase de ffmpeg. Nada de cuentas ni de correos.

## 1:40 a 2:30. El formato se pregunta

**Se dice.** "Antes de juntar referencias, RED pregunta el formato. Siempre. Si tú no lo dijiste, no adivina. Las opciones son estas: reel o short vertical, YouTube horizontal, faceless, motion o explicativo, tutorial con pantalla, anuncio, o video largo o clase. De esa respuesta salen el tamaño y la zona segura. Un reel es 1080 por 1920, y no pones nada importante arriba del todo ni abajo del todo, porque ahí la app tapa. Un YouTube horizontal es 1920 por 1080, y esa zona muerta del vertical no aplica. Un anuncio no se supone: se mide la plataforma."

**Se muestra.** La tabla del paso 0, una fila a la vez. Al lado, un marco 9:16 con la franja de arriba y la de abajo marcadas en rojo suave, y un marco 16:9 limpio.

## 2:30 a 5:10. Ejemplo con cara

**Se dice.** "Vamos con un estilo con cara. Le dices: quiero editar como este canal, y son reels. RED pide de 10 a 20 de los mejor editados. Si el canal también sube clips de otros, esos no cuentan. Los bajas, los numeras r01, r02, y mides con el script. El medidor saca cortes, color, texto, cara, sonido. Lo que no puede medir lo dice, no lo inventa. Después se desarma cada video: qué se dice, qué se ve y por qué ahí. La idea, la de Joseph cuando habla del estilo de Arthur Brooks, es esta: si no sabes por qué funciona, la IA solo te ayuda a hacer videos malos más rápido. Se copia la lógica, no la cara de esa persona. La cara y la voz de alguien real no se generan sin su permiso."

**Se muestra.** Una carpeta `investigaciones/` con `mapa.md`, `medidas/` y `reels/r01.md`. Un `medidas.json` con dos o tres números (hex, cortes por minuto, porcentaje de cara). La plantilla de desarme, scrolleada despacio. Un letrero corto: "lógica, no identidad".

## 5:10 a 6:20. Ejemplo faceless

**Se dice.** "El faceless es el mismo método con otra pregunta. No hay cara. Entonces miras qué la reemplaza: voz en off, stock, imagen generada o captura. Cada cuánto cambia la imagen. Si el texto lleva la historia o solo acompaña. La voz la fija el estilo. Si tienes dos faceless, no les mezclas la voz. Y si generas imagen, la pides sin texto: los rótulos los pones tú. La cara de una persona real sigue prohibida igual."

**Se muestra.** El bloque Faceless de la plantilla, lleno con un ejemplo inventado: "voz en off, imagen cada 3 segundos, el texto nombra lo que se ve". Al lado, el formato `faceless.md` del oficio, tres líneas.

## 6:20 a 8:00. El lienzo

**Se dice.** "Aquí está la regla que no se salta. Sin lienzo no hay síntesis. RED te pregunta cuál usas: Figma, Wonder, Paper, Excalidraw o el que ya tengas. Si Claude tiene un conector de esa herramienta, arma la página. Si no, te exporta las capturas y un `lienzo.md` para que la armes a mano. En el lienzo van dos cosas. El tablero: capturas agrupadas por tipo de escena, cada una con su código. Y el formato dibujado en tamaño real, con la zona segura y cada pieza suelta, para que la muevas tú. Te toma media hora. Marcas lo que te gusta. RED sintetiza pesando eso, no el promedio de los videos. Lo aprobado se guarda en la carpeta de estilos del oficio, desde una plantilla. Esa carpeta llega vacía. No trae un estilo de nadie."

**Se muestra.** Un lienzo con dos páginas. Página uno: grupos "gancho", "subtítulo", "b-roll", con miniaturas y códigos `r03-s02`. Página dos: un marco 1080×1920, zona segura en línea punteada, piezas con nombre (renglón grande, renglón chico, caja). Corte a `estilos/PLANTILLA.md` y a la tabla vacía del README.

## 8:00 a 9:40. El oficio y las tres capas

**Se dice.** "El oficio es la otra skill. Tiene tres capas, más unas reglas que van antes de todo. Las reglas son de cualquier video: zona segura, la voz más fuerte que la música, nada de datos privados en pantalla, y no publicas sin tu OK. El oficio, la capa uno, es lo que haría cualquier editor con cualquier estilo. Cortar al final de la palabra con un aire mínimo. Un apoyo visual que entra en la palabra que lo pide y vuelve a quien habla. Una clase de curso no se edita como un YouTube: la clase quiere que la persona aprenda, el YouTube quiere que se quede. El formato, la capa dos, son los pasos de un tipo de video, sin gustos: reel hablado, faceless, motion, tutorial, anuncio, video largo. El estilo, la capa tres, es el tuyo. Letras, colores, escenas. Se carga uno solo. La prueba es simple: si otro editor con otro estilo lo haría igual, es oficio. Si no, es tu gusto y va al estilo."

**Se muestra.** El diagrama del README, y después la tabla de capas de `SKILL.md` del oficio. Un principio abierto, el del corte al final de la palabra, solo el título y la sección "Funciona". La carpeta `formatos/` con los seis archivos.

## 9:40 a 11:00. Editar con un estilo ya creado

**Se dice.** "Cuando el estilo ya está, le dices: edita este reel. El oficio carga las reglas, abre el formato de reel hablado y tu estilo. Mide los brutos con ffprobe, transcribe, arma la tabla de planos y, antes de renderizar, un storyboard de cuadros reales en el mismo lienzo. Tú marcas cada cuadro. Recién ahí se renderiza, porque corregir un cuadro es barato y corregir un render no. Al final verifica: hoja de contactos, silencios, tamaño, audio cerca de -14 LUFS. Si un día le pides que edite y no hay estilo, te lo dice en una línea y te lleva a RED. No usa el estilo de otra persona."

**Se muestra.** El flujo del formato reel, del paso 1 al 9, con el 7 (storyboard) subrayado. Una hoja de contactos ficticia, sin datos personales. El letrero: "sin estilo, se va a RED".

## 11:00 a 11:30. Cierre

**Se dice.** "Resumen. Preguntas el formato. Si no hay estilo, RED mide y tú marcas el lienzo. El estilo queda en la carpeta del oficio. El oficio edita con reglas, formato y ese estilo. Nada se publica sin tu OK, y la cara y la voz de una persona real no se generan sin permiso. El guion de este video está en el repo, por si lo quieres regrabar."

**Se muestra.** Las cuatro frases del resumen, una por una. Al final, las dos carpetas otra vez.
