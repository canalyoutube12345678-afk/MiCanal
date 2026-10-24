"""Genera imágenes con IA sin GPU usando Pollinations (gratis, sin clave: 1 imagen cada ~45 s por IP).

Solo para miniaturas y banner (no para el vídeo entero). Si falla, el resto del sistema no depende de ella.
Con una clave gratuita de https://enter.pollinations.ai en .env (POLLINATIONS_KEY=...) no hay marca de agua ni espera.

Uso: python scripts/ia_imagen.py "descripción en inglés" salida.jpg [ancho alto semilla]
"""
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

from comun import RAIZ, log

URL = "https://image.pollinations.ai/prompt/{}"
ESTILO = ", photorealistic, cinematic dramatic lighting, HDR, high detail, 35mm photo, no text, no letters, no logos"


def clave():
    env = RAIZ / ".env"
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            if linea.startswith("POLLINATIONS_KEY="):
                return linea.split("=", 1)[1].strip()
    return os.environ.get("POLLINATIONS_KEY")


def generar(prompt, destino, ancho=1280, alto=720, semilla=1, intentos=8):
    params = {"width": ancho, "height": alto, "seed": semilla, "nologo": "true", "model": "flux"}
    cabeceras = {}
    if clave():
        cabeceras["Authorization"] = f"Bearer {clave()}"
    sesion = requests.Session()
    if os.environ.get("SSL_CERT_FILE"):
        sesion.verify = os.environ["SSL_CERT_FILE"]
    for i in range(intentos):
        # el modelo "flux" se satura a menudo: alterna con el modelo por defecto
        if i % 2:
            params.pop("model", None)
        else:
            params["model"] = "flux"
        try:
            r = sesion.get(URL.format(quote(prompt + ESTILO)), params=params, headers=cabeceras, timeout=180)
        except requests.RequestException as e:
            log(f"  red: {e.__class__.__name__}, reintento")
            time.sleep(20)
            continue
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
            Path(destino).write_bytes(r.content)
            return destino
        espera = 50 if r.status_code in (402, 429, 503) else 15
        log(f"  Pollinations {r.status_code}: espero {espera} s")
        time.sleep(espera)
    raise RuntimeError("Pollinations no ha generado la imagen; usa una imagen libre como plan B")


if __name__ == "__main__":
    a = sys.argv[1:]
    generar(a[0], a[1], *(int(x) for x in a[2:5]))
    log(f"Imagen guardada en {a[1]}")
