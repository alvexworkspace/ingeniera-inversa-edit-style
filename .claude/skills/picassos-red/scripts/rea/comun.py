"""Piezas compartidas: el formato de una métrica y de una dimensión.

Una métrica es {"valor": número o texto, "origen": "codigo"}. Si no se pudo medir es
{"valor": None, "causa": "...", "origen": "codigo"}: nunca se inventa un número.
Una dimensión devuelve {"metricas": {nombre: métrica}, "detalle": {...}}.
"""
import numpy as np

ORIGEN = "codigo"


def ok(valor):
    """Métrica medida. Los números de numpy se vuelven números de Python y se redondean."""
    if isinstance(valor, (np.floating, float)):
        valor = round(float(valor), 4)
    elif isinstance(valor, np.integer):
        valor = int(valor)
    return {"valor": valor, "origen": ORIGEN}


def nula(causa):
    """Métrica que no se pudo medir, con su causa."""
    return {"valor": None, "causa": causa, "origen": ORIGEN}


def o_nula(valor, causa):
    """`ok(valor)` si hay valor, `nula(causa)` si es None."""
    return nula(causa) if valor is None else ok(valor)


def mediana(valores):
    """Mediana de una lista, o None si está vacía."""
    return None if len(valores) == 0 else float(np.median(valores))


def porcentaje(parte, total):
    """Porcentaje (0 a 100), o None si no hay total."""
    return None if not total else 100.0 * parte / total


def todas_nulas(nombres, causa):
    """Resultado de una dimensión entera que no se pudo medir."""
    return {"metricas": {n: nula(causa) for n in nombres}, "detalle": {}}


# Qué tanto se puede fiar de cada métrica en estilos con barridos, desenfoque o dibujo sobre un decorado. La clave es el nombre completo de la métrica
# o un prefijo con comodín al final ("cortes.*"); gana la clave más específica (la más larga). Lo que no está aquí es confiable.
# "no": no entra al ranking de comparar.py, se mide a ojo con hojas de cuadros. "cuidado": entra, con una marca.
CONFIANZA = {
    "cortes.*": ("no", "los barridos con desenfoque cuentan como cortes"),
    "animacion.sostenido_modal_cuadros": ("no", "confunde el ciclo de pose y el paralaje"),
    "animacion.pct_en_*": ("no", "confunde el ciclo de pose y el paralaje"),
    "camara.empuje_escala*": ("no", "objetos que crecen y tramos unidos a través de cortes"),
    "camara.alejamiento_escala*": ("no", "objetos que crecen y tramos unidos a través de cortes"),
    "camara.pct_empujes_sube*": ("no", "objetos que crecen y tramos unidos a través de cortes"),
    "guion.*": ("no", "heredan los cortes y los subtítulos sesgados"),
    "sonido.efectos_por_min": ("no", "la música da efectos falsos"),
    "sonido.efectos_sobre_palabra_pct": ("no", "la música da efectos falsos"),
    "camara.pct_tiempo_*": ("cuidado", "la cámara se mide solo en una parte del tiempo y con objetos que crecen"),
    "camara.paneo_px_s_mediano": ("cuidado", "la cámara se mide solo en una parte del tiempo y con objetos que crecen"),
    "camara.pct_tiempo_con_paralaje": ("cuidado", "la cámara se mide solo en una parte del tiempo y con objetos que crecen"),
    "animacion.pct_cuadros_estaticos": ("cuidado", "el paralaje y el ciclo de pose también mueven celdas"),
    "animacion.cambio_medio_pct": ("cuidado", "el paralaje y el ciclo de pose también mueven celdas"),
    "ilustracion.*": ("cuidado", "se mide sobre unos 12 cuadros sueltos y las transiciones se omiten"),
    "sonido.inicios_sonido_por_min": ("cuidado", "cuenta también sílabas y notas, sirve para comparar mezclas parecidas"),
}


def confianza(nombre):
    """(nivel, porque) de una métrica: nivel es "no", "cuidado" o "si" (confiable, porque None). Busca el nombre exacto y
    después los prefijos con comodín; gana el más específico."""
    mejor, largo = ("si", None), -1
    for clave, valor in CONFIANZA.items():
        coincide = nombre.startswith(clave[:-1]) if clave.endswith("*") else nombre == clave
        if coincide and len(clave) > largo:
            mejor, largo = valor, len(clave)
    return mejor
