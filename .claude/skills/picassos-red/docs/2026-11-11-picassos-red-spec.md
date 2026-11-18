# Spec: Picasso's RED (medidor y fidelidad)

Fecha: 2026-11-11. RED significa Reverse Engineer Designs. Un medidor para desarmar cualquier formato audiovisual,
a partir de los videos de Joseph sobre diseño de edición (el estilo de Arthur Brooks, cómo volver un estilo una skill
y 17 tips para editores de video).

## Por qué
La skill ya trae el método (referencias, tablero, desarme, síntesis, motor), pero casi todo se medía a ojo y cada
estudio terminaba con sus propios scripts. No había una tabla común para comparar estilos, ni una forma de decir en
números en qué se aleja un render de su referencia.

## Qué se construye
Un paquete de Python en `scripts/rea/` dentro de esta skill (se importa como `rea`; el nombre del producto es
Picasso's RED). Sirve a cualquier proyecto:

1. `medir.py <carpeta_o_video> --salida <carpeta>`: corre todos los medidores sobre cada video y deja por video un
   `medidas.json` y en la carpeta un `resumen.json` y un `resumen.md` con mediana, p10 y p90 por métrica. Cada métrica
   lleva `origen: "codigo"`. Lo que no se pudo medir sale como `null` con su causa, nunca inventado.
2. `comparar.py <resumen_referencia.json> <medidas_o_resumen_propio.json>`: tabla de diferencias por métrica, con el
   rango de la referencia (p10 a p90), el valor propio y si cae adentro, arriba o abajo. Ordena por lo más lejos. Es el
   ciclo de fidelidad.
3. Un módulo por dimensión, cada uno probado por su lado:

| Dimensión | Métricas mínimas |
|---|---|
| `cortes` | cortes y transiciones (fundido detectable por mezcla de cuadros) por minuto, duración de plano mediana, primeros 3 s |
| `camara` | por plano: quieta, empuje, alejamiento, paneo o giro; magnitud (% de escala, px por segundo a 1080) y curva (sube rápido y frena, lineal); paralaje (capas que se mueven distinto). Con flujo óptico de OpenCV |
| `color` | paleta por plano (k-medias en Lab), reparto 60-30-10 real (peso del primer, segundo y tercer color), saturación media, percentil 1 y 99 de L (negros reales, blancos), temperatura |
| `texto` | texto en pantalla por cuadro con OCR (RapidOCR sobre onnxruntime), su caja, alto en px a 1080, palabras a la vez y tiempo en pantalla |
| `cara` | porcentaje del tiempo con cara humana y su tamaño en el cuadro (OpenCV FaceDetectorYN). En dibujos lo dice como no aplica si no detecta |
| `animacion` | cuadros sostenidos (si anima en uno, en dos o en tres), cuánto del cuadro cambia de un cuadro al siguiente |
| `ilustracion` | grosor del contorno (ancho de los bordes oscuros en px a 1080 y como proporción del alto del elemento), color del trazo, cuánto oscurece la sombra respecto a su base (razón de L en regiones del mismo tono), nitidez del borde |
| `sonido` | LUFS integrado y pico (ffmpeg, filtro ebur128), cuántos efectos por minuto y en qué segundo. Los inicios los detecta el propio paquete: flujo espectral bajo 1,2 kHz, más los saltos de la banda alta sobre 2,5 kHz |
| `guion` | con una transcripción palabra por palabra (`palabras.json` como el de Whisper, opcional): para cada cambio visual (corte, texto que entra, cambio fuerte de cuadro), la palabra más cercana y la distancia en ms. Porcentaje de cambios que caen en una palabra (a menos de 150 ms) |

Desde la raíz del proyecto, con la skill en su sitio:

```
python .claude/skills/picassos-red/scripts/rea/medir.py <carpeta_o_video> --salida <carpeta>
python .claude/skills/picassos-red/scripts/rea/comparar.py <resumen_referencia.json> <medidas_o_resumen_propio.json>
```

## Lo que NO incluye
- No decide qué es un "tipo de escena" ni por qué funciona: eso es juicio y lo hace la IA en el desarme (`plantilla-desarme.md`).
- No sube nada a terceros ni descarga modelos de pago. Los modelos de OCR y cara se bajan una vez a una carpeta fuera de git.
- No modifica el motor de edición del proyecto: solo mide y compara.
- Los videos de referencia nunca entran a git.

## Caminos tristes
- Video que no abre, sin audio o con fps variable: la métrica sale `null` con la causa, el resto sigue.
- AV1 u otro códec que OpenCV no lee: se decodifica con ffmpeg, no hace falta un temporal.
- Sin `palabras.json`: la dimensión `guion` sale `null` con "sin transcripción".
- Video muy largo: se muestrea (parámetro `--fps-muestreo`, por defecto 10) y se dice.

## Pruebas
- Videos sintéticos generados con ffmpeg o numpy en la prueba (un corte conocido, un zoom del 10 %, un texto que entra
  en un cuadro conocido, cuadros repetidos de a dos, una sombra con razón conocida) y la métrica tiene que dar el valor
  esperado con tolerancia.
- `comparar.py` con dos resúmenes de juguete.
- Nada de red en las pruebas. La detección de cara se salta si el modelo YuNet no está descargado.

## La prueba con referencias reales (después de construir)
1. `medir.py` sobre un lote de referencias del estilo (por ejemplo unas 20 piezas cortas) y sobre los renders propios.
2. `comparar.py` de cada render contra el resumen de las referencias.
3. Contrastar con lo medido a mano en `investigaciones/<fecha>-<estilo>/`: dónde coincide el medidor y dónde no.
4. Informe en `investigaciones/<fecha>-red-prueba/`: las 10 diferencias más grandes del render contra la referencia, por dimensión, y qué tan confiable salió cada medidor.

## Terminado cuando
- Las pruebas pasan sin red y cada dimensión tiene al menos una prueba con valor conocido.
- `medir.py` corre sobre el lote de referencias sin caerse y deja su resumen.
- `comparar.py` da la tabla del render contra la referencia.
