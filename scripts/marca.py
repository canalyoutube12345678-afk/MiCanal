"""Genera la imagen del canal en marca/: logo (800x800), banner sobrio y banner documental con fondo de IA.

Toma el nombre y los colores de config.yaml.
Uso: python scripts/marca.py        (añade --ia para generar el fondo del banner documental)
"""
import math
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from comun import ASSETS, RAIZ, config, log
from plantillas import color

SERIF = ASSETS / "fuentes" / "PlayfairDisplay.ttf"
SANS = ASSETS / "fuentes" / "Montserrat.ttf"


def fuente(ruta, tam, peso):
    f = ImageFont.truetype(str(ruta), tam)
    f.set_variation_by_axes([peso])
    return f


def iniciales(nombre):
    palabras = [p for p in nombre.split() if p.lower() not in ("de", "del", "la", "las", "el", "los", "con", "y")]
    return "".join(p[0].upper() for p in palabras[:2])


def fondo(ancho, alto, base, brillo=28):
    """Fondo oscuro con un halo de luz suave en el centro y grano fino."""
    img = Image.new("RGB", (ancho, alto), base)
    halo = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(halo).ellipse([ancho * 0.2, alto * 0.05, ancho * 0.8, alto * 0.95], fill=255)
    halo = halo.filter(ImageFilter.GaussianBlur(min(ancho, alto) * 0.2))
    claro = Image.new("RGB", (ancho, alto), tuple(min(255, c + brillo) for c in base))
    return Image.composite(claro, img, halo)


def logo(cfg, destino, tam=800):
    est = cfg["estilo"]
    oro, base = color(est["color_acento"]), color(est["color_fondo"])
    s = tam * 2  # se dibuja al doble y se reduce: bordes más finos
    img = fondo(s, s, base, 22)
    d = ImageDraw.Draw(img)
    c = s / 2
    # YouTube recorta el logo en círculo: todo dentro del 80 % central
    for r, w in ((s * 0.40, 10), (s * 0.375, 4)):
        d.ellipse([c - r, c - r, c + r, c + r], outline=oro, width=w)
    letras = iniciales(cfg["canal"]["nombre"])
    f = fuente(SERIF, round(s * 0.30), 800)
    d.text((c, c - s * 0.015), letras, font=f, fill=oro, anchor="mm")
    # filete y pequeña leyenda
    d.line([c - s * 0.12, c + s * 0.17, c + s * 0.12, c + s * 0.17], fill=oro, width=5)
    f2 = fuente(SANS, round(s * 0.034), 600)
    d.text((c, c + s * 0.23), "  ".join("HISTORIAS DE EMPRESA".split()), font=f2, fill=(220, 220, 220), anchor="mm")
    img.resize((tam, tam), Image.LANCZOS).save(destino)


def banner(cfg, destino, ancho=2560, alto=1440):
    est = cfg["estilo"]
    oro, base, blanco = color(est["color_acento"]), color(est["color_fondo"]), color(est["color_texto"])
    img = fondo(ancho, alto, base, 30)
    d = ImageDraw.Draw(img)
    # líneas finas tipo "gráfico bursátil" muy tenues de fondo
    for k, fase in enumerate((0.0, 1.7, 3.1)):
        pts = [(x, alto * 0.5 + math.sin(x / 260 + fase) * 90 + math.sin(x / 97 + fase * 2) * 35 - (x - ancho / 2) * 0.08)
               for x in range(0, ancho + 20, 20)]
        d.line(pts, fill=tuple(c + 14 + k * 4 for c in base), width=3)

    # zona segura (visible en todos los dispositivos): 1546x423 centrada
    cx, cy = ancho / 2, alto / 2
    nombre = cfg["canal"]["nombre"]
    palabras = nombre.upper().split()
    principal, final = " ".join(palabras[:-1]), palabras[-1]
    tam = 150
    while True:  # que el nombre quepa en la zona segura con margen
        f = fuente(SERIF, tam, 800)
        w1 = d.textlength(principal + " ", font=f)
        w2 = d.textlength(final, font=f)
        if w1 + w2 <= 1440 or tam <= 70:
            break
        tam -= 4
    x = cx - (w1 + w2) / 2
    y = cy - 40
    d.text((x, y), principal + " ", font=f, fill=blanco, anchor="ls")
    d.text((x + w1, y), final, font=f, fill=oro, anchor="ls")

    d.line([cx - 330, cy + 15, cx - 30, cy + 15], fill=oro, width=3)
    d.line([cx + 30, cy + 15, cx + 330, cy + 15], fill=oro, width=3)
    d.rectangle([cx - 8, cy + 7, cx + 8, cy + 23], fill=oro)
    f2 = fuente(SANS, 46, 500)
    d.text((cx, cy + 85), cfg["canal"].get("lema", ""), font=f2, fill=(225, 225, 225), anchor="mm")
    f3 = fuente(SANS, 34, 700)
    d.text((cx, cy + 165), cfg["canal"].get("frecuencia", "").upper(), font=f3, fill=oro, anchor="mm")
    img.save(destino)


PROMPT_FONDO_BANNER = (
    "wide panoramic view of an abandoned industrial district at dusk, ruined factories and old department "
    "store buildings on the left and right edges, empty dark sky and cracked concrete wall in the center, "
    "smokestacks, desaturated tones, stormy dramatic clouds"
)


def banner_documental(cfg, fondo_ia, destino, ancho=2560, alto=1440):
    """Banner estilo documental: fondo de IA (ruinas industriales) + nombre grande en el centro."""
    from PIL import ImageEnhance

    est = cfg["estilo"]
    oro, blanco = color(est["color_acento"]), color(est["color_texto"])
    img = Image.open(fondo_ia).convert("RGB").resize((ancho, alto), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.55)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    # oscurece el centro (donde va el texto) y deja ver las ruinas en los lados
    mascara = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(mascara).ellipse([ancho * 0.18, alto * 0.22, ancho * 0.82, alto * 0.78], fill=185)
    mascara = mascara.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(Image.new("RGB", (ancho, alto), (8, 9, 11)), img, mascara)
    d = ImageDraw.Draw(img)

    cx, cy = ancho / 2, alto / 2
    palabras = cfg["canal"]["nombre"].upper().split()
    arriba, abajo = " ".join(palabras[:-1]), palabras[-1]
    f_ab = fuente(SERIF, 230, 900)
    while d.textlength(abajo, font=f_ab) > 1400:
        f_ab = fuente(SERIF, f_ab.size - 6, 900)
    f_ar = fuente(SANS, 84, 700)
    d.text((cx, cy - 120), "  ".join(arriba), font=f_ar, fill=blanco, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((cx + 6, cy + 46), abajo, font=f_ab, fill=(0, 0, 0), anchor="mm")
    d.text((cx, cy + 40), abajo, font=f_ab, fill=oro, anchor="mm", stroke_width=4, stroke_fill=(40, 25, 5))
    d.line([cx - 560, cy + 160, cx + 560, cy + 160], fill=oro, width=3)
    f_lema = fuente(SANS, 42, 600)
    d.text((cx, cy + 200), "  ".join(cfg["canal"].get("lema", "").upper().split()), font=f_lema,
           fill=(230, 230, 230), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    img.save(destino)


def main():
    cfg = config()
    salida = RAIZ / "marca"
    salida.mkdir(exist_ok=True)
    logo(cfg, salida / "logo_800.png")
    banner(cfg, salida / "banner_2560x1440.png")
    fondo_ia = salida / "fondo_banner_ia.jpg"
    if "--ia" in sys.argv and not fondo_ia.exists():
        import ia_imagen
        ia_imagen.generar(PROMPT_FONDO_BANNER, fondo_ia, 1920, 1080, semilla=42)
    if fondo_ia.exists():
        banner_documental(cfg, fondo_ia, salida / "banner_documental_2560x1440.png")
    log(f"Logo y banners listos en {salida}")


if __name__ == "__main__":
    main()
