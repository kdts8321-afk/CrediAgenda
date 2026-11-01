from pathlib import Path

root = Path("app/src/main/java/mx/crediagenda/app")
main = root / "MainActivity.java"
s = main.read_text()

def change(old, new, label):
    global s
    if old not in s:
        raise RuntimeError("No se encontró referencia: " + label)
    s = s.replace(old, new, 1)

change("import android.os.Bundle;", """import android.os.Bundle;
import android.view.WindowManager;
import java.util.Arrays;""", "imports")

change("    private YearMonth visibleMonth = YearMonth.now();",
"""    private YearMonth visibleMonth = YearMonth.now();
    private boolean accessUnlocked = false;
    private char[] firstAccessSecret = null;""", "state")

change("        store = new Store(this);",
"""        store = new Store(this);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);""", "secure window")

change("""        setContentView(outer);
        render();
    }

    @Override public void onResume() {
        super.onResume();
        if (store != null && body != null) render();
    }""",
"""        showAccessScreen();
    }

    @Override public void onResume() {
        super.onResume();
        if (store == null || body == null) return;
        if (!accessUnlocked) showAccessScreen();
        else render();
    }

    @Override protected void onStop() {
        super.onStop();
        accessUnlocked = false;
        clearPendingAccess();
        if (store != null && body != null) showAccessScreen();
    }""", "lifecycle")

change("""    private void render() {
        if (body == null) return;""",
"""    private void render() {
        if (!accessUnlocked || body == null) return;""", "render security")

change("""        body.addView(button("Seguridad y eliminación de datos", false,
            v -> showPrivacyDialog()), margins(-1, dp(47), 10, 2));""",
"""        body.addView(button("Cambiar PIN o patrón de acceso", false,
            v -> showUnlockScreen(true)), margins(-1, dp(47), 10, 2));
        body.addView(button("Seguridad y eliminación de datos", false,
            v -> showPrivacyDialog()), margins(-1, dp(47), 10, 2));""", "change access menu")

change("""            PrivacyGuard.clear(this);
            selectedCardId = -1;""",
"""            PrivacyGuard.clear(this);
            AccessGuard.clear(this);
            clearPendingAccess();
            selectedCardId = -1;""", "clear access when erasing")

change("""            activeTab = NAV_CARDS;
            render();
            new AlertDialog.Builder(this).setTitle("Datos eliminados")""",
"""            activeTab = NAV_CARDS;
            accessUnlocked = false;
            showAccessScreen();
            new AlertDialog.Builder(this).setTitle("Datos eliminados")""", "relock after erasing")

methods = r'''
    private void clearPendingAccess() {
        if (firstAccessSecret != null) {
            Arrays.fill(firstAccessSecret, '\0');
            firstAccessSecret = null;
        }
    }

    private void showUnlockedApp() {
        clearPendingAccess();
        accessUnlocked = true;
        setContentView(outer);
        render();
    }

    private LinearLayout accessLayout(String title, String sub) {
        LinearLayout root = column();
        root.setBackgroundColor(BG);
        root.setPadding(dp(25), dp(27), dp(25), dp(25));
        root.setGravity(Gravity.CENTER);
        root.addView(label("▣  CrediAgenda", 19, INDIGO, true),
            margins(-1, -2, 0, 16));
        root.addView(label(title, 28, INK, true), margins(-1, -2, 0, 9));
        TextView description = label(sub, 14, MUTED, false);
        root.addView(description, margins(-1, -2, 0, 18));
        return root;
    }

    private void displayAccess(LinearLayout view) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.addView(view, new ScrollView.LayoutParams(-1, -1));
        setContentView(scroll);
    }

    private void showAccessScreen() {
        if (AccessGuard.enabled(this)) showUnlockScreen(false);
        else showSetupChoice();
    }

    private void showSetupChoice() {
        clearPendingAccess();
        LinearLayout screen = accessLayout("Protege tu aplicación",
            "Elige cómo quieres abrir CrediAgenda. El bloqueo se solicitará también al regresar desde otra aplicación.");
        screen.addView(button("Crear PIN de 6 a 8 dígitos", true,
            v -> showSetupCredential(AccessGuard.PIN, false)),
            margins(-1, dp(52), 11, 9));
        screen.addView(button("Crear patrón de 4 puntos o más", false,
            v -> showSetupCredential(AccessGuard.PATTERN, false)),
            margins(-1, dp(52), 0, 8));
        screen.addView(label("Si olvidas el acceso tendrás que borrar los datos de esta instalación de Android. " +
            "El PIN o patrón no cifra la base de datos.", 12, MUTED, false),
            margins(-1, -2, 11, 0));
        if (AccessGuard.enabled(this) && accessUnlocked) {
            screen.addView(button("Cancelar y volver", false, v -> showUnlockedApp()),
                margins(-1, dp(48), 17, 0));
        }
        displayAccess(screen);
    }

    private EditText accessPinField() {
        EditText field = textInput("PIN de 6 a 8 números", "");
        field.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        field.setFilters(new InputFilter[]{new InputFilter.LengthFilter(8)});
        field.setSingleLine(true);
        return field;
    }

    private void showSetupCredential(String kind, boolean confirmation) {
        LinearLayout screen = accessLayout(
            confirmation ? "Confirma tu acceso" : "Configura el acceso",
            AccessGuard.PIN.equals(kind)
                ? (confirmation ? "Repite tu PIN para confirmarlo." : "Utiliza entre 6 y 8 dígitos.")
                : (confirmation ? "Dibuja de nuevo el mismo patrón." : "Une al menos cuatro puntos distintos."));
        if (AccessGuard.PIN.equals(kind)) {
            EditText field = accessPinField();
            screen.addView(field, margins(-1, dp(56), 0, 7));
            screen.addView(button(confirmation ? "Confirmar PIN" : "Continuar", true,
                v -> acceptSetup(kind, field.getText().toString(), confirmation)),
                margins(-1, dp(52), 12, 0));
        } else {
            PatternLockView pattern = new PatternLockView(this);
            pattern.setListener(value -> acceptSetup(kind, value, confirmation));
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, dp(320));
            screen.addView(pattern, params);
            screen.addView(label("Dibuja el patrón sin levantar el dedo.", 13, MUTED, false),
                margins(-1, -2, 0, 9));
        }
        screen.addView(button("Cancelar", false, v -> showSetupChoice()),
            margins(-1, dp(47), 20, 0));
        displayAccess(screen);
    }

    private void acceptSetup(String kind, String value, boolean confirm) {
        char[] chars = value.toCharArray();
        if (!AccessGuard.valid(kind, chars)) {
            Arrays.fill(chars, '\0');
            toast(AccessGuard.PIN.equals(kind)
                ? "El PIN debe tener entre 6 y 8 números." :
                "Une 4 o más puntos diferentes.");
            return;
        }
        if (!confirm) {
            clearPendingAccess();
            firstAccessSecret = chars;
            showSetupCredential(kind, true);
            return;
        }
        boolean same = firstAccessSecret != null && Arrays.equals(firstAccessSecret, chars);
        clearPendingAccess();
        if (!same) {
            Arrays.fill(chars, '\0');
            toast("No coincide. Intenta configurar el acceso otra vez.");
            showSetupCredential(kind, false);
            return;
        }
        try {
            AccessGuard.save(this, kind, chars);
            toast("Acceso protegido correctamente.");
            showUnlockedApp();
        } catch (Exception e) {
            Arrays.fill(chars, '\0');
            toast("No se pudo guardar el método de acceso.");
            showAccessScreen();
        }
    }

    private void showUnlockScreen(boolean changing) {
        if (!AccessGuard.enabled(this)) {
            showSetupChoice();
            return;
        }
        String kind = AccessGuard.kind(this);
        long remaining = AccessGuard.remainingMillis(this);
        LinearLayout screen = accessLayout(
            changing ? "Verifica tu acceso actual" : "CrediAgenda protegida",
            remaining > 0
                ? ("Demasiados intentos. Vuelve a intentarlo en " +
                   (remaining + 999) / 1000 + " segundos.")
                : (AccessGuard.PIN.equals(kind) ? "Introduce tu PIN para continuar." :
                    "Traza tu patrón para continuar."));
        if (AccessGuard.PIN.equals(kind)) {
            EditText field = accessPinField();
            screen.addView(field, margins(-1, dp(56), 0, 10));
            screen.addView(button("Desbloquear", true,
                v -> verifyAccess(field.getText().toString(), changing)),
                margins(-1, dp(52), 9, 0));
        } else {
            PatternLockView pattern = new PatternLockView(this);
            pattern.setListener(value -> verifyAccess(value, changing));
            screen.addView(pattern, new LinearLayout.LayoutParams(-1, dp(320)));
            screen.addView(label("Une los puntos de tu patrón.", 13, MUTED, false),
                margins(-1, -2, 0, 9));
        }
        if (changing) {
            screen.addView(button("Cancelar", false, v -> showUnlockedApp()),
                margins(-1, dp(46), 14, 0));
        } else {
            screen.addView(label("Para proteger tus tarjetas, no hay un botón para omitir este acceso. " +
                "Si lo olvidas, Android permite borrar los datos locales desde Ajustes de aplicaciones.", 12, MUTED, false),
                margins(-1, -2, 19, 0));
        }
        displayAccess(screen);
    }

    private void verifyAccess(String value, boolean changing) {
        long left = AccessGuard.remainingMillis(this);
        if (left > 0) {
            toast("Acceso temporalmente bloqueado. Intenta después.");
            showUnlockScreen(changing);
            return;
        }
        boolean correct = AccessGuard.verify(this, value.toCharArray());
        if (correct) {
            if (changing) showSetupChoice();
            else showUnlockedApp();
        } else {
            toast("PIN o patrón incorrecto.");
            showUnlockScreen(changing);
        }
    }
'''
idx=s.rfind("\n}")
if idx<0:raise RuntimeError("End missing")
s=s[:idx]+"\n"+methods+s[idx:]
main.write_text(s)

# Referencias por copia: nuevos recursos de Java de la misma raíz del paquete.
for name in ["AccessGuard.java", "PatternLockView.java"]:
    path = Path("patches") / name
    dest = root / name
    if not path.exists(): raise RuntimeError(str(path))
    dest.write_text(path.read_text())
print("Acceso CrediAgenda 2.2: PIN o patrón, bloqueo al salir y pantalla segura.")
