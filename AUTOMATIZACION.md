# Producción semanal automática (instrucciones para Claude)

Esta tarea la lanza cada semana una tarea programada en una sesión nueva de Claude en la nube.
El usuario **no edita nada**: Claude hace todo y, en el **modo revisión**, solo le pide un "ok" antes de publicar.

## 0. Preparar el entorno (cada vez, la sesión es nueva)
```bash
cd <repo MiCanal>
python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
export SSL_CERT_FILE=/root/.ccr/ca-bundle.crt   # solo en la nube de Claude (proxy)
```
Lee `ESTADO.md` (decisiones, modo de revisión, vídeos publicados) e `ideas/analisis_competencia.md` (estrategia de títulos y miniaturas).

## 1. Elegir el tema
- Coge el siguiente con estado `pendiente` en `ideas/outliers.json` y, si no queda ninguno, en `ideas/cola.csv`.
- Usa título con fórmula probada ("Cómo un niño pobre creó…", "La caída de…", "De X a Y…", listas de 5). Nunca solo el nombre de la marca.
- No repitas tema ni enfoque de los vídeos que ya figuran en `registro/publicados.csv`.

## 2. Investigar y verificar
- Busca en la web fuentes fiables: prensa económica, hemerotecas, la web oficial de la empresa, resoluciones judiciales y Wikipedia solo como punto de partida.
- Comprueba cada fecha, cifra y nombre en al menos 2 fuentes. Si un dato no se puede confirmar, no se usa.
- Con estafas o escándalos: solo hechos probados, sentencias o lo que publicó la prensa, atribuido ("según la Audiencia Nacional…").

## 3. Guion → `videos/NNNN_tema/escenas.json`
- Entre **4.000 y 4.500 palabras** (25–30 min a −6 %), en **90–110 escenas** de 30–55 palabras.
- Estructura: gancho de 30–45 s → tarjeta del título → 5–7 capítulos (cada uno con `"tipo": "tarjeta"` y `"capitulo"`) → cierre con la lección y una llamada a la acción breve.
- Los años en cifras. Cada escena lleva `buscar` (2–3 búsquedas concretas, en inglés si conviene), y `rotulo` y `fecha` cuando aparezca una persona o un año clave.
- Rellena `youtube` (título de 70 caracteres como mucho, descripción con gancho en las 2 primeras líneas, etiquetas y fuentes) y `miniatura` (`ia`: prompt en inglés sin caras de personas reales; `lineas`: 2–4 palabras blanco y dorado; `circulo` y `banda` opcionales).
- Mira `videos/0000_prueba_chupa_chups/escenas.json` como ejemplo del formato.

## 4. Producir
```bash
.venv/bin/python scripts/producir.py videos/NNNN_tema
```
- Revisa **tú** los fotogramas de `qc/` y la lista de imágenes elegidas (`fuente` en escenas.json). Cambia las que no encajen (personas equivocadas, personajes con derechos, cosas sin relación con la escena) con `"imagen": "File:…"` o mejores búsquedas, borra `archivo`/`fuente` de esa escena y vuelve a lanzar el comando.
- Si la duración no está entre 25 y 30 min, ajusta el guion.

## 5. Miniatura
- Genera la imagen base con `scripts/ia_imagen.py` (prompt de `miniatura.ia`) y compón la miniatura con `plantillas.miniatura_drama`; guárdala como `videos/NNNN_tema/miniatura.png`.
- Mírala: el texto tiene que leerse en pequeño y el círculo tiene que señalar algo que tenga sentido.

## 6. Alojar el vídeo (Metricool necesita una URL pública)
```bash
gh release create NNNN_tema videos/NNNN_tema/video_final.mp4 videos/NNNN_tema/miniatura.png \
  --repo <usuario>/MiCanal-videos --title "<título>" --notes ""
```
La URL queda así: `https://github.com/<usuario>/MiCanal-videos/releases/download/NNNN_tema/video_final.mp4`

## 7. Publicar con Metricool
- `getBrandSettings` → `blogId` de la marca del canal correcto (ver `ESTADO.md`, "Canal de publicación").
- `getBestTimeToPostByNetwork` (youtube, próximos 7 días) → elige la mejor franja.
- **Modo revisión (`ESTADO.md` → `modo: revision`)**: antes de programar, enseña al usuario la miniatura, el título, la descripción y el enlace del vídeo, y espera su "ok". Si pide cambios, hazlos y vuelve a preguntar.
- **Modo automático**: programa directamente.
- `createScheduledPost` con `providers: [{"network":"youtube"}]`, `media: [URL]`, `videoThumbnailUrl: URL de miniatura.png`,
  `youtubeData: {"title": …, "type": "video", "privacy": "public", "madeForKids": false, "category": "EDUCATION", "tags": […], "isAiGeneratedContent": false}`, y `text` = descripción.

## 8. Registrar
- Marca el tema como `publicado` en la cola. Añade una línea a `registro/publicados.csv` (fecha, carpeta, título, fecha programada, plannerUrl).
- Actualiza `ESTADO.md` y haz commit y push al repositorio (los vídeos pesados no se suben al repositorio, solo a la release).
- Si algo falla, apúntalo en `registro/ERRORES.md`, explica al usuario qué ha pasado y no publiques nada a medias.

## 9. Una vez al mes: aprender de los datos
Con `getAnalyticsDataByMetrics` (YTVP06 vistas, YTVP07 minutos vistos, YTVP08 duración media, YTEV05 suscriptores ganados), compara los vídeos y ajusta los títulos, las miniaturas y los temas de la cola. Apunta las conclusiones en `ESTADO.md`.
