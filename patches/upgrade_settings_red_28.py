"""Personal 2.8: calendario rojo real por paleta, engrane y borrado verificado."""
from pathlib import Path
import re

root=Path("app/src/main/java/mx/crediagenda/app")
main=root/"MainActivity.java"
cal=root/"CalendarSync.java"
j=main.read_text()
c=cal.read_text()

def swap(text,old,new,label,expected=1):
    count=text.count(old)
    if count!=expected: raise RuntimeError("%s: esperado %d, encontrado %d" % (label,expected,count))
    return text.replace(old,new)

# CalendarContract: eventColor sin una clave válida puede ser descartado por el
# proveedor. Elegimos un rojo de la paleta de eventos de esa misma cuenta.
color_helpers=r'''
    private static final int PREFERRED_RED = 0xFFE53935;

    // No altera el color del calendario, solo escoge uno permitido para un evento.
    private static String availableRedEventColorKey(Context context, long calendarId) {
        ContentResolver resolver = context.getContentResolver();
        try (Cursor account = resolver.query(CalendarContract.Calendars.CONTENT_URI,
                new String[]{CalendarContract.Calendars.ACCOUNT_NAME,
                             CalendarContract.Calendars.ACCOUNT_TYPE},
                CalendarContract.Calendars._ID + "=?",
                new String[]{String.valueOf(calendarId)}, null)) {
            if (account == null || !account.moveToFirst()) return null;
            String accountName = account.getString(0);
            String accountType = account.getString(1);
            if (accountName == null || accountType == null) return null;
            String where = CalendarContract.Colors.ACCOUNT_NAME + "=? AND " +
                CalendarContract.Colors.ACCOUNT_TYPE + "=? AND " +
                CalendarContract.Colors.COLOR_TYPE + "=?";
            try (Cursor colors = resolver.query(CalendarContract.Colors.CONTENT_URI,
                    new String[]{CalendarContract.Colors.COLOR_KEY, CalendarContract.Colors.COLOR},
                    where,
                    new String[]{accountName, accountType,
                        String.valueOf(CalendarContract.Colors.TYPE_EVENT)}, null)) {
                String key = null;
                long best = Long.MAX_VALUE;
                if (colors != null) while (colors.moveToNext()) {
                    String candidate = colors.getString(0);
                    int color = colors.getInt(1);
                    int r = (color >>> 16) & 255, g = (color >>> 8) & 255, b = color & 255;
                    // Rechazar colores que no sean rojos de verdad.
                    if (r < 115 || r < g * 1.30 || r < b * 1.30) continue;
                    int dr = r - 229, dg = g - 57, db = b - 53;
                    long score = dr*dr + 2L*dg*dg + db*db;
                    if (score < best) { best=score; key=candidate; }
                }
                return key;
            }
        } catch (Exception ignore) {
            // Un proveedor podría no exponer su paleta. Intentamos el color directo.
            return null;
        }
    }

    private static ContentValues withRedColor(Context context, long calendarId, ContentValues values) {
        String key = availableRedEventColorKey(context, calendarId);
        if (key == null || key.isEmpty()) {
            values.put(CalendarContract.Events.EVENT_COLOR, PREFERRED_RED);
        } else {
            values.put(CalendarContract.Events.EVENT_COLOR_KEY, key);
        }
        return values;
    }

    static boolean hasVisibleRedEventColor(Context context, long eventId) {
        if (!hasPermissions(context) || eventId <= 0) return false;
        try (Cursor result = context.getContentResolver().query(
                CalendarContract.Events.CONTENT_URI,
                new String[]{CalendarContract.Events.DISPLAY_COLOR},
                CalendarContract.Events._ID + "=?", new String[]{String.valueOf(eventId)}, null)) {
            if (result == null || !result.moveToFirst()) return false;
            int color = result.getInt(0), r=(color >>> 16)&255,
                g=(color >>> 8)&255, b=color&255;
            return r >= 115 && r > g*1.30 && r > b*1.30;
        } catch (Exception ignore) { return false; }
    }
'''
needle="    static boolean upsert(Context context, Store store, Models.Payment payment) {"
c=swap(c,needle,color_helpers+"\n"+needle,"Color support helpers")
c=swap(c,"        values.put(CalendarContract.Events.EVENT_COLOR, 0xFFE53935);",
       "        // El color se elige usando la paleta de la cuenta en upsert().",
       "Color evento directo")
c=swap(c,"eventValues(payment, card, calId),",
       "withRedColor(context, calId, eventValues(payment, card, calId)),",
       "Color en update")
c=swap(c,"resolver.insert(CalendarContract.Events.CONTENT_URI, eventValues(payment, card, calId))",
       "resolver.insert(CalendarContract.Events.CONTENT_URI, withRedColor(context, calId, eventValues(payment, card, calId)))",
       "Color en insert")
cal.write_text(c)

# Menú único, accesible desde cualquier pestaña por el icono ⚙ arriba a la derecha.
old='''        body.addView(button("Cambiar PIN o patrón de acceso", false,
            v -> showUnlockScreen(true)), margins(-1, dp(47), 10, 2));
        body.addView(button(BiometricAccess.enabled(this)
                ? "Desactivar acceso con huella o rostro"
                : "Activar acceso con huella o rostro", false,
            v -> configureBiometrics()), margins(-1, dp(47), 10, 2));
        body.addView(button("Seguridad y eliminación de datos", false,
            v -> showPrivacyDialog()), margins(-1, dp(47), 10, 2));'''
j=swap(j,old,"","Eliminar opciones de seguridad de Mis tarjetas")
j=swap(j,'''        body.addView(button("Privacidad y eliminación de datos", false, v -> showPrivacyDialog()),
                margins(-1, dp(48), 10, 0));''',"","Eliminar acceso redundante calendario")

# Este método se llama en cada pantalla principal que presenta un encabezado;
# el detalle de una tarjeta no presenta headline y recibe su propio engrane.
jcount=len(re.findall(r'(?m)^        headline\(',j))
if jcount<3: raise RuntimeError("No suficientes encabezados: %s" % jcount)
j=j.replace("\n        headline(", "\n        addSettingsGear();\n        headline(")
j=swap(j,'''    private void showCardDetail() {
        Models.Card c = store.card(selectedCardId);''',
    '''    private void showCardDetail() {
        addSettingsGear();
        Models.Card c = store.card(selectedCardId);''', "engrane detalle")

# Elimina antiguos flujos basados en clave adicional; se conserva la ejecución
# real del borrado de pagos y eventos, usada ahora solo tras autenticación exitosa.
a=j.index("    private EditText passwordInput(String hint) {")
b=j.index("    private void eraseEverything() {",a)
j=j[:a]+j[b:]

menu_methods=r'''
    private void addSettingsGear() {
        LinearLayout bar = row();
        bar.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        TextView gear = label("⚙", 30, INDIGO, true);
        gear.setGravity(Gravity.CENTER);
        gear.setContentDescription("Configuración de Personal");
        gear.setOnClickListener(v -> showSettingsMenu());
        bar.addView(gear, new LinearLayout.LayoutParams(dp(58), dp(49)));
        body.addView(bar, margins(-1, dp(49), 0, 0));
    }

    private void showSettingsMenu() {
        if (!accessUnlocked) return;
        new AlertDialog.Builder(this)
            .setTitle("⚙  Configuración")
            .setItems(new String[]{
                "Cambiar PIN o patrón",
                BiometricAccess.enabled(this) ? "Desactivar huella o rostro" :
                    "Activar huella o rostro",
                "Eliminar todos los datos"
            }, (dialog, index) -> {
                if (index == 0) showUnlockScreen(true);
                else if (index == 1) configureBiometrics();
                else confirmDeleteAll();
            })
            .setNegativeButton("Cerrar", null).show();
    }

    private void confirmDeleteAll() {
        if (!accessUnlocked || !AccessGuard.enabled(this)) return;
        new AlertDialog.Builder(this)
            .setTitle("¿Eliminar todos los datos?")
            .setMessage("Se borrarán definitivamente todas las tarjetas, pagos, " +
                "apodos, fechas de corte y ajustes de esta instalación. " +
                "También se intentarán eliminar los eventos de pago creados por Personal " +
                "en Samsung Calendar. Esta acción no se puede deshacer. ¿Continuar?")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Confirmar", (dialog, which) -> authenticateForDeletion())
            .show();
    }

    private void authenticateForDeletion() {
        if (!accessUnlocked || !AccessGuard.enabled(this)) return;
        if (AccessGuard.remainingMillis(this) > 0) {
            toast("Acceso temporalmente bloqueado. Inténtalo después.");
            return;
        }
        if (BiometricAccess.enabled(this) && BiometricAccess.available(this)) {
            biometricPromptActive = true;
            biometricCancellation = BiometricAccess.prompt(this,
                () -> {
                    biometricPromptActive = false;
                    biometricCancellation = null;
                    if (accessUnlocked && AccessGuard.enabled(this)) eraseEverything();
                },
                () -> {
                    biometricPromptActive = false;
                    biometricCancellation = null;
                    if (accessUnlocked && !isFinishing() && !isDestroyed())
                        verifyDeleteWithCredential();
                });
        } else {
            verifyDeleteWithCredential();
        }
    }

    private void verifyDeleteWithCredential() {
        if (!accessUnlocked || !AccessGuard.enabled(this)) return;
        String kind=AccessGuard.kind(this);
        LinearLayout form=dialogContent();
        form.addView(label(AccessGuard.PIN.equals(kind)
                ? "Ingresa tu PIN de Personal para autorizar el borrado."
                : "Dibuja tu patrón de Personal para autorizar el borrado.",
            14, MUTED, false), margins(-1, -2, 0, 8));
        if (AccessGuard.PIN.equals(kind)) {
            EditText input=accessPinField();
            form.addView(input, margins(-1, dp(55), 0, 10));
            AlertDialog dlg=new AlertDialog.Builder(this)
                .setTitle("Verificar identidad")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Verificar y borrar", null).create();
            dlg.setOnShowListener(ignore ->
                dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                    if (AccessGuard.remainingMillis(this)>0) {
                        toast("Demasiados intentos. Inténtalo después.");
                        return;
                    }
                    if (AccessGuard.verify(this, input.getText().toString().toCharArray())) {
                        dlg.dismiss();
                        eraseEverything();
                    } else {
                        input.setText("");
                        input.setError("PIN incorrecto");
                    }
                }));
            dlg.show();
        } else {
            PatternLockView pattern=new PatternLockView(this);
            AlertDialog dlg=new AlertDialog.Builder(this)
                .setTitle("Verificar identidad")
                .setView(form)
                .setNegativeButton("Cancelar", null).create();
            pattern.setListener(value -> {
                if (AccessGuard.remainingMillis(this)>0) {
                    toast("Demasiados intentos. Inténtalo después.");
                    return;
                }
                if (AccessGuard.verify(this, value.toCharArray())) {
                    dlg.dismiss();
                    eraseEverything();
                } else {
                    toast("Patrón incorrecto. Intenta otra vez.");
                }
            });
            form.addView(pattern, new LinearLayout.LayoutParams(-1, dp(320)));
            dlg.show();
        }
    }
'''
idx=j.rfind("\n}")
if idx<0: raise RuntimeError("No se encontró cierre de MainActivity")
j=j[:idx]+"\n"+menu_methods+j[idx:]
if "showPrivacyDialog()" in j:raise RuntimeError("Acceso antiguo a privacidad sigue referenciado")
if "setupDeletePassword()" in j:raise RuntimeError("Flujo antiguo sigue activo")
main.write_text(j)
print("2.8: engrane global, menú único, borrado confirmación -> huella/rostro o PIN/patrón; color rojo de paleta.")
