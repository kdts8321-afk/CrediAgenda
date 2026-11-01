"""Empaqueta los identificadores visuales de marcas como PNG; no se descargan en el teléfono."""
from pathlib import Path
import re
import time
import urllib.request
import cairosvg
from PIL import Image, ImageDraw

out = Path("app/src/main/res/drawable-nodpi")
out.mkdir(parents=True, exist_ok=True)
ua = "CrediAgendaPersonal/2.0 (educational personal-use app; +https://github.com)"

def fetch(urls):
    problems = []
    for url in urls:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent":ua, "Accept":"image/svg+xml,*/*"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = r.read()
                if not data.lstrip().startswith(b"<") or b"<svg" not in data[:1000]:
                    raise ValueError("No es SVG")
                print("Logo obtenido:", url, len(data))
                return data
            except Exception as e:
                problems.append(str(e))
                time.sleep(1)
    raise RuntimeError("No se pudo descargar logo: " + str(problems[-2:]))

def save_logo(name, urls, fill=None):
    svg = fetch(urls)
    if fill:
        svg = re.sub(rb"<svg\b", b'<svg fill="' + fill.encode() + b'"', svg, count=1)
    # Algunos SVG incluyen entidades XML de Inkscape; se expanden con control antes del render.
    entities = re.findall(rb'<!ENTITY\s+([A-Za-z_][A-Za-z0-9_-]*)\s+"([^"]*)"', svg)
    for key, value in entities:
        svg = svg.replace(b"&" + key + b";", value)
    svg = re.sub(rb'<!DOCTYPE.*?\]>', b"", svg, flags=re.S)
    svg = re.sub(rb'<!DOCTYPE[^>]*>', b"", svg, flags=re.S)
    cairosvg.svg2png(bytestring=svg, write_to=str(out / (name + ".png")), output_width=540)

save_logo("bank_bbva", [
    "https://upload.wikimedia.org/wikipedia/commons/7/70/Logotipo_de_BBVA.svg",
    "https://raw.githubusercontent.com/JabberLabs/awesome-dashboard-icons/main/icons/bbva.svg"
])
save_logo("bank_banamex", [
    "https://www.banamex.com/solicita-tu-tarjeta-credito-en-linea/assets/img/ilustraciones/Banamex.svg",
    "https://commons.wikimedia.org/wiki/Special:Redirect/file/Banamex.svg",
])
save_logo("bank_stori", [
    "https://commons.wikimedia.org/wiki/Special:Redirect/file/Stori_Logo_2023.svg",
    "https://commons.wikimedia.org/wiki/Special:Redirect/file/Stori_logo.svg",
])
save_logo("bank_nu", [
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/nubank.svg"
], "#8A05BE")
save_logo("bank_mercado", [
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/mercadopago.svg"
], "#009EE3")
save_logo("network_visa", [
    "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/visa.svg"
], "#1434CB")

# Símbolo de red Mastercard: círculos de colores de la identidad gráfica.
im = Image.new("RGBA", (420, 260), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.ellipse((40, 30, 240, 230), fill="#EB001B")
d.ellipse((180, 30, 380, 230), fill="#F79E1B")
im.save(out / "network_mastercard.png")
assert len(list(out.glob("*.png"))) >= 7
print("Logos PNG generados", [p.name for p in out.glob("*.png")])
