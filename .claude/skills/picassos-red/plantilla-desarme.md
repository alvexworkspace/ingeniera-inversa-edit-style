# Plantilla de `reels/rNN.md`

Cada afirmación lleva CONFIRMADO, PROBABLE o NO CONFIRMADO, y su origen (medido, a ojo, fuente).

```
# rNN (archivo, duración, fps)

## Validación
Canal, puntaje atípico, videos del mismo formato a 1,5x o más (de 30 recientes), idea en otros canales. Estado: validado / no validado. Si es no validado, no cuenta en los 10 a 20.

## Guion
Transcripción con tiempos (por frase). Herramienta usada.

## Escenas
| # | Inicio a fin | Tipo | Qué se dice | Qué se ve | Por qué ahí (anuncia, describe, remata...) |

## Tipografía
Fuentes (comparar contra los TTF candidatos; si hay duda, decirlo), pesos, tamaños en px a 1080 de ancho, color en hex,
palabras por línea, cómo se colocan las palabras (cuál grande, cuál chica, dónde). Distancias entre renglones medidas
en la tinta y en em de la letra grande: cuánto queda la base del texto chico sobre la altura de la x, si se encaja en
el hueco de las letras altas o va apilado, la sangría desde el borde de la tinta, y si la palabra grande lleva caja y
cuándo.

## Fondos y texturas
Colores en hex muestreados de los cuadros, tipo y fuerza de la textura (papel, pintura, grano), viñeta y desenfoque de
bordes.

## Material
Pinturas (nombre y autor si se reconocen), ilustraciones, B-roll, fotos, imágenes generadas. De dónde sale cada cosa y
si tiene licencia.

## Animaciones
| # | Escena | Qué se mueve | Qué la dispara (palabra, corte) | Duración en cuadros a 30 fps | Curva (medida o estimada, decir cuál) | Cuánto se pasa (%) | Escalonado entre elementos | Pieza del motor parecida | Hoja |

## Transiciones
Dónde corta en seco y dónde pasa sin cortar, y cómo.

## Cámara
Por plano: quieta, empuje, alejamiento, paneo o giro, cuánto y con qué curva (de `medidas.json`), paralaje entre capas,
y la intención (tensión, revelación, seguir al personaje).

## Puesta en cuadro
Por plano, en 3 a 5 videos:
- Escala del personaje: el ancho de la cabeza y el del cuerpo visible como % del ancho del cuadro. Se dice cuál de los
  dos se midió. Se da la mediana y el rango por tipo de plano, porque cambia de plano a plano.
- Altura de cámara: baja (contrapicado), a la altura de los ojos o alta, y dónde corta el cuadro al personaje.
- Capas de profundidad: si hay primer plano, plano medio y fondo, qué hay en cada uno y si hay profundidad de campo.
- Línea: grosor en px a 1080 de ancho y color en hex, por capa: personaje, utilería en mano, utilería del set,
  arquitectura y fondo. Se anota si adelgaza con la distancia.
- Luz: contraste cálido contra frío (de dónde viene cada una), rim light, fuentes visibles (llamas, faroles) y si la
  luz tiñe al personaje.

## Guion contra pantalla
| Frase | Palabra que dispara | Qué se muestra (literal, metáfora, texto, gráfico, cara) | Antes, en o después de la palabra (ms, de `medidas.json`) | Cuánto dura |

## Diseño
Composición (foco, tercios), equilibrio (horizontal, vertical, diagonal), contraste (color, tamaño, textura, forma),
reparto 60-30-10 medido y de dónde sale el acento, forma de las esquinas.

## Ilustración (solo si hay dibujo)
Contorno (grosor y color medidos, de qué lado engorda), sombra (razón de oscuridad medida, color, borde duro o suave),
dirección de la luz, proporciones del personaje y nivel de acabado por capa. Pasos extra en `referencia/ilustracion.md`.

## Sonido
Música (tipo, nivel), cada efecto con su evento y su cuadro, silencios. Medido con `scripts/rea/` (LUFS, picos e inicios). Nunca se sube el audio a un tercero para que un modelo lo critique.

## Faceless (solo si no hay cara)
Qué ocupa el lugar de la cara, cada cuántos segundos cambia la imagen, cómo se mueve una imagen fija (acercamiento,
paralaje, nada), cuántas palabras hay en pantalla a la vez y si el texto lleva la historia o la acompaña.

## Ritmo
% del tiempo en la cara (o en la voz en off) contra gráficos, cambios de escena por minuto, qué pasa en los primeros 3 s.

## Lo más copiable
Tres cosas de este video que el estilo debería tomar, y qué choca con la marca del dueño.
```
