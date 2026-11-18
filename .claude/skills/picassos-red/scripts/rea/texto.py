"""Dimensión texto: el texto en pantalla por cuadro con OCR (RapidOCR sobre onnxruntime).

El OCR lee a 4 cuadros por segundo, así que el inicio de cada texto tiene un error de hasta 250 ms. `refinar_inicios`
lo lleva al cuadro exacto: mira la diferencia entre cuadros dentro de la caja del texto a 30 cuadros por segundo y
toma el último gran cambio de los 270 ms previos al inicio leído (`inicio_fino`). Solo si ese cambio es un escalón: la
caja cambia de golpe y después se queda estable unos cuadros, y antes no cambiaba tanto. Con el fondo en movimiento la
caja cambia siempre, no hay escalón y el inicio queda en None (se conserva el inicio del OCR, que es el grueso).
Por cuadro saca cada texto con su caja. De ahí salen el alto en px a 1080, las palabras a la vez y cuánto tiempo
está en pantalla cada texto (un mismo texto en cuadros seguidos es un solo tramo).
"""
import re

import numpy as np

from rea import comun

METRICAS = ("pct_tiempo_con_texto", "alto_texto_px_1080_mediano", "palabras_a_la_vez_mediano", "palabras_a_la_vez_max",
            "tiempo_en_pantalla_mediano_s", "textos_nuevos_por_min")

FPS_OCR = 4.0                # cuadros por segundo que lee el OCR
ALTO_OCR = 720                # alto (px) de los cuadros que lee el OCR (y lado mayor máximo que usa)
ALTO_REFERENCIA = 1080        # los altos de texto se dan como si el video fuera de 1080 de alto
CONFIANZA_MIN = 0.5            # confianza mínima del OCR para dar por bueno un texto
HUECO_MAX = 1          # cuadros seguidos sin ver un texto antes de dar el tramo por terminado
FPS_FINO = 30.0        # velocidad a la que se afina el inicio de un texto
ALTO_FINO = 360        # alto de los cuadros de esa lectura
ANTES_S, DESPUES_S = 0.27, 0.03    # ventana donde buscar el cambio: el OCR lo vio a lo sumo 250 ms después de que entró
DIF_FINA_MIN = 6.0     # diferencia media (de 255) dentro de la caja desde la que algo "entró"
ESTABLE_S = 0.15       # tiempo después del cambio en que la caja debe quedar estable
FRACCION_ESTABLE = 0.5  # "estable": la diferencia media de esos cuadros es menos de esta fracción del cambio
PREVIO_VECES = 2.5      # y el cambio debe superar tantas veces la diferencia mediana de los cuadros previos de la ventana
FRACCION_PICO = 0.5    # entre varios cambios en la ventana, el último que llega a esta fracción del mayor
IGUAL_MAX = 0.5        # diferencia media (de 255) bajo la cual un cuadro se da por igual al anterior y no se vuelve a leer


def crear_ocr():
    """RapidOCR, o None con la causa si no está instalado. Devuelve (ocr, causa)."""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return None, "rapidocr-onnxruntime no está instalado"
    # límite por el lado mayor: con el valor por defecto un cuadro vertical se agranda al doble y tarda tres veces más
    return RapidOCR(det_limit_type="max", det_limit_side_len=ALTO_OCR), None


def _normal(texto):
    return re.sub(r"[^0-9a-záéíóúñü]", "", texto.casefold())


def leer_cuadro(ocr, cuadro):
    """Lista de {texto, caja (x0, y0, x1, y1), alto, palabras} del cuadro, en px del cuadro."""
    resultado, _ = ocr(cuadro, use_cls=False)
    textos = []
    for poligono, texto, confianza in resultado or []:
        if float(confianza) < CONFIANZA_MIN or not _normal(texto):
            continue
        pts = np.array(poligono, np.float32)
        x0, y0 = pts.min(0)
        x1, y1 = pts.max(0)
        textos.append({"texto": texto, "caja": [float(x0), float(y0), float(x1), float(y1)], "alto": float(y1 - y0),
                       "palabras": len(texto.split())})
    return textos


def tramos(lecturas, fps):
    """Une los textos iguales de cuadros seguidos. `lecturas` es una lista (un item por cuadro) de listas de textos.
    Devuelve [{texto, inicio, fin, alto, caja}] con inicio y fin en segundos (fin es donde termina el último cuadro)."""
    abiertos, cerrados = {}, []
    for i, textos in enumerate(lecturas):
        vistos = set()
        for t in textos:
            clave = _normal(t["texto"])
            vistos.add(clave)
            if clave in abiertos:
                abiertos[clave].update(ultimo=i, altos=abiertos[clave]["altos"] + [t["alto"]])
            else:
                abiertos[clave] = {"texto": t["texto"], "primero": i, "ultimo": i, "altos": [t["alto"]], "caja": t["caja"]}
        for clave in [c for c, a in abiertos.items() if c not in vistos and i - a["ultimo"] > HUECO_MAX]:
            cerrados.append(abiertos.pop(clave))
    cerrados += abiertos.values()
    salida = [{"texto": a["texto"], "inicio": round(a["primero"] / fps, 3), "fin": round((a["ultimo"] + 1) / fps, 3),
               "alto": float(np.median(a["altos"])), "caja": a["caja"]} for a in cerrados]
    return sorted(salida, key=lambda t: t["inicio"])


def resumir(lecturas, lista, fps, dur, escala):
    """Las métricas a partir de las lecturas por cuadro, los tramos y la escala px_del_cuadro a px a 1080."""
    con_texto = [sum(t["palabras"] for t in textos) for textos in lecturas if textos]
    altos = [t["alto"] * escala for textos in lecturas for t in textos]
    metricas = {
        "pct_tiempo_con_texto": comun.ok(comun.porcentaje(len(con_texto), len(lecturas))),
        "alto_texto_px_1080_mediano": comun.o_nula(comun.mediana(altos), "no se vio texto en pantalla"),
        "palabras_a_la_vez_mediano": comun.o_nula(comun.mediana(con_texto), "no se vio texto en pantalla"),
        "palabras_a_la_vez_max": comun.o_nula(max(con_texto) if con_texto else None, "no se vio texto en pantalla"),
        "tiempo_en_pantalla_mediano_s": comun.o_nula(comun.mediana([t["fin"] - t["inicio"] for t in lista]),
                                                     "no se vio texto en pantalla"),
        "textos_nuevos_por_min": comun.ok(len(lista) / (dur / 60)),
    }
    detalle = {"fps_ocr": fps, "alto_cuadro": round(ALTO_REFERENCIA / escala), "tramos": [{**t, "alto_px_1080": round(t["alto"] * escala, 1)} for t in lista]}
    return {"metricas": metricas, "detalle": detalle}


def medir_cuadros(cuadros, fps, dur, escala, ocr):
    """Dimensión sobre un iterable de cuadros BGR a `fps`. `escala` pasa px del cuadro a px a 1080 de alto."""
    lecturas, anterior, previa = [], None, []
    for c in cuadros:
        gris = c.mean(2)
        if anterior is not None and np.abs(gris - anterior).mean() < IGUAL_MAX:
            lecturas.append(previa)
            continue
        previa = leer_cuadro(ocr, c)
        anterior = gris
        lecturas.append(previa)
    if not lecturas:
        return comun.todas_nulas(METRICAS, "sin cuadros")
    return resumir(lecturas, tramos(lecturas, fps), fps, dur, escala)


def _caja_en(caja, alto_cuadro, forma):
    """Rebanadas (filas, columnas) de la caja del OCR en un cuadro de forma `forma`, o None si queda vacía."""
    f = forma[0] / alto_cuadro
    x0, y0, x1, y1 = (max(0, int(v * f)) for v in caja)
    y1, x1 = min(forma[0], y1 + 1), min(forma[1], x1 + 1)
    return (slice(y0, y1), slice(x0, x1)) if y1 > y0 and x1 > x0 else None


def _escalon(serie, inicio_ocr):
    """El segundo del último gran cambio de `serie` (pares (segundo, diferencia media en la caja)) en los ANTES_S previos al
    inicio del OCR, si es un escalón: la caja queda estable después y antes cambiaba mucho menos. Si no, None."""
    en_ventana = [(i, t, d) for i, (t, d) in enumerate(serie) if t <= inicio_ocr + DESPUES_S]
    if not en_ventana:
        return None
    mayor = max(d for _, _, d in en_ventana)
    if mayor < DIF_FINA_MIN:
        return None
    k, t, d = [x for x in en_ventana if x[2] >= FRACCION_PICO * mayor][-1]
    despues = [dd for _, dd in serie[k + 1:k + 4]]
    antes = [dd for _, dd in serie[:k]]
    if despues and float(np.mean(despues)) >= FRACCION_ESTABLE * d:
        return None
    if len(antes) >= 3 and d < PREVIO_VECES * float(np.median(antes)):
        return None
    return round(t, 3)


def refinar_inicios(cuadros, fps, lista, alto_cuadro):
    """Agrega `inicio_fino` (segundos) a cada tramo de `lista` mirando cuadros BGR a `fps`. Es None si en la caja no hubo un
    cambio claro. `alto_cuadro` es el alto en px de los cuadros donde el OCR midió las cajas."""
    series = [[] for _ in lista]
    anterior = None
    ventanas = [(t["inicio"] - ANTES_S, t["inicio"] + DESPUES_S + ESTABLE_S) for t in lista]
    for i, c in enumerate(cuadros):
        gris = c.mean(2)
        t = i / fps
        if anterior is not None:
            for k, (a, b) in enumerate(ventanas):
                if a <= t <= b:
                    zona = _caja_en(lista[k]["caja"], alto_cuadro, gris.shape)
                    if zona is not None:
                        series[k].append((t, float(np.abs(gris[zona] - anterior[zona]).mean())))
        anterior = gris
    for tramo, serie in zip(lista, series):
        tramo["inicio_fino"] = _escalon(serie, tramo["inicio"])
    return lista


def medir(video, fps_ocr=FPS_OCR):
    ocr, causa = crear_ocr()
    if ocr is None:
        return comun.todas_nulas(METRICAS, causa)
    fps = min(fps_ocr, video.info["fps"])
    alto = video.tam(ALTO_OCR)[1]
    cuadros = video.iterar(fps, ALTO_OCR, max_cuadros=int(video.info["dur"] * fps) + 1)
    r = medir_cuadros(cuadros, fps, video.info["dur"], ALTO_REFERENCIA / alto, ocr)
    tramos_texto = r["detalle"].get("tramos")
    if tramos_texto:
        fps_fino = min(FPS_FINO, video.info["fps"])
        refinar_inicios(video.iterar(fps_fino, ALTO_FINO), fps_fino, tramos_texto, alto)
        r["detalle"]["inicios_refinados"] = sum(t["inicio_fino"] is not None for t in tramos_texto)
    return r
