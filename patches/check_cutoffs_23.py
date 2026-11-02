"""Verificaciones de las fechas de corte: pestaña, esquema y ausencia de eventos de calendario."""
from pathlib import Path
import subprocess, time, xml.etree.ElementTree as ET

root = Path("app/src/main/java/mx/crediagenda/app")
source = (root / "MainActivity.java").read_text()
store = (root / "Store.java").read_text()
calendar = (root / "CalendarSync.java").read_text()

assert "card_cutoffs" in store and ('null, 4)' in store or 'null, 5)' in store)
assert "PRIMARY KEY(card_id, month)" in store
assert "ON DELETE CASCADE" in store
assert "void saveCutoffDate" in store
assert "void removeCutoffDate" in store
assert "oldVersion < 4" in store
assert 'db.delete("card_cutoffs", null, null)' in store
assert "NAV_CUTOFFS" in source and "Fecha de corte" in source
cutoff = source[source.index("    /** Las fechas de corte"):source.rfind("\n}")]
assert "CalendarSync." not in cutoff.replace("CalendarSync: esta fecha", "sin calendario: esta fecha")
assert "CalendarSync.upsert" not in cutoff and "CalendarSync.openManualCalendar" not in cutoff
assert "CalendarContract.Events" not in cutoff
assert "card_cutoffs" not in calendar
print("Aislamiento de fechas de corte verificado: sin eventos en Samsung Calendar")

def adb(*args):
    return subprocess.check_output(["adb", *args], encoding="utf-8", timeout=65)
def nodes():
    for i in range(5):
        try:
            adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
            return list(ET.fromstring(adb("shell", "cat", "/sdcard/window.xml")).iter())
        except Exception:
            time.sleep(.5)
    raise RuntimeError("No hay jerarquía de interfaz")
tree=nodes()
cutoff_tab=next((n for n in tree if "Cortes" in n.attrib.get("text","")),None)
if cutoff_tab is None: raise RuntimeError("No se encontró la pestaña Cortes")
import re
box=list(map(int,re.findall(r"\d+",cutoff_tab.attrib["bounds"])))
adb("shell","input","tap",str((box[0]+box[2])//2),str((box[1]+box[3])//2))
time.sleep(.6)
texts=[n.attrib.get("text","") for n in nodes()]
assert any("Fechas de corte" in t for t in texts),texts[:20]
assert any("Aún no hay tarjetas" in t for t in texts),texts[:20]
print("Pestaña de cortes visible; sin tarjetas no inventa fechas.")
