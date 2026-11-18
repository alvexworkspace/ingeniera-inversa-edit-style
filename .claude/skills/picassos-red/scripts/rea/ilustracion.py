"""Dimensión ilustración: contorno, color del trazo, sombra y nitidez del borde.

Se mide sobre unos cuadros sueltos a la mayor resolución (hasta 1080 de alto) y todo se da en px a 1080. No se toman
cuadros dentro de una transición (un fundido mezcla dos imágenes y parece un degradado con dos niveles). Las cajas donde
la dimensión texto encontró letras se tapan antes de medir, para que los subtítulos no cuenten como trazo ni como borde.
  - grosor del contorno: área de los trazos oscuros y delgados dividida entre el largo de su esqueleto, en px y como
    proporción del alto del elemento más grande. Un componente oscuro que toca 3 o más bordes del cuadro (un fondo
    negro, barras) no es un trazo y se descarta;
  - color del trazo: el color mediano de esos píxeles;
  - sombra: en cada región conectada de un mismo tono (erosionada 2 px) se separan dos niveles de luz (Otsu) y se
    acepta solo si es bimodal: menos del 15 % de los puntos entre los dos niveles y un salto marcado, con cada nivel
    liso (poca variación fina) y en pocos pedazos conectados: una textura (ladrillos, tela) alterna los dos niveles
    en muchos pedazos y no es una sombra. La razón es la luz
    del nivel oscuro entre la del claro. Un degradado, o dos objetos del mismo tono separados, no son una sombra plana y
    la métrica sale nula con "degradado, no sombra plana";
  - nitidez: ancho de la transición del borde en px (contraste local dividido entre la pendiente). Más bajo, más nítido.
"""
import cv2
import numpy as np
from scipy import ndimage
from skimage.morphology import skeletonize

from rea import comun
from rea.color import a_lab, hex_de_lab

METRICAS = ("grosor_contorno_px_1080", "grosor_contorno_prop_elemento", "color_trazo", "sombra_razon_luz",
            "borde_transicion_px_1080")

ALTO_REFERENCIA = 1080        # los px se dan como si el cuadro fuera de 1080 de alto
OSCURO_MAX = 30.0         # L (0 a 100) bajo la cual un píxel cuenta como trazo oscuro
TRAZO_MAX_PROP = 0.04     # un trazo más ancho que esto (del alto del cuadro) es un relleno, no un contorno
TRAZO_MIN_PUNTOS = 30     # puntos de esqueleto mínimos para fiarse del grosor
BORDES_MAX = 3            # un componente oscuro que toca tantos bordes del cuadro no es un trazo
DIF_FONDO = 15.0          # distancia Lab al fondo desde la que un píxel es parte de un elemento
CROMA_MIN = 10.0              # croma Lab bajo el cual un píxel es gris y no tiene tono para buscar sombra
CUADROS_MAX = 12              # cuadros sueltos que se miden por video
BINES_TONO = 12              # franjas de tono (30 grados cada una) en que se agrupan las regiones
REGION_MIN_PROP = 0.005   # área mínima de una región de tono para buscar sombra (fracción del cuadro)
EROSION_PX = 5            # núcleo de 5x5: quita 2 px de cada lado
ENTRE_MAX = 0.15          # fracción máxima de puntos entre los dos niveles de luz
PEDAZOS_MAX = 4           # pedazos conectados (de 20 puntos o más) que puede tener cada nivel de una sombra
PEDAZO_MIN_PUNTOS = 20         # puntos mínimos para que un pedazo conectado cuente al juzgar si es textura
NIVEL_STD_MAX = 4.0       # variación (desviación de L) máxima dentro de un nivel para que sea liso
TRANSICION_MARGEN_S = 0.05     # margen (s) a cada lado de una transición donde tampoco se toman cuadros
SALTO_MIN = 5.0           # salto mínimo de luz (L de 0 a 100) entre los dos niveles
NIVEL_MIN = 0.05          # fracción mínima de puntos en cada nivel
SIN_REGIONES = "no se vieron regiones de color"
NO_SOMBRA = "degradado, no sombra plana"
SIN_TRAZO = "no se vio un trazo oscuro y delgado"


def _fondo(lab):
    """Color Lab del fondo: la mediana del borde del cuadro."""
    borde = np.concatenate([lab[:4].reshape(-1, 3), lab[-4:].reshape(-1, 3), lab[:, :4].reshape(-1, 3), lab[:, -4:].reshape(-1, 3)])
    return np.median(borde, axis=0)


def mascara_de_cajas(forma, cajas, margen=4):
    """Máscara bool (alto, ancho) con True dentro de las cajas (x0, y0, x1, y1), ensanchadas `margen` px."""
    m = np.zeros(forma, bool)
    for x0, y0, x1, y1 in cajas or []:
        m[max(0, int(y0) - margen):int(y1) + margen + 1, max(0, int(x0) - margen):int(x1) + margen + 1] = True
    return m


def alto_del_elemento(lab, fondo):
    """Alto en px del bloque conectado más grande que se distingue del fondo, o None."""
    mascara = (np.linalg.norm(lab - fondo, axis=2) > DIF_FONDO).astype(np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mascara)
    if n < 2:
        return None
    mayor = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return int(stats[mayor, cv2.CC_STAT_HEIGHT])


def _quitar_componentes_de_borde(mascara):
    """Quita de la máscara los componentes que tocan BORDES_MAX o más bordes del cuadro."""
    n, etiquetas = cv2.connectedComponents(mascara.astype(np.uint8), connectivity=8)
    salida = mascara.copy()
    for c in range(1, n):
        m = etiquetas == c
        if int(m[0].any()) + int(m[-1].any()) + int(m[:, 0].any()) + int(m[:, -1].any()) >= BORDES_MAX:
            salida[m] = False
    return salida


def largo_del_esqueleto(e):
    """Largo de un esqueleto de 1 px: pasos ortogonales de 1 y diagonales de raíz de 2."""
    horizontal = (e[:, :-1] & e[:, 1:]).sum()
    vertical = (e[:-1] & e[1:]).sum()
    diagonal = (e[:-1, :-1] & e[1:, 1:]).sum() + (e[:-1, 1:] & e[1:, :-1]).sum()
    return float(horizontal + vertical + np.sqrt(2) * diagonal)


def trazo(bgr, lab, fondo, fuera=None):
    """(grosor_px, color_hex) del trazo oscuro y delgado, o (None, None). `fuera` es una máscara de lo que no se mide."""
    umbral = min(OSCURO_MAX, 0.6 * float(fondo[0]))
    mascara = lab[..., 0] < umbral
    if fuera is not None:
        mascara &= ~fuera
    mascara = _quitar_componentes_de_borde(mascara)
    if mascara.sum() < TRAZO_MIN_PUNTOS:
        return None, None
    esqueleto = skeletonize(mascara)
    ancho_en_esqueleto = np.where(esqueleto, 2 * ndimage.distance_transform_edt(mascara), 0)
    delgado_e = esqueleto & (ancho_en_esqueleto <= TRAZO_MAX_PROP * bgr.shape[0])
    if delgado_e.sum() < TRAZO_MIN_PUNTOS:
        return None, None
    _, indices = ndimage.distance_transform_edt(~esqueleto, return_indices=True)
    # cada punto del trazo hereda el ancho de su esqueleto más cercano: así se queda con el área de lo delgado
    ancho_cercano = ancho_en_esqueleto[indices[0], indices[1]]
    area = (mascara & (ancho_cercano <= TRAZO_MAX_PROP * bgr.shape[0])).sum()
    return float(area / largo_del_esqueleto(delgado_e)), hex_de_lab(np.median(lab[delgado_e], axis=0))


def _pedazos(mascara):
    """Cuántos pedazos conectados de PEDAZO_MIN_PUNTOS puntos o más tiene la máscara."""
    n, _, stats, _ = cv2.connectedComponentsWithStats(mascara.astype(np.uint8), connectivity=4)
    return int((stats[1:, cv2.CC_STAT_AREA] >= PEDAZO_MIN_PUNTOS).sum())


def razon_bimodal(luz, region):
    """Razón (nivel oscuro / nivel claro) de la luz `luz` (L de 0 a 100, 2D) dentro de la máscara `region` si es una sombra plana:
    bimodal, con niveles lisos y en pocos pedazos. Si no, None."""
    luces = luz[region]
    l8 = np.clip(luces * 2.55, 0, 255).astype(np.uint8).reshape(-1, 1)
    corte, _ = cv2.threshold(l8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    es_bajo = l8.ravel() <= corte
    bajos, altos = luces[es_bajo], luces[~es_bajo]
    if min(len(bajos), len(altos)) < NIVEL_MIN * len(luces):
        return None
    m0, m1 = float(bajos.mean()), float(altos.mean())
    salto = m1 - m0
    if salto < SALTO_MIN or m1 <= 0:
        return None
    entre = ((luces > m0 + 0.25 * salto) & (luces < m1 - 0.25 * salto)).mean()
    if entre >= ENTRE_MAX or max(float(bajos.std()), float(altos.std())) > NIVEL_STD_MAX:
        return None
    clase_baja = np.zeros(luz.shape, bool)
    clase_baja[region] = es_bajo
    if max(_pedazos(clase_baja), _pedazos(region & ~clase_baja)) > PEDAZOS_MAX:
        return None
    return m0 / m1


def razon_de_sombra(lab, excluir):
    """(razon, causa): mediana de la razón de luz de las regiones de un tono que tienen sombra plana. `excluir` es una
    máscara de lo que no cuenta (trazo oscuro, texto)."""
    a, b, luz = lab[..., 1], lab[..., 2], lab[..., 0]
    valido = (np.hypot(a, b) > CROMA_MIN) & (luz >= OSCURO_MAX) & ~excluir
    tono = ((np.degrees(np.arctan2(b, a)) % 360) / (360 / BINES_TONO)).astype(int) % BINES_TONO
    minimo = REGION_MIN_PROP * luz.size
    nucleo = np.ones((EROSION_PX, EROSION_PX), np.uint8)
    razones, regiones = [], 0
    for k in range(BINES_TONO):
        n, etiquetas, stats, _ = cv2.connectedComponentsWithStats((valido & (tono == k)).astype(np.uint8), connectivity=4)
        for c in range(1, n):
            if stats[c, cv2.CC_STAT_AREA] < minimo:
                continue
            region = cv2.erode((etiquetas == c).astype(np.uint8), nucleo).astype(bool)
            if region.sum() < minimo / 2:
                continue
            regiones += 1
            razon = razon_bimodal(luz, region)
            if razon is not None:
                razones.append(razon)
    if razones:
        return comun.mediana(razones), None
    return None, NO_SOMBRA if regiones else SIN_REGIONES


def ancho_de_borde(lab, fuera=None):
    """Ancho mediano (px del cuadro) de la transición de los bordes con contraste, o None."""
    luz = lab[..., 0]
    gris8 = np.clip(luz * 2.55, 0, 255).astype(np.uint8)
    bordes = cv2.Canny(gris8, 60, 150) > 0
    if fuera is not None:
        bordes &= ~fuera
    pendiente = np.hypot(cv2.Sobel(luz, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(luz, cv2.CV_32F, 0, 1, ksize=3)) / 8.0
    contraste = ndimage.maximum_filter(luz, size=9) - ndimage.minimum_filter(luz, size=9)
    pendiente = ndimage.maximum_filter(pendiente, size=3)
    util = bordes & (contraste > 20) & (pendiente > 0)
    if util.sum() < TRAZO_MIN_PUNTOS:
        return None
    return float(np.median(contraste[util] / pendiente[util]))


def medir_cuadro(bgr, cajas_texto=None):
    """Las medidas de un cuadro en px a 1080 de alto. Cada una puede ser None. `cajas_texto` son cajas (x0, y0, x1, y1)
    en px del cuadro."""
    lab = a_lab(bgr)
    escala = ALTO_REFERENCIA / bgr.shape[0]
    fondo = _fondo(lab)
    fuera = mascara_de_cajas(lab.shape[:2], cajas_texto)
    grosor, color_hex = trazo(bgr, lab, fondo, fuera)
    alto_el = alto_del_elemento(lab, fondo)
    oscuro = (lab[..., 0] < min(OSCURO_MAX, 0.6 * float(fondo[0]))) | fuera
    sombra, causa_sombra = razon_de_sombra(lab, oscuro)
    ancho_borde = ancho_de_borde(lab, fuera)
    return {"grosor_px": None if grosor is None else grosor * escala,
            "prop_elemento": None if grosor is None or not alto_el else grosor / alto_el,
            "color_trazo": color_hex, "sombra": sombra, "sombra_causa": causa_sombra,
            "borde_px": None if ancho_borde is None else ancho_borde * escala}


def medir_cuadros(cuadros, cajas_por_cuadro=None):
    """Dimensión sobre cuadros BGR sueltos (a la mayor resolución posible). `cajas_por_cuadro` es, por cuadro, la lista de
    cajas de texto (x0, y0, x1, y1) en px del cuadro."""
    if len(cuadros) == 0:
        return comun.todas_nulas(METRICAS, "sin cuadros")
    cajas_por_cuadro = cajas_por_cuadro or [None] * len(cuadros)
    por_cuadro = [medir_cuadro(c, cajas) for c, cajas in zip(cuadros, cajas_por_cuadro)]
    de = lambda k: [m[k] for m in por_cuadro if m[k] is not None]
    colores = de("color_trazo")
    causas = de("sombra_causa")
    causa_sombra = NO_SOMBRA if NO_SOMBRA in causas else (causas[0] if causas else SIN_REGIONES)
    metricas = {
        "grosor_contorno_px_1080": comun.o_nula(comun.mediana(de("grosor_px")), SIN_TRAZO),
        "grosor_contorno_prop_elemento": comun.o_nula(comun.mediana(de("prop_elemento")), SIN_TRAZO),
        "color_trazo": comun.o_nula(max(set(colores), key=colores.count) if colores else None, SIN_TRAZO),
        "sombra_razon_luz": comun.o_nula(comun.mediana(de("sombra")), causa_sombra),
        "borde_transicion_px_1080": comun.o_nula(comun.mediana(de("borde_px")), "no se vieron bordes con contraste"),
    }
    return {"metricas": metricas, "detalle": {"cuadros_medidos": len(cuadros), "por_cuadro": por_cuadro}}


def cajas_en(tramos_texto, segundo, alto_ocr, alto_cuadro):
    """Las cajas de los textos que estaban en pantalla en `segundo`, pasadas de px del cuadro del OCR a px del cuadro."""
    factor = alto_cuadro / alto_ocr
    return [tuple(v * factor for v in t["caja"]) for t in tramos_texto if t["inicio"] <= segundo < t["fin"]]


def en_transicion(segundo, transiciones):
    """¿El segundo cae dentro de alguna transición (inicio_s, fin_s), con un margen?"""
    return any(a - TRANSICION_MARGEN_S <= segundo <= b + TRANSICION_MARGEN_S for a, b in transiciones)


def medir(video, texto_detalle=None, transiciones=()):
    """`texto_detalle` es el detalle de la dimensión texto (sus tramos con caja) para taparlos, o None. `transiciones` son
    los (inicio_s, fin_s) que vio la dimensión cortes: los cuadros dentro de ellas no se miden."""
    fps = min(1.0, CUADROS_MAX / video.info["dur"])
    todos = list(video.iterar(fps, ALTO_REFERENCIA, max_cuadros=CUADROS_MAX))
    quedan = [i for i in range(len(todos)) if not en_transicion(i / fps, transiciones)]
    if not quedan:
        return comun.todas_nulas(METRICAS, "todos los cuadros caen dentro de una transición")
    cuadros = [todos[i] for i in quedan]
    cajas = None
    if texto_detalle and texto_detalle.get("tramos"):
        cajas = [cajas_en(texto_detalle["tramos"], i / fps, texto_detalle["alto_cuadro"], todos[i].shape[0]) for i in quedan]
    r = medir_cuadros(cuadros, cajas)
    r["detalle"]["cuadros_en_transicion"] = len(todos) - len(cuadros)
    return r
