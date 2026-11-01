"""Prueba de interfaz: no se muestran tarjetas sin PIN, cierra al cambiar de app."""
import re, subprocess, time, xml.etree.ElementTree as ET

PKG = "mx.crediagenda.app.mx22"
ACTIVITY = f"{PKG}/mx.crediagenda.app.MainActivity"

def adb(*args):
    return subprocess.check_output(["adb", *args], encoding="utf-8", stderr=subprocess.STDOUT, timeout=60)

def ui():
    for _ in range(4):
        try:
            adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
            return ET.fromstring(adb("shell", "cat", "/sdcard/window.xml"))
        except Exception as e:
            time.sleep(1)
    raise RuntimeError("No se pudo inspeccionar la interfaz")

def text_list():
    return [n.attrib.get("text","") for n in ui().iter() if n.attrib.get("text")]

def find(text=None, cls=None, substring=False):
    for n in ui().iter():
        t=n.attrib.get("text","")
        if cls and n.attrib.get("class") != cls: continue
        if text is not None and not ((text in t) if substring else (text==t)): continue
        return n
    raise AssertionError(f"No se encontró {text or cls}; visible: {text_list()[:25]}")

def tap_node(n):
    nums=list(map(int,re.findall(r"\d+",n.attrib["bounds"])))
    x=(nums[0]+nums[2])//2;y=(nums[1]+nums[3])//2
    adb("shell","input","tap",str(x),str(y))
    time.sleep(.7)

def tap(text):
    tap_node(find(text=text,substring=True))

def pin(text):
    tap_node(find(cls="android.widget.EditText"))
    adb("shell","input","text",text)
    adb("shell","input","keyevent","4")
    time.sleep(.5)

print("Probar bloqueo inicial")
adb("shell","am","force-stop",PKG)
adb("shell","am","start","-W","-n",ACTIVITY)
find(text="Protege tu aplicación",substring=True)
assert not any("TU CONTROL FINANCIERO" in t for t in text_list())
tap("Crear PIN")
find(text="Configura el acceso",substring=True)
pin("654321")
tap("Continuar")
find(text="Confirma tu acceso",substring=True)
pin("654321")
tap("Confirmar PIN")
find(text="TU CONTROL FINANCIERO",substring=True)
print("PIN creado, resumen mostrado")

adb("shell","input","keyevent","3")
time.sleep(1)
adb("shell","am","start","-W","-n",ACTIVITY)
find(text="CrediAgenda protegida",substring=True)
assert not any("TU CONTROL FINANCIERO" in t for t in text_list())
pin("654321")
tap("Desbloquear")
find(text="TU CONTROL FINANCIERO",substring=True)
print("Autobloqueo al regresar y desbloqueo correcto")
