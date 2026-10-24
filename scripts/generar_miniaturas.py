"""Genera las miniaturas de ideas/outliers.json (imagen IA + plantilla dramática) en ideas/miniaturas/.

Uso: python scripts/generar_miniaturas.py [id ...]
"""
import sys

import ia_imagen
import plantillas
from comun import RAIZ, config, leer_json, log


def main(ids):
    cfg = config()
    salida = RAIZ / "ideas" / "miniaturas"
    salida.mkdir(parents=True, exist_ok=True)
    for i, idea in enumerate(leer_json(RAIZ / "ideas" / "outliers.json")):
        if ids and idea["id"] not in ids:
            continue
        base = salida / f"{idea['id']}_base.jpg"
        if not base.exists():
            log(f"IA: {idea['id']}...")
            ia_imagen.generar(idea["prompt"], base, 1280, 720, semilla=100 + i)
        m = idea["miniatura"]
        plantillas.miniatura_drama(base, m["lineas"], cfg["estilo"], salida / f"{idea['id']}.png",
                                   m.get("posicion", "abajo"), m.get("circulo"), m.get("banda"))
        log(f"Miniatura: {idea['id']}.png")


if __name__ == "__main__":
    main(sys.argv[1:])
