"""Personal 2.8: pruebas de menú, confirmación de borrado y paleta de calendario."""
from pathlib import Path
import re, subprocess, xml.etree.ElementTree as ET, time

root=Path("app/src/main/java/mx/crediagenda/app")
j=(root/"MainActivity.java").read_text()
c=(root/"CalendarSync.java").read_text()
s=(root/"Store.java").read_text()

assert "availableRedEventColorKey" in c
assert "CalendarContract.Colors.CONTENT_URI" in c
assert "CalendarContract.Colors.TYPE_EVENT" in c
assert "CalendarContract.Events.EVENT_COLOR_KEY" in c
assert "CalendarContract.Events.EVENT_COLOR, PREFERRED_RED" in c
assert "CalendarContract.Events.ALL_DAY, 1" in c
assert "withRedColor(context, calId, eventValues(payment, card, calId))" in c
assert "addSettingsGear();" in j
assert 'gear.setContentDescription("Configuración de Personal")' in j
assert 'setTitle("⚙  Configuración")' in j
assert "showPrivacyDialog()" not in j
assert "setupDeletePassword()" not in j
assert "PrivacyGuard.verify(this" not in j
assert "confirmDeleteAll()" in j
assert 'setTitle("¿Eliminar todos los datos?")' in j
assert 'setPositiveButton("Confirmar", (dialog, which) -> authenticateForDeletion())' in j
assert "BiometricAccess.prompt(this," in j
assert "AccessGuard.verify(this, input.getText().toString().toCharArray())" in j
assert "AccessGuard.verify(this, value.toCharArray())" in j
assert "eraseEverything();" in j
assert "store.clearAllData();" in j
assert 'db.delete("card_cutoffs", null, null);' in s
print("Código 2.8: color rojo compatible, engrane y flujo protegido de borrado OK.")

def adb(*args):
    return subprocess.check_output(["adb",*args], encoding="utf-8",stderr=subprocess.STDOUT,timeout=60)
def find(value, field="text"):
    adb("shell","uiautomator","dump","/sdcard/personal28.xml")
    root=ET.fromstring(adb("shell","cat","/sdcard/personal28.xml"))
    for n in root.iter():
        if value in n.attrib.get(field,""):return n
    raise AssertionError("No aparece: "+value)
def tap_node(n):
    xy=list(map(int,re.findall(r"\d+",n.attrib["bounds"])))
    adb("shell","input","tap",str((xy[0]+xy[2])//2),str((xy[1]+xy[3])//2))
    time.sleep(.5)

tap_node(find("Configuración de Personal","content-desc"))
find("Cambiar PIN o patrón")
find("Activar huella o rostro")
tap_node(find("Eliminar todos los datos"))
find("¿Eliminar todos los datos?")
tap_node(find("Cancelar"))
find("Configuración de Personal","content-desc")
print("Interfaz 2.8: menú y confirmación cancelable comprobados.")
