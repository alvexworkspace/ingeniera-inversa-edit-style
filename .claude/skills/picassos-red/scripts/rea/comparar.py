"""comparar.py: el ciclo de fidelidad. Dice en qué se aleja un render de su referencia, métrica por métrica.

    python .claude/skills/picassos-red/scripts/rea/comparar.py <resumen_referencia.json> <medidas_o_resumen_propio.json> [--salida <carpeta>] [--top N]

Por cada métrica de la referencia muestra su rango (p10 a p90), el valor propio y si cae adentro, arriba o abajo.
Ordena por lo más lejos: la lejanía es cuántos anchos del rango de la referencia se sale el valor propio. El ancho
nunca baja de un piso por unidad (un punto en un porcentaje, un px, 10 ms, 0,01 en una razón), para que una métrica
que casi no varía en la referencia no tape a las demás.
Se niega a comparar si la versión del medidor (`version` en medidas.json y resumen.json) no es la misma en los dos
archivos: una métrica con el mismo nombre puede haber cambiado de significado. Con --ignorar-version compara y lo
avisa en la primera línea. Lista aparte las métricas propias que la referencia no tiene.
Las métricas marcadas como no confiables (`comun.CONFIANZA`, nivel "no") no entran al ranking: van a una
sección aparte, "Se miden a ojo (hojas de cuadros)", con su valor, su rango y el porqué. Las de nivel "cuidado" quedan en
la tabla con una marca. El conteo de "dentro del rango" solo cuenta las confiables y las de cuidado.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rea.comun import confianza  # noqa: E402

PISO_RAZON = 0.01    # piso de las métricas sin unidad (razones, pesos, saturación, proporciones)


def piso(nombre):
    """Ancho mínimo del rango de la referencia para medir la lejanía, según la unidad que se lee en el nombre."""
    corto = nombre.split(".", 1)[-1]
    if corto.endswith("_ms"):
        return 10.0
    if corto.endswith("_s"):
        return 0.1
    if any(f in corto for f in ("pct", "_px", "px_", "por_min", "lufs", "dbfs", "luz_p", "temperatura", "cuadros", "grados", "total")):
        return 1.0
    return PISO_RAZON


def valor_de(entrada):
    """El número de una métrica propia: `valor` si es de un video, `mediana` si es de un resumen. None si no hay."""
    if entrada is None:
        return None
    v = entrada.get("mediana", entrada.get("valor"))
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def lejania(valor, ref, nombre=""):
    """(posicion, lejania) del valor respecto al rango p10-p90 de la referencia."""
    p10, p90 = ref["p10"], ref["p90"]
    escala = max(p90 - p10, piso(nombre))
    if valor > p90:
        return "arriba", (valor - p90) / escala
    if valor < p10:
        return "abajo", (p10 - valor) / escala
    return "adentro", 0.0


def _causa(propio, nombre, entrada):
    """Por qué no hay valor propio: la causa de la métrica (de un video) o las de las nulas del resumen."""
    if entrada is not None and entrada.get("causa"):
        return entrada["causa"]
    nulas = propio.get("nulas", {}).get(nombre)
    if nulas:
        return "; ".join(nulas["causas"])
    return "no está en lo propio" if entrada is None else "el valor propio no es un número"


class VersionDistinta(ValueError):
    """La referencia y lo propio se midieron con versiones distintas del medidor."""


def version_de(datos):
    """La versión del medidor que escribió el archivo (los anteriores a la versión 2 no la traen y valen 1)."""
    return datos.get("version", 1)


def comparar(referencia, propio, ignorar_version=False):
    """Filas de la comparación, ordenadas por lejanía. Las métricas sin dato propio van al final con su causa. Las
    propias que no están en la referencia van en `solo_propias`. Lanza VersionDistinta si las versiones no coinciden,
    salvo con `ignorar_version`, que lo deja en `aviso_version`."""
    va, vb = version_de(referencia), version_de(propio)
    aviso = None
    if va != vb:
        aviso = f"la referencia es de la versión {va} del medidor y lo propio de la {vb}: las métricas no son comparables"
        if not ignorar_version:
            raise VersionDistinta(aviso)
    filas, sin_dato, a_ojo = [], [], []
    for k, ref in referencia["metricas"].items():
        if "mediana" not in ref:
            sin_dato.append({"metrica": k, "causa": "es un texto, no un número: no se compara"})
            continue
        entrada = propio["metricas"].get(k)
        valor = valor_de(entrada)
        if valor is None:
            sin_dato.append({"metrica": k, "causa": _causa(propio, k, entrada)})
            continue
        posicion, lej = lejania(valor, ref, k)
        nivel, porque = confianza(k)
        fila = {"metrica": k, "ref_p10": ref["p10"], "ref_mediana": ref["mediana"], "ref_p90": ref["p90"],
                "propio": round(valor, 4), "posicion": posicion, "lejania": round(lej, 3), "confianza": nivel, "porque": porque}
        (a_ojo if nivel == "no" else filas).append(fila)
    filas.sort(key=lambda f: -f["lejania"])
    solo_propias = [{"metrica": k, "valor": valor_de(e)} for k, e in propio["metricas"].items() if k not in referencia["metricas"]]
    return {"version_referencia": va, "version_propio": vb, "aviso_version": aviso, "filas": filas, "a_ojo": a_ojo,
            "sin_dato": sin_dato, "solo_propias": solo_propias}


def a_markdown(resultado, top=None):
    filas = resultado["filas"][:top] if top else resultado["filas"]
    md = [f"AVISO: {resultado['aviso_version']}", ""] if resultado.get("aviso_version") else []
    md += ["| Métrica | Referencia p10 a p90 (mediana) | Propio | Posición | Lejanía | Confianza |", "|---|---|---|---|---|---|"]
    for f in filas:
        md.append(f"| {f['metrica']} | {f['ref_p10']} a {f['ref_p90']} ({f['ref_mediana']}) | {f['propio']} | "
                  f"{f['posicion']} | {f['lejania']} | {'cuidado: ' + f['porque'] if f['confianza'] == 'cuidado' else ''} |")
    adentro = sum(f["posicion"] == "adentro" for f in resultado["filas"])
    md += ["", f"{adentro} de {len(resultado['filas'])} métricas caen adentro del rango de la referencia."]
    if resultado.get("a_ojo"):
        md += ["", "Se miden a ojo (hojas de cuadros):", "", "| Métrica | Referencia p10 a p90 (mediana) | Propio | Porqué |", "|---|---|---|---|"]
        md += [f"| {f['metrica']} | {f['ref_p10']} a {f['ref_p90']} ({f['ref_mediana']}) | {f['propio']} | {f['porque']} |"
               for f in resultado["a_ojo"]]
    if resultado["sin_dato"]:
        md += ["", "Sin comparar:", ""] + [f"- {s['metrica']}: {s['causa']}" for s in resultado["sin_dato"]]
    if resultado.get("solo_propias"):
        md += ["", "Solo en lo propio (la referencia no las tiene):", ""]
        md += [f"- {s['metrica']}: {s['valor']}" for s in resultado["solo_propias"]]
    return "\n".join(md) + "\n"


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Compara un video (o un resumen) propio contra el resumen de una referencia.")
    ap.add_argument("referencia", help="resumen.json de la referencia")
    ap.add_argument("propio", help="medidas.json de un video o resumen.json propio")
    ap.add_argument("--salida", help="carpeta donde dejar comparacion.json y comparacion.md")
    ap.add_argument("--top", type=int, help="solo las N más lejanas en la tabla")
    ap.add_argument("--ignorar-version", action="store_true", help="compara aunque las versiones del medidor no coincidan")
    args = ap.parse_args(argv)
    referencia = json.loads(Path(args.referencia).read_text(encoding="utf-8"))
    propio = json.loads(Path(args.propio).read_text(encoding="utf-8"))
    try:
        resultado = comparar(referencia, propio, args.ignorar_version)
    except VersionDistinta as e:
        print(f"No se compara: {e}. Vuelve a medir con la misma versión (o usa --ignorar-version).", file=sys.stderr)
        return 2
    md = a_markdown(resultado, args.top)
    print(md)
    if args.salida:
        salida = Path(args.salida)
        salida.mkdir(parents=True, exist_ok=True)
        (salida / "comparacion.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
        (salida / "comparacion.md").write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
