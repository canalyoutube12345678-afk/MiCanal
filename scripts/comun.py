"""Utilidades compartidas: configuración, rutas y llamadas a FFmpeg."""
import json
import os
import ssl
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
VIDEOS = RAIZ / "videos"
ASSETS = RAIZ / "assets"
REGISTRO = RAIZ / "registro"
USER_AGENT = "MiCanalBot/1.0 (canal educativo; contacto en la descripcion del canal) python-requests"


def config():
    with open(RAIZ / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def contexto_ssl():
    """Si hay un certificado de proxy (entornos corporativos/nube), úsalo; si no, el normal."""
    cafile = os.environ.get("SSL_CERT_FILE")
    if cafile and Path(cafile).exists():
        return ssl.create_default_context(cafile=cafile)
    return None


def ffmpeg(*args, cwd=None):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg falló:\n{' '.join(cmd)}\n{r.stderr}")


def duracion(ruta):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def carpeta_video(arg):
    p = Path(arg)
    if not p.is_absolute():
        p = VIDEOS / arg if (VIDEOS / arg).exists() else Path.cwd() / arg
    if not (p / "escenas.json").exists():
        sys.exit(f"No encuentro escenas.json en {p}")
    return p


def log(msg):
    print(msg, flush=True)
