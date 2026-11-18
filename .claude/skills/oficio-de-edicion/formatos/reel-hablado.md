# Formato: reel hablado a cámara

Los pasos del reel o short vertical, con alguien a cámara. El gusto vive en el estilo. Aquí está el orden. Tamaño de trabajo: 1080×1920. Zona segura: `reglas.md`.

## Qué manda (en este orden)
1. La identidad del dueño, si el proyecto la tiene.
2. El estilo (`estilos/`). Donde las reglas del estilo chocan entre sí, manda la corrección más reciente.
3. El manual del motor del estilo, si trae uno: cómo se escribe la lista de escenas y qué hace cada pieza.
4. La guía de sonido del estilo, si la trae.
5. Las notas de reels anteriores del proyecto, si las tiene: lo que ya se decidió y no se vuelve a preguntar.

## Los pasos
1. **Bajar y medir.** Los brutos quedan en una carpeta del proyecto que no sube a git. `ffprobe` de cada uno: duración, fps, rotación y HDR. Nunca se fija una resolución sin medirla.
2. **Transcribir.** Palabra por palabra. El estilo dice con qué herramienta.
3. **Inventario.** Qué bruto es cara y cuál es pantalla, la mejor toma de cada frase y si se ve algún dato privado.
4. **Escenas.** Cada frase recorre la tabla de escenas del estilo, y gana la primera regla que se cumple. Topes: nunca más de 5 s seguidos fuera de la cara ni más de 10 s sin que pase nada.
5. **La tabla de planos.** Las tomas, el orden, la escena de cada tramo y la palabra clave de cada frase. Sirve para armar la lista de escenas y no reemplaza al storyboard.
6. **La lista de escenas.** Se arma en el formato del motor del estilo. Antes de renderizar, el motor la valida en seco si sabe hacerlo.
7. **El storyboard. Es la puerta de control** (ver `SKILL.md`). Un cuadro real de cada toma, con sus subtítulos y la zona segura, en el lienzo. El dueño lo revisa y se corrige hasta que lo apruebe. Sin su OK no hay render.
8. **Render** con el motor del estilo.
9. **Verificar antes de decir listo.** Hoja de contactos, `silencedetect`, 1080×1920, audio cerca de -14 LUFS con pico de -1 dB, ningún dato privado y nada congelado sin razón.
10. **Aprender.** Cada corrección del dueño va como regla a su estilo, con fecha, y lo decidido en este video a una nota del proyecto.

## Texto de publicación
El texto que acompaña al video pasa por el flujo de escritura del proyecto. Se publica solo con el OK del dueño.

## Lo que más se equivoca (mirarlo en cada cuadro)
- **La palabra clave** es la que se dijo, no la del guion.
- **La interfaz del reel:** nada importante arriba de y 270 ni de y 1500 para abajo.
- **La cara de quien habla** no se tapa. Nunca se dibuja ni se genera la cara ni la voz de una persona real sin su permiso.
- **Una frase no cruza un cambio de escena:** se parte en el segundo del corte.

## Terminado cuando (además del de la skill)
- El dueño aprobó el storyboard (un cuadro real por toma) antes del render.
- El video pasó la verificación del paso 9.
- Ningún cuadro muestra un dato privado y nada importante cae arriba de y 270 ni de y 1500 para abajo.
- Las correcciones del dueño quedaron en su estilo.
- Nada se publicó sin el OK del dueño.
