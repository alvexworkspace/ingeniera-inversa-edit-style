# Reglas de todo video

Valen para cualquier video de este proyecto, antes de planear, generar, editar o renderizar. El detalle de cada formato está en `formatos/`. El gusto (letras, colores, escenas) está en el estilo, no aquí.

## Formato y zonas seguras
No se fija una resolución sin medir el bruto con `ffprobe`. El formato se pregunta si nadie lo dijo.

| Formato | Tamaño de trabajo | Zona segura |
|---|---|---|
| Reel o short vertical 9:16 | 1080×1920 | Nada importante en los 270 px de arriba ni por debajo de y 1500. Sin tarjetas pegadas a los lados: no hay espacio. |
| YouTube 16:9 | 1920×1080 | La zona muerta del vertical no aplica. El texto importante no se pega a los bordes. |
| Faceless | El del lugar donde se publica. Si es vertical, 1080×1920 | La del vertical, si es 9:16 |
| Motion o explicativo | El del lugar donde se publica | La de ese tamaño |
| Tutorial con pantalla | El del lugar donde se publica | El texto de la interfaz no baja de 36 px en el tamaño final |
| Anuncio | El de la plataforma, medido antes de editar | No se supone. Se consulta la ficha de esa plataforma y se dibuja en el lienzo |
| Video largo o clase | El que dé `ffprobe`. Un curso y un YouTube suelen ser 16:9 | La de YouTube si es horizontal; la del vertical si el bruto es vertical |

En el lienzo, el formato se dibuja a este tamaño, con la zona segura marcada.

## Movimiento
Ningún cambio de escala ni entrada en seco. La curva arranca rápido y frena largo. Una cosa a la vez.

## Sonido
La voz manda. La música va unos 20 dB bajo la voz y no entra en el primer segundo, salvo que el estilo diga otra cosa. El máster queda cerca de -14 LUFS con pico de -1 dB. Un golpe fuerte por idea; el resto, más bajo. El silencio corto antes del golpe es parte del golpe.

Si el proyecto tiene una biblioteca de efectos, se usa antes de generar un sonido nuevo.

## Imagen generada
Se pide sin texto: los rótulos, las cifras y la marca los pone el editor. Cada generación cuesta: se dice el costo y se espera el OK del dueño antes de correrla. Nunca se genera la cara ni la voz de una persona real sin su permiso.

## Assets y licencias
Todo proyecto con material de terceros o generado lleva un `assets-licencias.md` en su carpeta, con una tabla: asset, origen (link o herramienta), licencia, autor si la pide (atribución) y en qué plano se usa.
- Lo que no tiene una licencia clara no entra en un video que se venda o se publique.
- Lo generado con IA anota la herramienta y su plan, porque los derechos comerciales dependen del plan.
- Nada del creador estudiado entra en el render.

## Herramienta
Se usa el motor que ya tenga el proyecto (código, editor de línea de tiempo o el que diga el estilo). Esta regla no impone un programa ni una licencia.

**GPU en la nube.** Se usa solo con el OK del dueño para ese trabajo. Antes de rentar, se dice cuánto cuesta la hora y cuánto se calcula en total.
- Al terminar, la instancia **se destruye**, no se detiene: una instancia detenida sigue cobrando el disco.
- Se **verifica** que ya no existe (por ejemplo, con `vastai show instances` vacío).
- Se **reporta** el costo real (horas por precio, o lo que dice la factura) junto con la entrega.
- Si algo falla a mitad, la instancia se destruye igual antes de seguir probando.

## Pantalla limpia
En ningún cuadro se ve un dato de otra persona, un correo, un chat privado ni una ruta del computador. La grabación de pantalla captura una sola ventana limpia.

## Comparar con la referencia
Cada etapa (look, plano, video) se muestra al lado del original, en el mismo cuadro y a la misma escala. Esa comparación es **interna**: no se publica, no se vende, no entra en un paquete ni en un portafolio. Los cuadros del original no se usan en ningún render. Se nombra el archivo con `INTERNO` (por ejemplo, `lado-a-lado-INTERNO.jpg`) y no va a git.

## Verificación antes de decir listo
- Hoja de contactos del render.
- `silencedetect`: no quedaron huecos largos ni palabras mordidas, salvo una pausa deliberada.
- La resolución es la del formato, medida, no supuesta.
- El audio está en el nivel de arriba.
- Nada importante cae en la zona muerta.
- El dueño dio el OK en el chat antes de publicar.

## Cuando el dueño corrige
La corrección va como regla con fecha al archivo que la cubre (el estilo, o `reglas.md` si vale para todo video y no está en ningún otro lado). No se deja solo en el chat.

## Terminado cuando
- Nada importante cae en la zona muerta del formato, y la resolución se midió con `ffprobe`.
- Hay hoja de contactos y `silencedetect` del render.
- La música va bajo la voz y el audio final queda cerca de -14 LUFS con pico de -1 dB.
- Cada generación con IA tuvo su costo dicho y el OK del dueño antes de correr.
- No se ve ningún dato privado en pantalla.
- Nada se publicó sin el OK del dueño.
- Ninguna comparación con el original salió del uso interno.
- Cada asset del render está en `assets-licencias.md` con su licencia.
- Si hubo GPU en la nube, la instancia quedó destruida y verificada, y el costo se reportó.
