from pathlib import Path

root = Path("app/src/main/java/mx/crediagenda/app")
main = root / "MainActivity.java"
pattern = root / "PatternLockView.java"
manifest = Path("app/src/main/AndroidManifest.xml")
j = main.read_text()
p = pattern.read_text()
xml = manifest.read_text()

def rep(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError("%s: expected 1 occurrence, found %d" % (label, count))
    return text.replace(old, new, 1)

# Permisos normales (vibración) y biometría (Android controla autenticación).
if "android.permission.VIBRATE" not in xml:
    xml = rep(xml, "<manifest", "<manifest", "check manifest") # no-op positional check
    idx=xml.index(">")
    xml=xml[:idx+1] + """
    <uses-permission android:name="android.permission.VIBRATE"/>
    <uses-permission android:name="android.permission.USE_BIOMETRIC"/>
    <uses-permission android:name="android.permission.USE_FINGERPRINT"/>
""" + xml[idx+1:]
manifest.write_text(xml)

# La vibración ocurre únicamente al entrar en un punto nuevo, también cuando
# Android incorpora automáticamente el punto intermedio de un trazo.
p = rep(p, "import android.graphics.Paint;",
    """import android.graphics.Paint;
import android.os.Vibrator;
import android.os.VibrationEffect;
import android.os.Build;""", "imports hapticos")
p = rep(p, "    private boolean drawing = false;",
    """    private boolean drawing = false;

    private void vibrateNewPoint() {
        try {
            Vibrator vibrator = (Vibrator) getContext().getSystemService(Context.VIBRATOR_SERVICE);
            if (vibrator != null && vibrator.hasVibrator()) {
                vibrator.vibrate(VibrationEffect.createOneShot(20L, 85));
            }
        } catch (Exception ignored) {
            // Sin motor o vibración bloqueada por ajustes del sistema: patrón usable.
        }
    }""", "motor de vibracion")
p = rep(p, "                            if (!nodes.contains(mid)) nodes.add(mid);",
    """                            if (!nodes.contains(mid)) {
                                nodes.add(mid);
                                vibrateNewPoint();
                            }""", "punto intermedio")
p = rep(p, "                    nodes.add(i);",
    """                    nodes.add(i);
                    vibrateNewPoint();""", "nuevo punto")
pattern.write_text(p)

# Control de ciclo de vida: jamás saltarse la pantalla de acceso por pausar la app.
j = rep(j, "import android.view.WindowManager;",
    """import android.view.WindowManager;
import android.os.CancellationSignal;""", "imports biometricos")
j = rep(j, "    private boolean accessUnlocked = false;",
    """    private boolean accessUnlocked = false;
    private boolean biometricPromptActive = false;
    private boolean biometricAutoAttempted = false;
    private CancellationSignal biometricCancellation;""", "estado biometricos")

j = rep(j,
    """        if (!accessUnlocked) showAccessScreen();
        else render();""",
    """        if (biometricPromptActive) return;
        if (!accessUnlocked) showAccessScreen();
        else render();""", "onResume biometric")

j = rep(j,
    """        if (store != null && body != null) showAccessScreen();
        super.onPause();""",
    """        if (!biometricPromptActive && store != null && body != null) showAccessScreen();
        super.onPause();""", "onPause biometric")

j = rep(j,
    """    @Override protected void onStop() {
        super.onStop();
        accessUnlocked = false;
    }""",
    """    @Override protected void onStop() {
        super.onStop();
        accessUnlocked = false;
        // Si el usuario se cambia de app durante el diálogo, se cancela la operación.
        if (biometricCancellation != null) {
            CancellationSignal cancel = biometricCancellation;
            biometricCancellation = null;
            biometricPromptActive = false;
            cancel.cancel();
        }
        biometricAutoAttempted = false;
        if (store != null && body != null) showAccessScreen();
    }""", "onStop biometric")

j = rep(j,
    """        body.addView(button("Cambiar PIN o patrón de acceso", false,
            v -> showUnlockScreen(true)), margins(-1, dp(47), 10, 2));""",
    """        body.addView(button("Cambiar PIN o patrón de acceso", false,
            v -> showUnlockScreen(true)), margins(-1, dp(47), 10, 2));
        body.addView(button(BiometricAccess.enabled(this)
                ? "Desactivar acceso con huella o rostro"
                : "Activar acceso con huella o rostro", false,
            v -> configureBiometrics()), margins(-1, dp(47), 10, 2));""",
    "acceso al ajuste desde tarjetas")

j = rep(j, """            AccessGuard.clear(this);
            clearPendingAccess();""",
    """            AccessGuard.clear(this);
            BiometricAccess.clear(this);
            clearPendingAccess();""", "borrado total también desactiva biometrias")

j = rep(j, """            AccessGuard.save(this, kind, chars);
            toast("Acceso protegido correctamente.");""",
    """            AccessGuard.save(this, kind, chars);
            // Al cambiar el PIN/patrón se exige volver a activar la biometría.
            BiometricAccess.setEnabled(this, false);
            toast("Acceso protegido correctamente.");""", "reset biometric al cambiar clave")

j = rep(j,
    """        if (changing) {
            screen.addView(button("Cancelar", false, v -> showUnlockedApp()),
                margins(-1, dp(46), 14, 0));""",
    """        if (!changing && BiometricAccess.enabled(this) && BiometricAccess.available(this)) {
            screen.addView(button("Desbloquear con huella o rostro", false,
                v -> startBiometricUnlock()), margins(-1, dp(50), 12, 5));
        }
        if (changing) {
            screen.addView(button("Cancelar", false, v -> showUnlockedApp()),
                margins(-1, dp(46), 14, 0));""", "botón huella/rostro pantalla login")

j = rep(j,
    """        displayAccess(screen);
    }

    private void verifyAccess(String value, boolean changing) {""",
    """        displayAccess(screen);
        if (!changing && BiometricAccess.enabled(this) && BiometricAccess.available(this)
                && !biometricAutoAttempted) {
            biometricAutoAttempted = true;
            screen.post(() -> {
                if (!accessUnlocked && !biometricPromptActive &&
                        !isFinishing() && !isDestroyed() &&
                        BiometricAccess.enabled(this)) {
                    startBiometricUnlock();
                }
            });
        }
    }

    private void verifyAccess(String value, boolean changing) {""", "auto prompt")

j = rep(j,
    """    private void showUnlockedApp() {
        clearPendingAccess();
        accessUnlocked = true;""",
    """    private void showUnlockedApp() {
        clearPendingAccess();
        biometricAutoAttempted = false;
        accessUnlocked = true;""", "reset auto prompt al desbloquear")

methods = r'''
    private void startBiometricUnlock() {
        if (biometricPromptActive || accessUnlocked || !BiometricAccess.enabled(this)
                || !BiometricAccess.available(this) || !AccessGuard.enabled(this)) {
            if (!BiometricAccess.available(this)) toast("No hay biometría disponible o registrada.");
            return;
        }
        biometricPromptActive = true;
        biometricCancellation = BiometricAccess.prompt(this,
            () -> {
                biometricPromptActive = false;
                biometricCancellation = null;
                // La comprobación la realiza la ventana biométrica de Android.
                if (AccessGuard.enabled(this) && BiometricAccess.enabled(this)) {
                    showUnlockedApp();
                } else {
                    showAccessScreen();
                }
            }, () -> {
                biometricPromptActive = false;
                biometricCancellation = null;
                // Se conserva el formulario de PIN o patrón, sin abrir los datos.
                if (!accessUnlocked && !isFinishing() && !isDestroyed()) showAccessScreen();
            });
    }

    private void configureBiometrics() {
        if (!accessUnlocked || !AccessGuard.enabled(this)) return;
        if (BiometricAccess.enabled(this)) {
            new AlertDialog.Builder(this)
                .setTitle("Desactivar desbloqueo biométrico")
                .setMessage("Seguirás entrando con tu PIN o patrón. Puedes volver a activar la biometría en cualquier momento.")
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Desactivar", (d, which) -> {
                    BiometricAccess.setEnabled(this, false);
                    toast("Biometría desactivada.");
                    render();
                }).show();
            return;
        }
        if (!BiometricAccess.available(this)) {
            new AlertDialog.Builder(this)
                .setTitle("Biometría no disponible")
                .setMessage("Para usar huella o rostro primero registra un método compatible " +
                    "en los ajustes de seguridad de tu Samsung. Si el equipo no admite " +
                    "autenticación biométrica para apps, continúa con PIN o patrón.")
                .setPositiveButton("Entendido", null).show();
            return;
        }
        new AlertDialog.Builder(this)
            .setTitle("Activar huella o rostro")
            .setMessage("Usaremos la identificación biométrica guardada en Android. " +
                "Personal no almacena huellas ni rostros. Tu PIN o patrón seguirá disponible.")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Verificar y activar", (dialog, which) -> {
                if (biometricPromptActive) return;
                biometricPromptActive = true;
                biometricCancellation = BiometricAccess.prompt(this, () -> {
                    biometricPromptActive = false;
                    biometricCancellation = null;
                    if (AccessGuard.enabled(this)) {
                        BiometricAccess.setEnabled(this, true);
                        toast("Huella o rostro activados.");
                        showUnlockedApp();
                    }
                }, () -> {
                    biometricPromptActive = false;
                    biometricCancellation = null;
                    toast("No se activó la biometría.");
                    // Al regresar del diálogo puede haberse bloqueado la actividad.
                    if (accessUnlocked) render();
                    else showAccessScreen();
                });
            }).show();
    }
'''
idx=j.rfind("\n}")
if idx<0:raise RuntimeError("End of activity not found")
j=j[:idx]+"\n"+methods+j[idx:]
main.write_text(j)

biometric_java = Path("patches/BiometricAccess.java")
if not biometric_java.exists(): raise RuntimeError("Falta BiometricAccess.java")
(root/"BiometricAccess.java").write_text(biometric_java.read_text())
assert "android.permission.USE_BIOMETRIC" in manifest.read_text()
assert "android.permission.VIBRATE" in manifest.read_text()
print("Personal 2.6: vibración por cada punto; huella/rostro opt-in, pantalla de desbloqueo automática, respaldo PIN/patrón.")
