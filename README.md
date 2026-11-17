# Picasso's RED

RED significa **Reverse Engineer Designs**: ingeniería inversa de un diseño audiovisual.

Esta skill de Claude Code desarma un estilo (edición con cara, motion, formato, faceless, video largo o ilustración) a partir de sus referencias y lo vuelve medidas, un tablero y piezas que se pueden repetir. Primero se entiende por qué el estilo funciona, después se miden los números y al final se edita. Lo que se copia es la lógica (cuándo entra cada escena, curvas, tiempos, jerarquía), no la identidad de otro creador.

El paquete de medición sigue en `scripts/rea/` y se importa como `rea`. Renombrarlo a `red` rompería los `import rea` de los módulos y de los tests. RED es el nombre del método; `rea` es el nombre del paquete de Python. La variable de entorno de los modelos de cara también se llama `REA_MODELOS`, y la caché queda en `~/.cache/rea/modelos` (en Windows, `%LOCALAPPDATA%/rea/modelos`).

## Instalarla en un proyecto de Claude Code

En este repo la skill ya está en su sitio. Para usarla en otro proyecto, copia la carpeta dentro de `.claude/skills/`:

```bash
mkdir -p .claude/skills
cp -a .claude/skills/picassos-red /ruta/del/proyecto/.claude/skills/
```

Queda en `.claude/skills/picassos-red/`. Ahí viven el método (`SKILL.md`), la plantilla de desarme, las referencias, la spec y los scripts. En Claude Code se invoca con frases como «quiero editar como X» o «desarma este estilo».

Instala las dependencias de Python en el proyecto donde vayas a medir:

```bash
pip install -r requirements.txt
```

En el sistema hacen falta `ffmpeg` y `ffprobe` en el `PATH`. El medidor decodifica con ffmpeg (también AV1) y el volumen lo saca el filtro `ebur128`.

| Paquete | Para qué |
|---|---|
| `numpy`, `scipy` | números, flujo espectral, curvas |
| `opencv-python-headless` | imagen, flujo óptico, detección de cara (YuNet) |
| `scikit-image` | esqueleto del contorno en ilustración |
| `rapidocr-onnxruntime` | texto en pantalla (OCR). Si falta, esas métricas salen nulas con su causa |
| `pytest` | la suite de `scripts/rea/tests` |

La primera vez que quieras medir caras, baja el modelo YuNet (una vez, fuera de git):

```bash
python .claude/skills/picassos-red/scripts/rea/medir.py --descargar-modelos
```

## Ejemplo de uso

En el proyecto, con la skill ya copiada:

- «Quiero editar como este canal» y una carpeta o una lista de links de 10 a 20 videos bien editados.
- «Desarma este estilo» sobre esa carpeta.

La skill reúne las referencias, las numera y mide:

```bash
python .claude/skills/picassos-red/scripts/rea/medir.py ./referencias \
  --salida investigaciones/2026-11-17-estilo/medidas
```

Deja un `medidas.json` por video y un `resumen` con mediana, p10 y p90. El estudio completo (mapa, desarmes, capturas, síntesis) va en `investigaciones/<fecha>-<estilo>/`. Cuando haya un render propio, se compara contra ese resumen:

```bash
python .claude/skills/picassos-red/scripts/rea/comparar.py \
  investigaciones/2026-11-17-estilo/medidas/resumen.json \
  investigaciones/2026-11-17-estilo/render/medidas.json
```

Los videos de referencia no se commitean: a git van el texto y las medidas. Nunca se genera la cara ni la voz de una persona real sin su permiso.

## Qué hay en la carpeta

- `SKILL.md`: el método, paso a paso.
- `plantilla-desarme.md`: la ficha de cada video.
- `referencia/dimensiones.md`: las siete dimensiones y el vocabulario de diseño.
- `referencia/ilustracion.md`: el modo de dibujo y animación.
- `docs/2026-11-11-picassos-red-spec.md`: la spec del medidor.
- `scripts/rea/`: `medir.py`, `comparar.py` y un módulo por dimensión, con tests.

## Tests

Desde la raíz de este repo:

```bash
pip install -r requirements.txt
PYTHONPATH=.claude/skills/picassos-red/scripts pytest .claude/skills/picassos-red/scripts/rea/tests
```

Los tests arman videos sintéticos con ffmpeg y no usan la red. Dos pruebas de cara se saltan si YuNet no está descargado; el resto de la dimensión cara (métrica nula cuando falta el modelo, y la verificación del hash al bajarlo) sí corre.

## Créditos

El método se inspira en Joseph, en su video sobre el estilo de edición de Arthur Brooks y en su forma de volver un estilo una skill de diseño: si no sabes por qué un estilo funciona, la IA solo ayuda a hacer videos malos más rápido. El vocabulario de composición, equilibrio, contraste, color 60-30-10 y letra sale de sus tips de diseño para editores.
