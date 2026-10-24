"""Paso 6: deja el vídeo y la miniatura en una URL pública para que Metricool los descargue.

GitHub limita cada archivo a 100 MB, así que el vídeo se recomprime (2 pasadas) a ~95 MB como máximo.
Cada vídeo va en su propia rama del repositorio público `MiCanal-videos`; cuando ya está publicado
en YouTube, se borra la rama con --borrar para no llenar el repositorio.

Uso:
  python scripts/alojar.py videos/<carpeta>            # sube y muestra las URLs
  python scripts/alojar.py videos/<carpeta> --borrar   # borra la rama tras publicar
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from comun import carpeta_video, config, duracion, ffmpeg, guardar_json, leer_json, log

LIMITE_MB = 95
AUDIO_KBPS = 96


def git(*args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falló:\n{r.stderr}")
    return r.stdout


def comprimir(origen, destino):
    """Vídeo a la tasa justa para que quepa en LIMITE_MB (si ya cabe, se copia tal cual)."""
    if origen.stat().st_size <= LIMITE_MB * 1024 * 1024:
        shutil.copy(origen, destino)
        return
    kbps = int(LIMITE_MB * 8 * 1024 / duracion(origen)) - AUDIO_KBPS - 10
    log(f"Recomprimiendo a {kbps} kbps para que quepa en {LIMITE_MB} MB...")
    with tempfile.TemporaryDirectory() as tmp:
        log_pasada = Path(tmp) / "pasada"
        comunes = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-passlogfile", log_pasada]
        ffmpeg("-i", origen, *comunes, "-pass", "1", "-an", "-f", "mp4", "-y", Path(tmp) / "nulo.mp4")
        ffmpeg("-i", origen, *comunes, "-pass", "2", "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k",
               "-movflags", "+faststart", destino)


def main(carpeta, borrar=False):
    cfg = config()["alojamiento"]
    repo, rama = cfg["repositorio"], f"video/{carpeta.name}"
    url_git = f"https://github.com/{repo}"
    if borrar:
        subprocess.run(["git", "push", url_git, "--delete", rama], capture_output=True, text=True)
        log(f"Rama {rama} borrada.")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        git("init", "-q", "-b", rama, cwd=tmp)
        comprimir(carpeta / "video_final.mp4", tmp / "video.mp4")
        shutil.copy(carpeta / "miniatura.png", tmp / "miniatura.png")
        git("add", "video.mp4", "miniatura.png", cwd=tmp)
        git("-c", "user.name=MiCanal", "-c", "user.email=micanal@localhost", "commit", "-qm",
            f"Vídeo {carpeta.name}", cwd=tmp)
        git("push", "-f", url_git, f"{rama}:{rama}", cwd=tmp)
    base = f"https://raw.githubusercontent.com/{repo}/{rama}"
    urls = {"video": f"{base}/video.mp4", "miniatura": f"{base}/miniatura.png"}
    meta = leer_json(carpeta / "metadata.json")
    meta["alojamiento"] = urls
    guardar_json(carpeta / "metadata.json", meta)
    log(f"Vídeo: {urls['video']}\nMiniatura: {urls['miniatura']}")
    return urls


if __name__ == "__main__":
    main(carpeta_video(sys.argv[1]), "--borrar" in sys.argv)
