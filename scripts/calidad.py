"""Paso 4: control de calidad automático + fotogramas para revisar a ojo.

Comprueba resolución, duración, pantallas negras largas y silencios largos.
Extrae 8 fotogramas a qc/ para revisarlos antes de publicar.

Uso: python scripts/calidad.py videos/<carpeta>
"""
import re
import subprocess
import sys

from comun import carpeta_video, config, duracion, ffmpeg, leer_json, log


def main(carpeta):
    cfg = config()
    datos = leer_json(carpeta / "escenas.json")
    video = carpeta / "video_final.mp4"
    problemas = []

    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    ancho, alto = map(int, r.stdout.strip().split(","))
    if (ancho, alto) != (cfg["video"]["ancho"], cfg["video"]["alto"]):
        problemas.append(f"Resolución {ancho}x{alto}, esperaba {cfg['video']['ancho']}x{cfg['video']['alto']}")

    dur = duracion(video)
    minimo, maximo = cfg["video"]["duracion_objetivo_min"]
    if not datos.get("prueba") and not (minimo * 60 <= dur <= maximo * 60 + 60):
        problemas.append(f"Duración {dur / 60:.1f} min fuera del objetivo {minimo}-{maximo} min")

    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "blackdetect=d=1.0:pix_th=0.08",
                        "-af", "silencedetect=n=-45dB:d=2.5", "-f", "null", "-"], capture_output=True, text=True)
    negros = re.findall(r"black_start:([\d.]+)", r.stderr)
    silencios = re.findall(r"silence_start: ([\d.]+)", r.stderr)
    # las tarjetas de capítulo tienen fondo muy oscuro: no cuentan como pantalla negra
    tarjetas = [(e["inicio"], e["inicio"] + 6) for e in datos["escenas"] if e.get("tipo") == "tarjeta" and "inicio" in e]
    negros = [s for s in negros if not any(a - 0.5 <= float(s) <= b for a, b in tarjetas)]
    if negros:
        problemas.append(f"Pantalla negra >1 s en: {', '.join(f'{float(s):.0f}s' for s in negros[:10])}")
    escenas_mudas = {round(e["inicio"]) for e in datos["escenas"] if not e.get("duracion_voz") and "inicio" in e}
    silencios = [s for s in silencios if round(float(s)) not in escenas_mudas]
    if silencios:
        problemas.append(f"Silencio >2.5 s en: {', '.join(f'{float(s):.0f}s' for s in silencios[:10])}")

    qc = carpeta / "qc"
    qc.mkdir(exist_ok=True)
    for i in range(8):
        t = dur * (i + 0.5) / 8
        ffmpeg("-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=960:-2", qc / f"fotograma_{i + 1}.jpg")

    log(f"Duración: {int(dur // 60)}:{int(dur % 60):02d} · {ancho}x{alto}")
    if problemas:
        log("PROBLEMAS:\n- " + "\n- ".join(problemas))
    else:
        log("Control de calidad OK.")
    log(f"Revisa los fotogramas en {qc}")
    return not problemas


if __name__ == "__main__":
    sys.exit(0 if main(carpeta_video(sys.argv[1])) else 1)
