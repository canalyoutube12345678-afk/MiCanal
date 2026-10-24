"""Paso 1: genera la locución de cada escena con edge-tts y guarda los tiempos de cada palabra.

Uso: python scripts/voz.py videos/<carpeta>
"""
import asyncio
import hashlib
import sys

import edge_tts
import edge_tts.communicate

from comun import carpeta_video, config, contexto_ssl, duracion, guardar_json, leer_json, log

ctx = contexto_ssl()
if ctx:
    edge_tts.communicate._SSL_CTX = ctx


async def sintetizar(texto, voz, velocidad, tono, mp3, intentos=4):
    for intento in range(1, intentos + 1):
        palabras = []
        try:
            com = edge_tts.Communicate(texto, voz, rate=velocidad, pitch=tono, boundary="WordBoundary")
            with open(mp3, "wb") as f:
                async for chunk in com.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        palabras.append({
                            "t": chunk["text"],
                            "ini": chunk["offset"] / 1e7,
                            "fin": (chunk["offset"] + chunk["duration"]) / 1e7,
                        })
            return palabras
        except Exception as e:  # la red falla de vez en cuando: reintenta
            if intento == intentos:
                raise
            log(f"  reintento {intento} ({e.__class__.__name__})")
            await asyncio.sleep(2 ** intento)


async def main(carpeta):
    cfg = config()["voz"]
    escenas = leer_json(carpeta / "escenas.json")
    (carpeta / "audio").mkdir(exist_ok=True)
    total = 0.0
    for e in escenas["escenas"]:
        texto = e.get("texto", "").strip()
        if not texto:  # escena muda (p. ej. tarjeta de capítulo sin narración)
            e["duracion_voz"] = 0.0
            continue
        tono = cfg.get("tono", "+0Hz")
        firma = hashlib.md5(f"{cfg['voz']}|{cfg['velocidad']}|{tono}|{texto}".encode()).hexdigest()
        mp3 = carpeta / "audio" / f"{e['id']:03d}.mp3"
        palabras_json = carpeta / "audio" / f"{e['id']:03d}.json"
        if mp3.exists() and palabras_json.exists() and leer_json(palabras_json).get("firma") == firma:
            e["duracion_voz"] = duracion(mp3)
        else:
            log(f"Voz escena {e['id']}...")
            palabras = await sintetizar(texto, cfg["voz"], cfg["velocidad"], tono, mp3)
            guardar_json(palabras_json, {"firma": firma, "palabras": palabras})
            e["duracion_voz"] = duracion(mp3)
        total += e["duracion_voz"]
    guardar_json(carpeta / "escenas.json", escenas)
    log(f"Voz lista: {len(escenas['escenas'])} escenas, {total / 60:.1f} min de locución")


if __name__ == "__main__":
    asyncio.run(main(carpeta_video(sys.argv[1])))
