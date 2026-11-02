"""Prueba de interfaz: no se muestran tarjetas sin PIN, cierra al cambiar de app."""
import re, subprocess, time, xml.etree.ElementTree as ET
import os

PKG = os.environ.get("CREDIAGENDA_TEST_PACKAGE", "mx.crediagenda.app.mx22")
APP_LABEL = os.environ.get("CREDIAGENDA_APP_LABEL", "CrediAgenda")
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
    # El volcado de accesibilidad puede capturarse en pleno cambio de pantalla.
    # Reintentar antes de concluir que falta un elemento.
    for attempt in range(6):
        for n in ui().iter():
            t=n.attrib.get("text","")
            if cls and n.attrib.get("class") != cls: continue
            if text is not None and not ((text in t) if substring else (text==t)): continue
            return n
        time.sleep(.5)
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

def await_screen(expected):
    # El Pixel Launcher del emulador puede mostrar un ANR encima de la app.
    # No es un fallo de Personal; se cierra ese aviso y se vuelve a abrir.
    for attempt in range(10):
        tree = ui()
        items = [n.attrib.get("text", "") for n in tree.iter()]
        if any(expected in value for value in items):
            return
        wait = next((n for n in tree.iter() if n.attrib.get("text") == "Wait"), None)
        if wait is not None:
            tap_node(wait)
        adb("shell", "am", "start", "-n", ACTIVITY)
        time.sleep(2)
    raise AssertionError("Pantalla no encontrada tras reintentos: " + expected + "; visible: " + str(text_list()[:20]))

print("Probar bloqueo inicial")
adb("shell","am","force-stop",PKG)
adb("shell","am","start","-W","-n",ACTIVITY)
await_screen("Protege tu aplicación")
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
time.sleep(2)
adb("shell","am","start","-W","-n",ACTIVITY)
time.sleep(1)
await_screen(f"{APP_LABEL} protegida")
assert not any("TU CONTROL FINANCIERO" in t for t in text_list())
pin("654321")
tap("Desbloquear")
find(text="TU CONTROL FINANCIERO",substring=True)
print("Autobloqueo al regresar y desbloqueo correcto")
