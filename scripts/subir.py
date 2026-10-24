"""Paso 6: sube el vídeo a YouTube con la API oficial (vídeo + miniatura + metadatos).

La primera vez abre el navegador para que pulses "Permitir"; después guarda token.json y ya no pregunta.
Por defecto sube como PRIVADO. Para programarlo: --programar "2026-11-03 18:00" (hora de Madrid).

Uso:
  python scripts/subir.py videos/<carpeta>                      # privado
  python scripts/subir.py videos/<carpeta> --programar "2026-11-03 18:00"
  python scripts/subir.py videos/<carpeta> --publico            # solo cuando la API esté verificada
  python scripts/subir.py --autorizar                           # solo autorizar la cuenta
"""
import argparse
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from comun import RAIZ, REGISTRO, carpeta_video, config, guardar_json, leer_json, log

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
CLIENTE = RAIZ / "client_secret.json"
TOKEN = RAIZ / "token.json"


def servicio():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    # en la nube, las credenciales llegan como variables de entorno (nunca en el repositorio, que es público)
    for archivo, variable in ((CLIENTE, "YOUTUBE_CLIENT_SECRET_JSON"), (TOKEN, "YOUTUBE_TOKEN_JSON")):
        if not archivo.exists() and os.environ.get(variable):
            archivo.write_text(os.environ[variable], encoding="utf-8")
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if TOKEN.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not CLIENTE.exists():
            sys.exit(f"Falta {CLIENTE.name}: descárgalo de Google Cloud (ver ESTADO.md, paso 'Google Cloud').")
        creds = InstalledAppFlow.from_client_secrets_file(CLIENTE, SCOPES).run_local_server(port=0)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def subir(carpeta, programar=None, publico=False, forzar=False):
    from googleapiclient.http import MediaFileUpload

    cfg = config()
    meta = leer_json(carpeta / "metadata.json")
    if meta.get("youtube_id") and not forzar:
        sys.exit(f"Este vídeo ya está subido: https://youtu.be/{meta['youtube_id']} (usa --forzar para repetir)")

    estado = {
        "privacyStatus": "public" if publico else "private",
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": bool(meta.get("contenido_sintetico")),
    }
    if programar:
        zona = ZoneInfo(config()["canal"].get("zona_horaria", "Europe/Madrid"))
        cuando = datetime.strptime(programar, "%Y-%m-%d %H:%M").replace(tzinfo=zona)
        if cuando <= datetime.now(zona):
            sys.exit("La fecha de publicación tiene que ser futura.")
        estado.update(privacyStatus="private", publishAt=cuando.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"))

    cuerpo = {
        "snippet": {
            "title": meta["titulo"], "description": meta["descripcion"], "tags": meta.get("etiquetas", []),
            "categoryId": meta.get("categoria", cfg["youtube"]["categoria"]),
            "defaultLanguage": meta.get("idioma", "es"), "defaultAudioLanguage": meta.get("idioma", "es"),
        },
        "status": estado,
    }
    yt = servicio()
    media = MediaFileUpload(str(carpeta / "video_final.mp4"), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    peticion = yt.videos().insert(part="snippet,status", body=cuerpo, media_body=media)
    respuesta = None
    while respuesta is None:
        progreso, respuesta = peticion.next_chunk()
        if progreso:
            log(f"  subido {progreso.progress() * 100:.0f} %")
    video_id = respuesta["id"]
    log(f"Vídeo subido: https://youtu.be/{video_id} (estado: {respuesta['status']['privacyStatus']})")

    miniatura = carpeta / "miniatura.png"
    if miniatura.exists():
        try:
            yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(miniatura), mimetype="image/png")).execute()
            log("Miniatura puesta.")
        except Exception as e:  # falla si el canal no está verificado por teléfono
            log(f"AVISO: no se pudo poner la miniatura ({e}). ¿Está el canal verificado con el teléfono?")

    meta.update(youtube_id=video_id, youtube_estado=respuesta["status"]["privacyStatus"],
                youtube_publicacion=estado.get("publishAt"), youtube_subido=datetime.now().isoformat(timespec="seconds"))
    guardar_json(carpeta / "metadata.json", meta)
    REGISTRO.mkdir(exist_ok=True)
    with open(REGISTRO / "subidas.csv", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M},{carpeta.name},{video_id},{estado['privacyStatus']},{estado.get('publishAt', '')}\n")
    return video_id


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta", nargs="?")
    ap.add_argument("--programar", help='fecha y hora de Madrid, p. ej. "2026-11-03 18:00"')
    ap.add_argument("--publico", action="store_true")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--autorizar", action="store_true")
    a = ap.parse_args()
    if a.autorizar:
        servicio()
        log("Cuenta autorizada. token.json guardado.")
    elif a.carpeta:
        subir(carpeta_video(a.carpeta), a.programar, a.publico, a.forzar)
    else:
        ap.print_help()
