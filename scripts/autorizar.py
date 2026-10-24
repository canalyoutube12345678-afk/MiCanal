"""Autoriza el canal de YouTube sin navegador en esta máquina (sirve en la nube).

1) python scripts/autorizar.py            -> imprime un enlace: ábrelo, elige el canal y pulsa "Permitir"
2) El navegador acabará en una página que no carga (http://localhost/...): copia esa dirección entera
3) python scripts/autorizar.py "<dirección copiada>"   -> guarda token.json

token.json no se sube nunca al repositorio (.gitignore).
"""
import json
import sys

from google_auth_oauthlib.flow import Flow

from comun import RAIZ, log
from subir import CLIENTE, SCOPES, TOKEN

REDIRECCION = "http://localhost:8765/"
ESTADO = RAIZ / ".oauth_pendiente.json"


def flujo():
    return Flow.from_client_secrets_file(str(CLIENTE), SCOPES, redirect_uri=REDIRECCION)


def main():
    if len(sys.argv) < 2:
        f = flujo()
        url, estado = f.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
        ESTADO.write_text(json.dumps({"state": estado, "verifier": f.code_verifier}))
        log(url)
        return
    pendiente = json.loads(ESTADO.read_text())
    f = flujo()
    f.code_verifier = pendiente["verifier"]
    f.fetch_token(authorization_response=sys.argv[1].replace("http://", "https://", 1))
    TOKEN.write_text(f.credentials.to_json(), encoding="utf-8")
    ESTADO.unlink()
    log("Autorizado. token.json guardado.")


if __name__ == "__main__":
    main()
