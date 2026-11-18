---
id: un-director-por-chiste-con-contrato-y-linea-de-tiempo-bloqueada
principio: Con la voz y los cortes ya bloqueados, cada chiste que no funciona se le entrega a un agente con contexto fresco y archivo propio, bajo un contrato de dueños y entregas, en vez de que un solo integrador retoque todo
capa: oficio
fuentes: make animated shorts with claude code full workflow
fecha: 2026-11-05
---
## Qué decide quien lo enseña

Decide repartir por unidad cómica y no por especialidad cuando el puntaje se estanca. Antes de repartir, la línea de tiempo (voz y límites de plano) se bloquea. Un documento de contrato dice quién es dueño de qué archivo, qué entrega cada agente y dónde se piden cambios. Cada director escribe solo su archivo, vuelve a renderizar solo su rango, mira su tira de cuadros dos veces y reporta el cuadro exacto del impacto.

## Por qué

Un integrador con todo el contexto repitió los mismos cinco fallos dos rondas seguidas mientras su contexto pasaba de 450 mil tokens. Con un director por chiste y contexto nuevo, el puntaje salió del estancamiento. Sin contrato, dos agentes pisan el mismo archivo: en la fuente un archivo temporal compartido se corrompió y un proceso se cayó.

## Funciona

- Bloquear voz y límites de plano antes del trabajo en paralelo, y dar a cada corte un dueño.
- Referirse a los planos por rango de cuadros, o congelar los ids.
- Si el mismo defecto aparece en varios chistes, arreglarlo una vez en la base (el rig) y no en cada plano.

## No funciona

- Agentes en paralelo sobre el mismo archivo o sobre una línea de tiempo que aún cambia.
- Modificar un estado compartido (un punto de anclaje, un color de paleta usado por varios materiales) sin congelarlo antes.

## Cuándo no aplica

- En una pieza corta que cabe en una sola cabeza, donde coordinar agentes cuesta más que hacerla.
- Si solo falla un chiste, basta un director: el contrato es para varios en paralelo.
