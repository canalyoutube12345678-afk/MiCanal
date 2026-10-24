"""Paso 5: miniatura + metadata.json (título, descripción con capítulos y créditos, etiquetas).

El título, la descripción y las etiquetas los escribe Claude en escenas.json -> "youtube".
Este script añade los capítulos con los tiempos reales y los créditos de las imágenes.

Uso: python scripts/metadatos.py videos/<carpeta>
"""
import sys

import plantillas
from comun import carpeta_video, config, guardar_json, leer_json, log


def mmss(s):
    s = int(s)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def main(carpeta):
    cfg = config()
    datos = leer_json(carpeta / "escenas.json")
    yt = datos.get("youtube", {})

    # miniatura: estilo dramático con imagen de IA si hay "ia" y "lineas"; si no, la sencilla con una escena
    mini = datos.get("miniatura", {})
    escena_mini = next((e for e in datos["escenas"] if e["id"] == mini.get("escena")), None) \
        or next(e for e in datos["escenas"] if e.get("archivo"))
    base = carpeta / "miniatura_base.jpg"
    if mini.get("ia") and not base.exists():
        try:
            import ia_imagen
            ia_imagen.generar(mini["ia"], base, 1280, 720, semilla=mini.get("semilla", 7))
        except Exception as e:  # sin IA, se usa la imagen de una escena
            log(f"AVISO: imagen IA no disponible ({e}); uso la de la escena {escena_mini['id']}")
    if mini.get("lineas"):
        fondo = base if base.exists() else carpeta / escena_mini["archivo"]
        plantillas.miniatura_drama(fondo, mini["lineas"], cfg["estilo"], carpeta / "miniatura.png",
                                   mini.get("posicion", "abajo"), mini.get("circulo"), mini.get("banda"))
    else:
        plantillas.miniatura(carpeta / escena_mini["archivo"], mini.get("texto", datos["titulo"]), cfg["estilo"],
                             carpeta / "miniatura.png")

    # capítulos (YouTube exige que el primero sea 0:00 y al menos 3 de 10 s o más)
    capitulos = [(e["inicio"], e["capitulo"]) for e in datos["escenas"] if e.get("capitulo") and "inicio" in e]
    if capitulos and capitulos[0][0] > 0:
        capitulos.insert(0, (0, "Introducción"))
    texto_capitulos = "\n".join(f"{mmss(t)} {nombre}" for t, nombre in capitulos) if len(capitulos) >= 3 else ""

    partes = [yt.get("descripcion", "").strip()]
    if texto_capitulos:
        partes.append("CAPÍTULOS\n" + texto_capitulos)
    if yt.get("fuentes"):
        partes.append("FUENTES\n" + "\n".join(f"- {f}" for f in yt["fuentes"]))
    creditos = carpeta / "creditos.txt"
    if creditos.exists():
        partes.append(creditos.read_text(encoding="utf-8").strip())
    partes.append("Narración con voz sintética. Vídeo con fines informativos y divulgativos.")

    meta = {
        "titulo": yt.get("titulo", datos["titulo"])[:100],
        "descripcion": "\n\n".join(p for p in partes if p)[:5000],
        "etiquetas": yt.get("etiquetas", []),
        "categoria": cfg["youtube"]["categoria"],
        "idioma": cfg["youtube"]["idioma"],
        "privacidad": cfg["youtube"]["privacidad_por_defecto"],
        "contenido_sintetico": False,  # voz TTS narrando no es "contenido realista alterado"; ver ESTADO.md
        "duracion_s": datos.get("duracion_total"),
    }
    anterior = carpeta / "metadata.json"
    if anterior.exists():  # conserva el ID de YouTube si ya se subió
        meta = {**{k: v for k, v in leer_json(anterior).items() if k.startswith("youtube_")}, **meta}
    guardar_json(anterior, meta)
    log(f"Miniatura y metadata listos ({len(capitulos)} capítulos).")


if __name__ == "__main__":
    main(carpeta_video(sys.argv[1]))
