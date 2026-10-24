"""Plantillas visuales con Pillow: lienzo para el movimiento, tarjetas de capítulo y miniaturas."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

# Fuentes de respaldo por sistema (Linux / Windows / Mac)
FUENTES_NEGRITA = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
FUENTES_NORMAL = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]

MARGEN_MOVIMIENTO = 1.12  # el lienzo es un 12 % mayor que el vídeo para poder desplazarse


def fuente(preferida, respaldo, tam):
    for ruta in [preferida, *respaldo]:
        if ruta and Path(ruta).exists():
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default(tam)


def color(hexa):
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def lienzo(ruta_imagen, ancho, alto, destino):
    """Imagen centrada sobre su propia versión desenfocada, a tamaño 'ancho*margen'."""
    w, h = round(ancho * MARGEN_MOVIMIENTO), round(alto * MARGEN_MOVIMIENTO)
    w, h = w - w % 2, h - h % 2
    img = ImageOps.exif_transpose(Image.open(ruta_imagen)).convert("RGB")
    fondo = ImageOps.fit(img, (w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    fondo = Image.blend(fondo, Image.new("RGB", (w, h), (0, 0, 0)), 0.45)
    escala = min(w / img.width, h / img.height)
    # si la imagen es casi 16:9 la dejamos llenar el lienzo; si no, cabe entera sobre el fondo
    if abs(img.width / img.height - w / h) < 0.12:
        frente = ImageOps.fit(img, (w, h), Image.LANCZOS)
    else:
        frente = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    fondo.paste(frente, ((w - frente.width) // 2, (h - frente.height) // 2))
    fondo.save(destino, quality=92)
    return destino


def _ajustar_texto(draw, texto, font, ancho_max):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=font) <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def tarjeta(titulo, subtitulo, estilo, ancho, alto, destino):
    """Tarjeta de capítulo: fondo oscuro, línea dorada, título grande."""
    w, h = round(ancho * MARGEN_MOVIMIENTO), round(alto * MARGEN_MOVIMIENTO)
    w, h = w - w % 2, h - h % 2
    img = Image.new("RGB", (w, h), color(estilo["color_fondo"]))
    d = ImageDraw.Draw(img)
    # viñeta suave
    for i in range(0, 300, 6):
        d.rectangle([i, i, w - i, h - i], outline=tuple(max(0, c - 18 + i // 18) for c in color(estilo["color_fondo"])), width=6)
    f_tit = fuente(estilo.get("fuente_titulos"), FUENTES_NEGRITA, round(alto * 0.085))
    f_sub = fuente(estilo.get("fuente_texto"), FUENTES_NORMAL, round(alto * 0.04))
    lineas = _ajustar_texto(d, titulo.upper(), f_tit, ancho * 0.75)
    alto_linea = round(alto * 0.105)
    bloque = alto_linea * len(lineas) + (round(alto * 0.08) if subtitulo else 0)
    y = (h - bloque) // 2
    acento = color(estilo["color_acento"])
    d.rectangle([w // 2 - 90, y - 50, w // 2 + 90, y - 42], fill=acento)
    for linea in lineas:
        d.text((w // 2, y), linea, font=f_tit, fill=color(estilo["color_texto"]), anchor="ma")
        y += alto_linea
    if subtitulo:
        d.text((w // 2, y + 15), subtitulo, font=f_sub, fill=acento, anchor="ma")
    img.save(destino, quality=95)
    return destino


def miniatura(ruta_imagen, texto, estilo, destino, ancho=1280, alto=720):
    """Miniatura 1280x720: imagen oscurecida a la derecha, texto grande con contorno a la izquierda."""
    img = ImageOps.fit(ImageOps.exif_transpose(Image.open(ruta_imagen)).convert("RGB"), (ancho, alto), Image.LANCZOS)
    degradado = Image.linear_gradient("L").rotate(90).resize((ancho, alto))
    negro = Image.new("RGB", (ancho, alto), (0, 0, 0))
    img = Image.composite(img, negro, degradado.point(lambda v: min(255, 60 + v)))
    d = ImageDraw.Draw(img)
    palabras = texto.upper().split()
    tam = 150
    while tam > 60:
        f = fuente(estilo.get("fuente_titulos"), FUENTES_NEGRITA, tam)
        lineas = _ajustar_texto(d, " ".join(palabras), f, ancho * 0.62)
        if len(lineas) <= 3 and tam * 1.1 * len(lineas) < alto * 0.8:
            break
        tam -= 8
    y = (alto - round(tam * 1.1) * len(lineas)) // 2
    for i, linea in enumerate(lineas):
        ultima = i == len(lineas) - 1 and len(lineas) > 1  # la última línea va en el color de acento
        d.text((50, y), linea, font=f, fill=color(estilo["color_acento" if ultima else "color_texto"]),
               stroke_width=8, stroke_fill=(0, 0, 0))
        y += round(tam * 1.1)
    img.save(destino)
    return destino


FUENTES_PROPIAS = Path(__file__).resolve().parent.parent / "assets" / "fuentes"


def _fuente_variable(nombre, tam, peso):
    ruta = FUENTES_PROPIAS / nombre
    if not ruta.exists():
        return fuente(None, FUENTES_NEGRITA, tam)
    f = ImageFont.truetype(str(ruta), tam)
    f.set_variation_by_axes([peso])
    return f


def miniatura_drama(ruta_imagen, lineas, estilo, destino, posicion="abajo", circulo=None, banda=None,
                    ancho=1280, alto=720):
    """Miniatura estilo documental dramático (como los canales de "imperios caídos"):
    foto a sangre con contraste alto, texto en mayúsculas con serifa en blanco y dorado, y
    opcionalmente un círculo rojo que señala algo o una banda superior con letra gruesa.

    lineas: [["EL ERROR DE", "blanco"], ["30.000 MILLONES", "acento"]]
    circulo: [x, y, ancho, alto] en proporciones 0-1 (elipse roja)
    banda: texto para una franja oscura arriba (estilo "CÓMO SE CREÓ ...")
    """
    from PIL import ImageEnhance

    img = ImageOps.fit(ImageOps.exif_transpose(Image.open(ruta_imagen)).convert("RGB"), (ancho, alto), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Sharpness(img).enhance(1.6)

    # oscurecer la zona del texto para que se lea
    sombra = Image.new("L", (ancho, alto), 0)
    ds = ImageDraw.Draw(sombra)
    if posicion == "abajo":
        for y in range(alto // 2, alto):
            ds.line([(0, y), (ancho, y)], fill=int(200 * (y - alto / 2) / (alto / 2)))
    else:
        for y in range(0, alto // 2):
            ds.line([(0, y), (ancho, y)], fill=int(200 * (1 - y / (alto / 2))))
    img = Image.composite(Image.new("RGB", (ancho, alto), (0, 0, 0)), img, sombra)
    d = ImageDraw.Draw(img)

    if circulo:
        x, y, w, h = circulo
        caja = [x * ancho, y * alto, (x + w) * ancho, (y + h) * alto]
        d.ellipse(caja, outline=(0, 0, 0), width=16)
        d.ellipse(caja, outline=(230, 20, 20), width=10)

    if banda:
        f = _fuente_variable("Montserrat.ttf", 64, 900)
        tw = d.textlength(banda.upper(), font=f)
        d.rectangle([ancho / 2 - tw / 2 - 40, 28, ancho / 2 + tw / 2 + 40, 128], fill=(15, 15, 18))
        d.text((ancho / 2, 78), banda.upper(), font=f, fill=(255, 255, 255), anchor="mm")

    colores = {"blanco": color(estilo["color_texto"]), "acento": color(estilo["color_acento"]), "rojo": (230, 30, 30)}
    tam = 104
    while tam > 50:
        f = _fuente_variable("PlayfairDisplay.ttf", tam, 900)
        if all(d.textlength(t.upper(), font=f) < ancho * 0.86 for t, _ in lineas):
            break
        tam -= 4
    alto_linea = round(tam * 1.08)
    y = alto - 50 - alto_linea * len(lineas) if posicion == "abajo" else 40 + (110 if banda else 0)
    for texto, col in lineas:
        d.text((52, y + 6), texto.upper(), font=f, fill=(0, 0, 0))  # sombra
        d.text((46, y), texto.upper(), font=f, fill=colores.get(col, colores["blanco"]),
               stroke_width=5, stroke_fill=(0, 0, 0))
        y += alto_linea
    img.save(destino)
    return destino
