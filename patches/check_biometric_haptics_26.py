"""Verifica vibraciones de patrón y flujo biométrico manteniendo PIN/patrón."""
from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess,re,time

root=Path("app/src/main")
p=(root/"java/mx/crediagenda/app/PatternLockView.java").read_text()
j=(root/"java/mx/crediagenda/app/MainActivity.java").read_text()
b=(root/"java/mx/crediagenda/app/BiometricAccess.java").read_text()
m=(root/"AndroidManifest.xml").read_text()
assert "android.permission.VIBRATE" in m
assert "android.permission.USE_BIOMETRIC" in m
assert "VibrationEffect.createOneShot(20L, 85)" in p
assert "if (!nodes.contains(mid))" in p
assert re.search(r"nodes\.add\(mid\);\s+vibrateNewPoint\(\);",p)
assert re.search(r"nodes\.add\(i\);\s+vibrateNewPoint\(\);",p)
assert "BiometricAccess.enabled(this)" in j
assert "BiometricAccess.available(this)" in j
assert 'button("Desbloquear con huella o rostro"' in j
assert 'BiometricAccess.setEnabled(this, true)' in j
assert 'BiometricAccess.setEnabled(this, false)' in j
assert 'BiometricAccess.clear(this)' in j
assert "showUnlockedApp();" in j
assert "onAuthenticationSucceeded" in b
assert "onAuthenticationError" in b
assert "hasEnrolledFingerprints()" in b
assert "BIOMETRIC_WEAK" in b
assert "getMainExecutor()" in b
assert "AtomicBoolean finished" in b
assert "AccessGuard.enabled(c)" in b
ET.fromstring(m)
print("Validaciones de código 2.6 OK: vibración por punto, permiso, biometría con consentimiento y PIN de respaldo.")

# PIN configurado por el ensayo anterior; comprobar que el botón de configuración aparece.
def adb(*a):
    return subprocess.check_output(["adb",*a],text=True,stderr=subprocess.STDOUT,timeout=60)
def nodes():
    adb("shell","uiautomator","dump","/sdcard/personal26.xml")
    return list(ET.fromstring(adb("shell","cat","/sdcard/personal26.xml")).iter())
def find(sub):
    for node in nodes():
        if sub in node.attrib.get("text",""): return node
    return None
def tap(node):
    n=list(map(int,re.findall(r"\d+",node.attrib.get("bounds",""))))
    adb("shell","input","tap",str((n[0]+n[2])//2),str((n[1]+n[3])//2))
    time.sleep(.6)
tab=find("Tarjetas")
assert tab is not None,"No se vio pestaña Tarjetas después de desbloquear"
tap(tab)
assert find("⚙") is not None, "Falta acceso a Configuración"
print("Interfaz 2.6 OK: ajuste biométrico reubicado en Configuración.")
