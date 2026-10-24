# ESTADO DEL CANAL (léelo siempre al empezar una sesión)

_Última actualización: 2026-10-24 (fin de la primera sesión)_

## ⚡ RESUMEN PARA EMPEZAR (lo más reciente manda sobre lo de más abajo)
- **El usuario quiere todo automatizado y que se le moleste lo mínimo.** Pregunta solo lo imprescindible y actúa.
- **Publicación: API de YouTube (Google Cloud), NO Metricool.** Metricool gratis solo admite 1 marca, y la cuenta conectada a Claude es la de The Nations History (otro canal del usuario, UC8JkloSi2Y20MpvFGTFL-Jg: **no tocarla nunca**).
- **Autorización hecha y probada** sobre el canal correcto UCrxZm4ofcvqjG3UUg0-nT0Q, con el proyecto de Google Cloud `marcasconhistoria`.
  - ⚠️ **El repositorio `MiCanal` es PÚBLICO**: las credenciales NUNCA van al repositorio (GitHub ya bloqueó un intento).
  - Las credenciales llegan como variables de entorno del entorno en la nube: `YOUTUBE_CLIENT_SECRET_JSON` y `YOUTUBE_TOKEN_JSON` (el contenido completo de cada JSON). `subir.py` las convierte en archivos solo.
  - Si no están: el usuario sube `client_secret.json` al chat y se repite `scripts/autorizar.py` (enlace → "Permitir" → pegar la URL de localhost).
  - Subida probada el 24/10: se subió un vídeo en privado y otro como oculto (unlisted), y se borraron. El oculto siguió oculto tras procesarse, así que de momento no se ve el bloqueo en privado de los proyectos sin verificar. Hay que confirmarlo con el primer vídeo real.
  - **Miniatura personalizada: error 403.** Falta que el usuario verifique el canal con el teléfono (youtube.com/verify). Mientras tanto, subir sin miniatura personalizada y reintentar `thumbnails.set` en la siguiente ejecución.
- **Ya aplicado por API en el canal:** el banner documental, la descripción, las palabras clave y el país ES.
- **Pendiente manual del usuario** (la API no lo permite): nombre "Marcas con Historia", identificador @MarcasConHistoriaES, foto de perfil `marca/logo_800.png`, y verificación por teléfono.
- **Siguiente paso:** crear la tarea programada semanal (sesión nueva en cada ejecución, con este repositorio) que siga `AUTOMATIZACION.md`, publicando con `scripts/subir.py --programar` en lugar de Metricool. Primer vídeo: "Cómo un Recadero de 14 Años Creó Zara" (`ideas/outliers.json` → `zara_recadero`).
  - **Modo revisión:** antes de programar cada vídeo, se le enseña al usuario y se espera su "ok". Las 2–3 primeras semanas.
- `scripts/alojar.py` y el repositorio `MiCanal-videos` solo hacen falta si algún día se usa Metricool; con la API de YouTube no se necesitan.

## Ficha del canal
| | |
|---|---|
| **Nombre** | Marcas con Historia · @MarcasConHistoriaES · canal UCrxZm4ofcvqjG3UUg0-nT0Q |
| **Nicho** | Historia de marcas y empresas: origen, auge, quiebras y escándalos |
| **Público** | España y Latinoamérica, adultos interesados en negocios e historia |
| **Idioma** | Español |
| **Formato** | Solo vídeos largos de 25–30 min (sin Shorts por ahora) |
| **Estilo visual** | Documental con imágenes libres que se mueven despacio, tarjetas de capítulo oscuras con línea dorada y rótulos con nombre y año |
| **Paleta** | Fondo `#101418`, acento dorado `#E8B04A`, texto blanco |
| **Tipografía** | DejaVu Sans / Arial en negrita |
| **Voz** | edge-tts `es-ES-AlvaroNeural`, velocidad −6 % y tono −4 Hz ("Álvaro documental", elegida por el usuario entre 20 muestras) |
| **Tono** | Narrador de documental: cercano, con ritmo y sin relleno |

## Estructura típica de un vídeo (unas 4.000–4.500 palabras ≈ 27–30 min)
1. **Gancho** (30–45 s): el momento más dramático o sorprendente, sin título todavía.
2. **Tarjeta del título** y presentación de lo que viene.
3. **5–7 capítulos**, cada uno con su tarjeta: orígenes → la idea → el despegue → la expansión → la crisis o el escándalo → cómo está hoy.
4. **Cierre**: la lección que deja la historia, más una llamada corta a suscribirse y al siguiente vídeo.
- Escenas de 30–60 palabras (unos 15–25 s) con una imagen cada una: entre 80 y 110 escenas por vídeo.
- Los años van en cifras en el guion (la voz los lee bien y los subtítulos los muestran como "1958").

## Cómo se produce un vídeo
1. Claude elige el tema de `ideas/cola.csv`, investiga y verifica los datos (anota las fuentes).
2. Claude escribe `videos/NNNN_tema/escenas.json`: guion por escenas, búsquedas de imagen, rótulos, capítulos y datos para YouTube.
3. Un solo comando: `python scripts/producir.py videos/NNNN_tema` (en Windows, `producir_windows.bat NNNN_tema`).
   Hace la voz, las imágenes (Wikimedia Commons, o Openverse si Commons falla), el montaje, el control de calidad, la miniatura y `metadata.json`.
4. **Claude revisa los fotogramas** en `qc/` y las imágenes elegidas. Las que no encajan las cambia, poniendo `"imagen": "File:..."` en la escena o una imagen propia, y vuelve a lanzar el comando (solo rehace lo que ha cambiado).
5. Se sube: `python scripts/subir.py videos/NNNN_tema --programar "AAAA-MM-DD HH:MM"`.

## Hecho ✅
- [x] Entorno comprobado y herramientas instaladas (en la nube de Claude: Python 3.13, FFmpeg 6.1, 4 núcleos, sin GPU)
- [x] Decisiones: nicho, voz de España y solo vídeos largos
- [x] Scripts completos: `voz.py`, `imagenes.py`, `montaje.py`, `calidad.py`, `metadatos.py`, `producir.py`, `subir.py`
- [x] **Vídeo de prueba** (`videos/0000_prueba_chupa_chups`, 47 s) completo hasta el render: control de calidad OK y −14,5 LUFS
- [x] Cola de 26 ideas en `ideas/cola.csv`
- [x] Voz cambiada a "Álvaro documental" y vídeo de prueba regenerado con ella
- [x] Logo (`marca/logo_800.png`) y dos banners: sobrio (`banner_2560x1440.png`) y documental con fondo de IA (`banner_documental_2560x1440.png`). Se regeneran con `python scripts/marca.py --ia`
- [x] Análisis de competencia (Historias de Negocios e Imperios Olvidados) en `ideas/analisis_competencia.md`
- [x] 6 vídeos adaptados de sus outliers (`ideas/outliers.json`) con título, descripción y miniatura (`ideas/miniaturas/`)
- [x] Miniaturas de estilo dramático: `scripts/generar_miniaturas.py` (imagen de IA de Pollinations + plantilla `miniatura_drama`)

## Rendimiento medido
- En la nube (4 núcleos): el montaje tardó 26 s para 47 s de vídeo, unas 0,55× tiempo real. **Un vídeo de 30 min tardaría unos 17 min.**
- En un portátil normal puede tardar el doble (30–40 min). Se puede dejar de noche sin problema.
- La voz tarda 1–3 s por escena y las imágenes 3–5 s por escena (Wikimedia limita la velocidad), así que cada vídeo suma unos 5–10 min más.

## Falta / siguiente paso ⏳
- [ ] **Usuario:** elegir el nombre del canal
- [ ] **Usuario:** crear la cuenta de Google y el canal, y verificarlo con el teléfono
- [ ] **Usuario:** crear el proyecto en Google Cloud, activar YouTube Data API v3, configurar OAuth "Externo" (añadirse como usuario de prueba), crear credenciales de "aplicación de escritorio" y descargar `client_secret.json` a esta carpeta
- [ ] Pasar el proyecto al portátil y ejecutar `instalar_windows.bat`
- [ ] Autorizar YouTube una vez: `python scripts/subir.py --autorizar`
- [ ] Subir la prueba como **privada** y comprobar si la API deja publicar en público
- [ ] Música de fondo: descargar 3–5 pistas tranquilas de YouTube Audio Library o Pixabay Music en `assets/musica/` (si la carpeta está vacía, el vídeo sale sin música)
- [ ] Banner, foto de perfil y descripción del canal
- [ ] Primer vídeo real de 25–30 min

## Avisos importantes
- **Publicación por API:** según la política que conozco, los proyectos de Google sin verificar suben los vídeos bloqueados en **privado**. Mientras no se pase la auditoría de YouTube API Services, subimos como privado o programado y el usuario pulsa "Publicar" en YouTube Studio (un clic). Hay que comprobarlo con la primera subida.
- **edge-tts** usa el servicio de voz de Microsoft Edge de forma no oficial. Es gratis y funciona bien, pero podría dejar de funcionar algún día; en ese caso, plan B con Piper (offline).
- **Contenido "inauténtico":** cada vídeo tiene que aportar algo real (investigación, datos verificados, un enfoque propio), con estructura y visuales distintos entre vídeos. Nada de relleno.
- **Datos y personas reales:** verificar las cifras y citar las fuentes en la descripción. Con escándalos y estafas, ceñirse a hechos probados o sentencias y no acusar sin respaldo.
- **Imágenes:** solo licencias que permiten uso comercial (dominio público, CC0, CC BY, CC BY-SA). Los créditos van solos en la descripción. Revisar que no salgan personajes con derechos (Disney, etc.) aunque la foto sea libre.
- **Voz sintética:** narrar con TTS no obliga a marcar "contenido alterado o sintético" (eso es para contenido realista que pueda engañar). Si algún día se usan imágenes de IA realistas, hay que poner `contenido_sintetico: true`.
- **Cuota de la API:** unas 6 subidas al día como máximo en el nivel gratuito.

## Estrategia de contenidos (sale del análisis de competencia)
- Dos series fijas: **"Cómo un niño pobre creó…"** (superación del fundador) y **"La caída de…"** (colapso con cifras), más listas de 5 y estafas.
- El título nunca es solo el nombre de la marca: lleva contraste, una cifra o un secreto.
- Nuestro hueco: marcas españolas y latinoamericanas.
- Miniatura: imagen dramática de IA, 2–4 palabras con serifa en blanco y dorado, círculo rojo cuando ayude.
- No copiar sus nombres, logos ni frases: se adapta la fórmula, no la marca de otro canal.
- Imágenes de IA: no generar con IA la cara de personas reales (Ortega, Rosalía Mera…). Usar personajes anónimos, imágenes de espaldas o fotos reales con licencia.
- Pollinations gratis: 1 imagen cada ~45 s, calidad justa y marca de agua pequeña en la esquina. Para más calidad: crear la imagen en Bing Image Creator, Gemini o ChatGPT (gratis), guardarla como `ideas/miniaturas/<id>_base.jpg` y relanzar `generar_miniaturas.py`. O conseguir una clave gratuita de Pollinations y ponerla en `.env` como `POLLINATIONS_KEY`.

## Opciones de nombre (pendiente de elegir)
1. **Marcas con Historia**
2. **El Origen de las Marcas**
3. **Imperios de Empresa**
4. **Detrás de la Marca**
5. **Auge y Caída**

## Notas técnicas
- En la nube de Claude hace falta `SSL_CERT_FILE=/root/.ccr/ca-bundle.crt` (por el proxy). En el portátil no.
- Desde la nube, Wikimedia a veces responde 429 (límite de peticiones): el script cambia solo a Openverse.
- Si cambias una escena y vuelves a lanzar el comando, solo se rehace lo que ha cambiado (voz, imagen o escena).

## Automatización (decidida el 24/10/2026)
- **Dónde:** en la nube de Claude, con una tarea programada semanal que abre una sesión nueva y sigue `AUTOMATIZACION.md`.
- **Publicación:** con Metricool (aplicación verificada: publica en público sin auditoría de la API). El vídeo se aloja en las releases de un repositorio público `MiCanal-videos`.
- **modo: revision**. Las 2–3 primeras semanas el usuario da el "ok" antes de publicar; después se cambia a `modo: automatico`.
- **Canal de publicación:** UCrxZm4ofcvqjG3UUg0-nT0Q (antes "aitor cortijo escamilla", vacío). NO es el canal que tiene Metricool ahora (UC8JkloSi2Y20MpvFGTFL-Jg). Antes de publicar, comprueba con getBrandSettings que `youtubeData` = UCrxZm4ofcvqjG3UUg0-nT0Q.
- El usuario ha autorizado que Claude configure el canal (nombre, logo, banner, descripciones). Como Claude no tiene acceso a YouTube Studio, se le ha dado todo listo para pegar en `marca/CANAL_YOUTUBE.md`.
- **Pasos del usuario (una vez):**
  - [ ] Conectar el canal correcto en Metricool
  - [ ] Conectar GitHub a Claude (https://claude.ai/connect-github) y crear dos repositorios vacíos: `MiCanal` (privado) y `MiCanal-videos` (público)
  - [ ] Pegar en YouTube Studio lo de `marca/CANAL_YOUTUBE.md` (nombre, @handle, logo, banner, descripción y palabras clave) y verificar el canal con el teléfono
- **Pasos de Claude cuando el usuario termine:** conectar el repositorio, subir el código, probar la release y Metricool con el vídeo de prueba en borrador, y crear la tarea programada semanal (con el conector de Metricool y avisos al móvil).

## Metricool (actualizado el 24/10/2026)
- Añadir una segunda marca en la cuenta de Metricool de The Nations History es de pago, y el usuario lo quiere gratis.
- Solución elegida: una **segunda cuenta gratuita de Metricool** solo para Marcas con Historia, con el conector de Claude reconectado a esa cuenta.
- El usuario dice que ha reconectado el conector, pero la sesión del 24/10 seguía viendo la cuenta antigua (canalyoutube123456789@gmail.com, brand 7594539, The Nations History).
- **Al empezar la próxima sesión:** ejecutar `getBrandSettings` y comprobar que aparece `youtubeData = UCrxZm4ofcvqjG3UUg0-nT0Q`. Si sigue saliendo la cuenta antigua, el usuario tiene que cerrar sesión en metricool.com, desconectar y volver a conectar el conector iniciando sesión con la cuenta nueva.
- Siguientes pasos: conectar GitHub (repos `MiCanal` privado y `MiCanal-videos` público) → subir el proyecto → prueba en borrador con Metricool → tarea semanal.


## Situación al cerrar la sesión del 24/10/2026 (LEER PRIMERO)
- ✅ Proyecto en GitHub: `canalyoutube12345678-afk/MiCanal` (privado, rama `main`).
- ✅ Alojamiento de vídeos probado: `canalyoutube12345678-afk/MiCanal-videos` (público). `scripts/alojar.py` sube a la rama `video/<carpeta>` y la URL raw funciona (200). Las releases de GitHub NO funcionan en las sesiones en la nube (403).
- ❌ **Metricool:** al terminar la sesión seguía viéndose solo la cuenta antigua (brand 7594539, The Nations History, UC8JkloSi2Y20MpvFGTFL-Jg), aunque el usuario dice que reconectó el conector con la cuenta nueva.
- **PRIMER PASO de la nueva sesión:** `getBrandSettings`. Hay que encontrar una marca con `youtubeData = UCrxZm4ofcvqjG3UUg0-nT0Q`.
  - Si aparece: prueba con `createScheduledPost` en **borrador** (`draft: true`) usando las URLs de `videos/0000_prueba_chupa_chups/metadata.json` → `alojamiento`. Comprobar que se ve en el planificador de Metricool y borrarla después. Luego crear la tarea programada semanal (nueva sesión en cada ejecución, con el repositorio MiCanal, el conector de Metricool y aviso push) con la instrucción "Sigue AUTOMATIZACION.md".
  - Si NO aparece: el conector sigue en la cuenta antigua. El usuario tiene que cerrar sesión en metricool.com, entrar con la cuenta nueva y reconectar el conector (mejor en una ventana de incógnito).
- **No tocar nunca** la marca de The Nations History.
- Primer vídeo real previsto: "Cómo un Recadero de 14 Años Creó Zara" (`ideas/outliers.json`, id `zara_recadero`).
