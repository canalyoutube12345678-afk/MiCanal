"""Produce un vídeo completo con UN solo comando: voz -> imágenes -> montaje -> calidad -> miniatura/metadatos.

Uso: python scripts/producir.py videos/<carpeta>
Si algo falla, vuelve a lanzarlo: lo ya hecho (voz, imágenes, escenas montadas) no se repite.
"""
import asyncio
import sys
import time
import traceback
from datetime import datetime

import calidad
import imagenes
import metadatos
import montaje
import voz
from comun import REGISTRO, carpeta_video, log


def main(carpeta):
    inicio = time.time()
    try:
        log("== 1/5 Voz ==")
        asyncio.run(voz.main(carpeta))
        log("== 2/5 Imágenes ==")
        imagenes.main(carpeta)
        log("== 3/5 Montaje ==")
        montaje.main(carpeta)
        log("== 4/5 Calidad ==")
        ok = calidad.main(carpeta)
        log("== 5/5 Miniatura y metadatos ==")
        metadatos.main(carpeta)
    except Exception:
        REGISTRO.mkdir(exist_ok=True)
        with open(REGISTRO / "ERRORES.md", "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now():%Y-%m-%d %H:%M} · {carpeta.name}\n```\n{traceback.format_exc()}```\n")
        log("ERROR: apuntado en registro/ERRORES.md")
        raise
    minutos = (time.time() - inicio) / 60
    log(f"Terminado en {minutos:.1f} min. {'Listo para revisar.' if ok else 'Revisa los problemas de calidad.'}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(carpeta_video(sys.argv[1])) else 1)
