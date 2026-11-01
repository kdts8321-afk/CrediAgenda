"""Personal: nombre visible + icono minimalista triangulo equilatero con circulo."""
from pathlib import Path
from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET
import re, math

root=Path("app/src/main")
res=root/"res"
manifest=root/"AndroidManifest.xml"
java=root/"java/mx/crediagenda/app"

# Cambiar exclusivamente texto visible; nombres de paquete/clases, base de datos y
# preferencias se mantienen para evitar cambios colaterales.
for filename in ("MainActivity.java", "CalendarSync.java"):
    path=java/filename
    if not path.exists(): raise RuntimeError("Falta archivo "+str(path))
    contents=path.read_text()
    # Cadena para texto de pantallas y eventos del calendario (no nombres internos)
    contents=contents.replace('"CrediAgenda', '"Personal').replace(' CrediAgenda', ' Personal')
    path.write_text(contents)

# Asegurar nombre del lanzador y recursos en el manifiesto Android.
content=manifest.read_text()
if 'android:label=' not in content: raise RuntimeError("Falta etiqueta de app")
content,n=re.subn(r'android:label="[^"]+"','android:label="Personal"',content,count=1)
if n!=1: raise RuntimeError("No se pudo renombrar")
if 'android:icon=' in content:
    content=re.sub(r'android:icon="[^"]+"','android:icon="@mipmap/ic_personal"',content,count=1)
else:
    content=content.replace('<application','<application android:icon="@mipmap/ic_personal"',1)
if 'android:roundIcon=' in content:
    content=re.sub(r'android:roundIcon="[^"]+"','android:roundIcon="@mipmap/ic_personal_round"',content,count=1)
else:
    content=content.replace('<application','<application android:roundIcon="@mipmap/ic_personal_round"',1)
manifest.write_text(content)

# Dibujo 512 x 512 con supermuestreo 4x para lineas suaves.
S=512; SS=4
BLUE=(22,54,111,255)
WHITE=(255,255,255,255)
def square_icon():
    image=Image.new("RGBA",(S*SS,S*SS),WHITE)
    d=ImageDraw.Draw(image)
    # Equilatero: lado 286px, altura = lado * raiz(3)/2, centrado geometricamente.
    side=286
    h=side*math.sqrt(3)/2
    center_y=258
    apex=(256,center_y-2*h/3)
    left=(256-side/2,center_y+h/3)
    right=(256+side/2,center_y+h/3)
    poly=[(int(x*SS),int(y*SS)) for x,y in [apex,left,right,apex]]
    d.line(poly,fill=BLUE,width=29*SS,joint="curve")
    radius=36
    d.ellipse(((256-radius)*SS,(center_y-radius)*SS,(256+radius)*SS,(center_y+radius)*SS),fill=BLUE)
    return image.resize((512,512),Image.Resampling.LANCZOS)

# Icono tradicional cuadrado para versiones Android antiguas y vista de apps.
base=square_icon()
sizes={"mdpi":48,"hdpi":72,"xhdpi":96,"xxhdpi":144,"xxxhdpi":192}
for density,size in sizes.items():
    directory=res/f"mipmap-{density}"
    directory.mkdir(parents=True,exist_ok=True)
    for name in ("ic_personal.png","ic_personal_round.png"):
        base.resize((size,size),Image.Resampling.LANCZOS).save(directory/name)

# Adaptive: fondo blanco y simbolo centrado en zona segura. Android aplica su propia mascara.
foreground=Image.new("RGBA",(512*SS,512*SS),(0,0,0,0))
d=ImageDraw.Draw(foreground)
side=233; h=side*math.sqrt(3)/2
cy=256
points=[(256,cy-2*h/3),(256-side/2,cy+h/3),(256+side/2,cy+h/3)]
coords=[(int(x*SS),int(y*SS)) for x,y in [*points,points[0]]]
d.line(coords,fill=BLUE,width=27*SS,joint="curve")
rad=33
d.ellipse(((256-rad)*SS,(cy-rad)*SS,(256+rad)*SS,(cy+rad)*SS),fill=BLUE)
foreground=foreground.resize((512,512),Image.Resampling.LANCZOS)
nodpi=res/"drawable-nodpi";nodpi.mkdir(parents=True,exist_ok=True)
foreground.save(nodpi/"personal_foreground.png")

anydpi=res/"mipmap-anydpi-v26";anydpi.mkdir(parents=True,exist_ok=True)
xml='''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@android:color/white"/>
    <foreground android:drawable="@drawable/personal_foreground"/>
</adaptive-icon>
'''
(anydpi/"ic_personal.xml").write_text(xml)
(anydpi/"ic_personal_round.xml").write_text(xml)
assert 'android:label="Personal"' in manifest.read_text()
assert 'android:icon="@mipmap/ic_personal"' in manifest.read_text()
assert (res/"mipmap-xxhdpi/ic_personal.png").exists()
print("Nombre: Personal. Icono: triángulo equilátero azul con círculo central sobre fondo blanco. 5 densidades + adaptativo.")
