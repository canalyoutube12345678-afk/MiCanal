"""Paso 3: monta el vídeo. Escena a escena (imagen con movimiento suave + voz + subtítulos),
luego concatena, mezcla la música bajo la voz y normaliza el volumen.

Uso: python scripts/montaje.py videos/<carpeta>
"""
import hashlib
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import plantillas
from comun import ASSETS, RAIZ, carpeta_video, config, duracion, ffmpeg, guardar_json, leer_json, log

COLA_SILENCIO = 0.45   # respiro tras cada escena (s)
FUNDIDO = 0.25         # fundido a negro muy corto entre escenas (s)
MAX_CARACTERES = 44    # por línea de subtítulo


def ass_tiempo(s):
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def ass_escapar(t):
    return t.replace("\\", "").replace("{", "(").replace("}", ")")


def _normal(s):
    return re.sub(r"[^\w]", "", s.lower())


def alinear(palabras, texto):
    """edge-tts devuelve las palabras sin puntuación: las recuperamos del guion original."""
    tokens = texto.split()
    i, salida = 0, []
    for p in palabras:
        k = max(1, len(p["t"].split()))
        objetivo = _normal(p["t"])
        for salto in range(4):  # tolera palabras del guion que la voz no marca (p. ej. símbolos sueltos)
            trozo = tokens[i + salto:i + salto + k]
            if trozo and _normal("".join(trozo)) == objetivo:
                salida.append({**p, "t": " ".join(trozo)})
                i += salto + k
                break
        else:
            salida.append(p)
    return salida


def trozos_subtitulos(palabras):
    """Agrupa palabras en frases cortas: corta en pausas, final de frase o al llegar al límite de caracteres."""
    trozos, actual = [], []
    for i, p in enumerate(palabras):
        actual.append(p)
        texto = " ".join(x["t"] for x in actual)
        siguiente = palabras[i + 1] if i + 1 < len(palabras) else None
        pausa = siguiente and (siguiente["ini"] - p["fin"] > 0.28 or p["t"].rstrip("»\"”)").endswith((".", "?", "!", ":", ";")))
        if not siguiente or pausa or len(texto) >= MAX_CARACTERES * 2 - 10 or (
            len(texto) > MAX_CARACTERES and siguiente and len(texto) + len(siguiente["t"]) > MAX_CARACTERES * 2 - 10
        ):
            trozos.append({"texto": texto, "ini": actual[0]["ini"], "fin": p["fin"]})
            actual = []
    # que cada subtítulo dure hasta que empiece el siguiente si el hueco es pequeño
    for a, b in zip(trozos, trozos[1:]):
        if b["ini"] - a["fin"] < 0.6:
            a["fin"] = b["ini"]
    return trozos


def partir_en_dos(texto):
    if len(texto) <= MAX_CARACTERES:
        return texto
    palabras = texto.split()
    mejor, corte = 1e9, 1
    for i in range(1, len(palabras)):
        dif = abs(len(" ".join(palabras[:i])) - len(" ".join(palabras[i:])))
        if dif < mejor:
            mejor, corte = dif, i
    return " ".join(palabras[:corte]) + r"\N" + " ".join(palabras[corte:])


def escribir_ass(destino, escena, palabras, duracion_total, cfg):
    estilo = cfg["estilo"]
    acento = estilo["color_acento"].lstrip("#")
    acento_ass = f"&H00{acento[4:6]}{acento[2:4]}{acento[0:2]}"
    alto = cfg["video"]["alto"]
    lineas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {cfg['video']['ancho']}", f"PlayResY: {alto}", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        f"Style: Sub,Arial,{round(alto * 0.05)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,"
        f"{round(alto * 0.0035)},1,2,160,160,{round(alto * 0.07)},1",
        f"Style: Rotulo,Arial,{round(alto * 0.036)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,1,0,0,0,100,100,0,0,3,"
        f"14,0,7,70,70,60,1",
        f"Style: Fecha,Arial,{round(alto * 0.03)},{acento_ass},{acento_ass},&H00000000,&H96000000,1,0,0,0,100,100,0,0,3,"
        f"12,0,7,70,70,115,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    if escena.get("rotulo"):
        lineas.append(f"Dialogue: 0,{ass_tiempo(0.3)},{ass_tiempo(duracion_total - 0.3)},Rotulo,,0,0,0,,"
                      f"{{\\fad(400,300)}}{ass_escapar(escena['rotulo'])}")
    if escena.get("fecha"):
        lineas.append(f"Dialogue: 0,{ass_tiempo(0.3)},{ass_tiempo(duracion_total - 0.3)},Fecha,,0,0,0,,"
                      f"{{\\fad(400,300)}}{ass_escapar(escena['fecha'])}")
    if cfg["estilo"].get("subtitulos", True):
        for t in trozos_subtitulos(palabras):
            lineas.append(f"Dialogue: 1,{ass_tiempo(t['ini'])},{ass_tiempo(t['fin'])},Sub,,0,0,0,,"
                          f"{partir_en_dos(ass_escapar(t['texto']))}")
    Path(destino).write_text("\n".join(lineas) + "\n", encoding="utf-8")


def movimiento(id_escena, dur):
    """Desplazamiento suave distinto en cada escena (izq→der, der→izq, arriba→abajo, abajo→arriba)."""
    tipo = random.Random(id_escena).choice(range(4))
    if tipo == 0:
        return f"(iw-ow)*t/{dur:.3f}", "(ih-oh)/2"
    if tipo == 1:
        return f"(iw-ow)*(1-t/{dur:.3f})", "(ih-oh)/2"
    if tipo == 2:
        return "(iw-ow)/2", f"(ih-oh)*t/{dur:.3f}"
    return "(iw-ow)/2", f"(ih-oh)*(1-t/{dur:.3f})"


def render_escena(carpeta, e, cfg, hilos):
    v = cfg["video"]
    tmp = carpeta / "tmp"
    clip = carpeta / "clips" / f"{e['id']:03d}.mp4"
    firma_archivo = clip.with_suffix(".firma")
    mp3 = carpeta / "audio" / f"{e['id']:03d}.mp3"
    hay_voz = e.get("duracion_voz", 0) > 0
    dur = (e["duracion_voz"] + COLA_SILENCIO) if hay_voz else float(e.get("duracion", 3.5))

    # si cambia cualquier entrada (texto, imagen, voz, estilo o este script), la escena se vuelve a montar
    entradas = [carpeta / e["archivo"] if e.get("archivo") else None, mp3 if hay_voz else None, Path(__file__)]
    huellas = [(p.stat().st_size, p.stat().st_mtime_ns) for p in entradas if p and p.exists()]
    firma = hashlib.md5(repr([
        e.get("texto"), e.get("tipo"), e.get("archivo"), e.get("rotulo"), e.get("fecha"), e.get("capitulo"),
        e.get("subtitulo"), round(dur, 3), v, cfg["estilo"], huellas,
    ]).encode()).hexdigest()
    if clip.exists() and firma_archivo.exists() and firma_archivo.read_text() == firma:
        return clip

    # 1) imagen de fondo (lienzo un poco más grande que el vídeo para poder moverse)
    lienzo = tmp / f"{e['id']:03d}.jpg"
    if e.get("tipo") == "tarjeta":
        titulo = e.get("capitulo") or e.get("rotulo") or e.get("tarjeta_texto") or ""
        plantillas.tarjeta(titulo, e.get("subtitulo", ""), cfg["estilo"],
                           v["ancho"], v["alto"], lienzo)
    else:
        plantillas.lienzo(carpeta / e["archivo"], v["ancho"], v["alto"], lienzo)

    # 2) subtítulos y rótulos
    palabras = alinear(leer_json(mp3.with_suffix(".json"))["palabras"], e["texto"]) if hay_voz else []
    ass = tmp / f"{e['id']:03d}.ass"
    escribir_ass(ass, {**e, "rotulo": None} if e.get("tipo") == "tarjeta" else e, palabras, dur, cfg)

    # 3) render
    x, y = movimiento(e["id"], dur)
    entrada_audio = ["-i", mp3] if hay_voz else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    filtro = (
        f"[0:v]crop={v['ancho']}:{v['alto']}:x='{x}':y='{y}',"
        f"fade=t=in:st=0:d={FUNDIDO},fade=t=out:st={dur - FUNDIDO:.3f}:d={FUNDIDO},"
        f"subtitles=tmp/{ass.name},format=yuv420p[v];"
        f"[1:a]aresample=48000,apad[a]"
    )
    ffmpeg(
        "-threads", hilos, "-loop", "1", "-framerate", v["fps"], "-i", lienzo.relative_to(carpeta), *entrada_audio,
        "-filter_complex", filtro, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", v["preset"], "-crf", v["crf"], "-r", v["fps"], "-g", v["fps"] * 2,
        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
        clip.relative_to(carpeta), cwd=carpeta,
    )
    firma_archivo.write_text(firma)
    return clip


def mezclar_audio(carpeta, unido, final, cfg):
    musicas = sorted(p for p in (RAIZ / cfg["musica"]["carpeta"]).glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg"))
    lufs = cfg["audio"]["lufs"]
    norm = f"loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample=48000"
    if musicas:
        pista = random.Random(carpeta.name).choice(musicas)
        log(f"Música: {pista.name}")
        filtro = (
            f"[0:a]asplit=2[voz][lateral];"
            f"[1:a]volume={cfg['musica']['volumen_db']}dB,aresample=48000[m];"
            f"[m][lateral]sidechaincompress=threshold=0.03:ratio=8:attack=30:release=600[md];"
            f"[voz][md]amix=inputs=2:duration=first:normalize=0,{norm}[a]"
        )
        ffmpeg("-i", unido, "-stream_loop", "-1", "-i", pista, "-filter_complex", filtro,
               "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
               "-movflags", "+faststart", final)
    else:
        ffmpeg("-i", unido, "-af", norm, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", final)


def main(carpeta):
    cfg = config()
    datos = leer_json(carpeta / "escenas.json")
    for sub in ("tmp", "clips"):
        (carpeta / sub).mkdir(exist_ok=True)
    escenas = datos["escenas"]
    nucleos = os.cpu_count() or 2
    trabajadores = max(1, nucleos // 2)
    log(f"Montando {len(escenas)} escenas ({trabajadores} a la vez)...")
    with ThreadPoolExecutor(trabajadores) as pool:
        futuros = [pool.submit(render_escena, carpeta, e, cfg, 2) for e in escenas]
        clips = []
        for i, f in enumerate(futuros, 1):
            clips.append(f.result())
            if i % 10 == 0 or i == len(futuros):
                log(f"  {i}/{len(futuros)} escenas")

    # tiempos reales de cada escena -> capítulos para la descripción
    t = 0.0
    for e, c in zip(escenas, clips):
        e["inicio"] = round(t, 2)
        t += duracion(c)
    datos["duracion_total"] = round(t, 2)
    guardar_json(carpeta / "escenas.json", datos)

    lista = carpeta / "tmp" / "lista.txt"
    lista.write_text("".join(f"file '{c.resolve().as_posix()}'\n" for c in clips), encoding="utf-8")
    unido = carpeta / "tmp" / "unido.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", unido)
    final = carpeta / "video_final.mp4"
    mezclar_audio(carpeta, unido, final, cfg)
    log(f"Vídeo listo: {final} ({t / 60:.1f} min)")


if __name__ == "__main__":
    main(carpeta_video(sys.argv[1]))
