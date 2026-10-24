"""Paso 2: busca y descarga una imagen con licencia libre para cada escena.

Fuentes (gratis, sin clave): Wikimedia Commons y, si falla o no hay resultados, Openverse
(que reúne imágenes libres de Flickr, Wikimedia, museos, etc.).

- Solo acepta dominio público, CC0, CC BY y CC BY-SA (permiten uso comercial y modificación).
- Guarda autor y licencia en assets/LICENCIAS.csv y en creditos.txt del vídeo.
- Si una escena trae "imagen" con un archivo propio, se usa tal cual.
- Si no encuentra nada, la escena se monta como tarjeta de texto.

Uso: python scripts/imagenes.py videos/<carpeta>
"""
import csv
import os
import re
import sys
import time
from pathlib import Path

import requests

from comun import ASSETS, USER_AGENT, carpeta_video, guardar_json, leer_json, log

COMMONS = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1/images/"
LICENCIA_OK = re.compile(r"^(public domain|pd\b|pdm|cc0|cc[- ]by(-sa)?([- ][\d.]+)?$|by(-sa)?$|no restrictions)", re.I)
ANCHO_MINIMO = 900

sesion = requests.Session()
sesion.headers["User-Agent"] = USER_AGENT
if os.environ.get("SSL_CERT_FILE"):
    sesion.verify = os.environ["SSL_CERT_FILE"]

commons_activo = True  # se desactiva en esta ejecución si Wikimedia nos limita


def obtener(url, params=None, intentos=3, json=True):
    """GET con reintentos; respeta Retry-After (límite 429). Devuelve None si no hay manera."""
    r = None
    for i in range(intentos):
        try:
            r = sesion.get(url, params=params, timeout=45)
        except requests.RequestException:
            time.sleep(3 * (i + 1))
            continue
        if r.status_code == 200 and (not json or r.headers.get("content-type", "").startswith("application/json")):
            time.sleep(1.2)  # ritmo amable con los servidores
            return r.json() if json else r.content
        if r.status_code in (404, 403):
            return None
        try:
            espera = int(r.headers.get("Retry-After", ""))
        except ValueError:
            espera = 4 * 2 ** i
        if espera > 60:  # nos piden esperar demasiado: mejor probar otra fuente
            return None
        time.sleep(espera)
    return None


def limpiar_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def licencia_valida(lic):
    return bool(LICENCIA_OK.search(lic)) and not re.search(r"\b(N[CD]|nc|nd)\b", lic)


def buscar_commons(busqueda=None, titulo=None):
    global commons_activo
    if not commons_activo:
        return []
    params = {"action": "query", "format": "json", "prop": "imageinfo",
              "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 2400}
    if titulo:
        params["titles"] = titulo
    else:
        params.update(generator="search", gsrsearch=f"{busqueda} filetype:bitmap", gsrnamespace=6, gsrlimit=15)
    datos = obtener(COMMONS, params)
    if datos is None:
        log("  Wikimedia no responde ahora; sigo solo con Openverse")
        commons_activo = False
        return []
    paginas = sorted(datos.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    salida = []
    for p in paginas:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = limpiar_html(meta.get("LicenseShortName", {}).get("value"))
        if info.get("mime") in ("image/jpeg", "image/png", "image/webp") and licencia_valida(lic) \
                and info.get("width", 0) >= ANCHO_MINIMO:
            salida.append({
                "titulo": p["title"], "url": info.get("thumburl") or info["url"], "pagina": info.get("descriptionurl"),
                "ancho": info["width"], "alto": info["height"],
                "autor": limpiar_html(meta.get("Artist", {}).get("value")) or "Desconocido", "licencia": lic,
            })
    return salida


def buscar_openverse(busqueda):
    datos = obtener(OPENVERSE, {"q": busqueda, "license_type": "commercial,modification", "page_size": 20,
                                "mature": "false"})
    if not datos:
        return []
    salida = []
    for r in datos.get("results", []):
        lic = f"CC {r['license'].upper()} {r.get('license_version') or ''}".strip()
        if r["license"] in ("cc0", "pdm"):
            lic = "CC0" if r["license"] == "cc0" else "Public domain"
        if not licencia_valida(lic) or (r.get("width") or 0) < ANCHO_MINIMO:
            continue
        salida.append({
            "titulo": f"{r.get('title') or 'Imagen'} ({r.get('source')})", "url": r["url"],
            "pagina": r.get("foreign_landing_url"), "ancho": r.get("width"), "alto": r.get("height"),
            "autor": r.get("creator") or "Desconocido", "licencia": lic, "id": r["id"],
        })
    return salida


def registrar_licencia(c, video):
    archivo = ASSETS / "LICENCIAS.csv"
    nuevo = not archivo.exists()
    with open(archivo, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["video", "archivo", "autor", "licencia", "fuente"])
        w.writerow([video, c["titulo"], c["autor"], c["licencia"], c["pagina"]])


def elegir(e, usadas, carpeta):
    """Prueba cada búsqueda en Commons y luego en Openverse; descarga la primera imagen nueva que funcione."""
    imagen = e.get("imagen", "")
    busquedas = e.get("buscar", [])
    fuentes = [lambda: buscar_commons(titulo=imagen)] if imagen else []
    for b in busquedas:
        fuentes += [lambda b=b: buscar_commons(busqueda=b), lambda b=b: buscar_openverse(b)]
    for fuente in fuentes:
        for c in fuente():
            if c["url"] in usadas or c["titulo"] in usadas:
                continue
            contenido = obtener(c["url"], json=False, intentos=2)
            if not contenido or len(contenido) < 20_000:
                continue
            ext = Path(c["url"].split("?")[0]).suffix.lower()
            destino = Path("imagenes") / f"{e['id']:03d}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp') else '.jpg'}"
            (carpeta / destino).write_bytes(contenido)
            return c, destino
    return None, None


def main(carpeta):
    datos = leer_json(carpeta / "escenas.json")
    (carpeta / "imagenes").mkdir(exist_ok=True)
    usadas = set()
    for e in datos["escenas"]:
        if e.get("fuente"):
            usadas |= {e["fuente"]["titulo"], e["fuente"]["url"]}
    for e in datos["escenas"]:
        if e.get("tipo") == "tarjeta":
            continue
        imagen = e.get("imagen", "")
        if imagen and not imagen.startswith("File:"):
            if not (carpeta / imagen).exists():
                sys.exit(f"Escena {e['id']}: no existe la imagen propia {imagen}")
            e["archivo"] = imagen
            continue
        if e.get("archivo") and (carpeta / e["archivo"]).exists():
            continue
        elegido, destino = elegir(e, usadas, carpeta)
        if not elegido:
            log(f"Escena {e['id']}: sin imagen libre para {e.get('buscar')} -> tarjeta de texto")
            e["tipo"] = "tarjeta"
            e.setdefault("tarjeta_texto", datos.get("titulo", ""))
            continue
        usadas |= {elegido["titulo"], elegido["url"]}
        e["archivo"] = destino.as_posix()
        e["fuente"] = elegido
        registrar_licencia(elegido, carpeta.name)
        log(f"Escena {e['id']}: {elegido['titulo'][:70]} ({elegido['licencia']})")
        guardar_json(carpeta / "escenas.json", datos)

    creditos = ["Imágenes con licencia libre:"]
    for e in datos["escenas"]:
        if e.get("fuente"):
            f = e["fuente"]
            creditos.append(f"- {f['titulo'].removeprefix('File:')} — {f['autor']} — {f['licencia']} — {f['pagina']}")
    (carpeta / "creditos.txt").write_text("\n".join(creditos) + "\n", encoding="utf-8")
    guardar_json(carpeta / "escenas.json", datos)
    log("Imágenes listas.")


if __name__ == "__main__":
    main(carpeta_video(sys.argv[1]))
