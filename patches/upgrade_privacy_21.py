from pathlib import Path

root = Path("app/src/main/java/mx/crediagenda/app")
main = root / "MainActivity.java"
store = root / "Store.java"
j = main.read_text()
s = store.read_text()

def rep(old, new, label):
    global j
    if old not in j:
        raise RuntimeError("No se encontró " + label)
    j = j.replace(old, new, 1)

rep('    private void showCardDialog(Models.Card card) {',
'''    private static final String[] MEXICAN_ISSUERS = {
        "Selecciona un banco", "Banamex", "BBVA", "HSBC", "Santander",
        "Banorte", "Stori", "Nu", "Mercado Libre"
    };

    private void showCardDialog(Models.Card card) {''', "catalogo emisores")

rep('        inputTitle(fields, "Banco o emisor");\n        EditText bank = textInput("BBVA, Banamex, Stori, Nu, Mercado Libre...", edit ? card.name : "");\n        bank.setFilters(new InputFilter[]{new InputFilter.LengthFilter(35)});\n        fields.addView(bank);',
'''        inputTitle(fields, "Banco / emisor (tarjetas de crédito de México)");
        Spinner bank = new Spinner(this);
        ArrayAdapter<String> bankAdapter = new ArrayAdapter<>(this,
            android.R.layout.simple_spinner_dropdown_item, MEXICAN_ISSUERS);
        bank.setAdapter(bankAdapter);
        if (edit) {
            for (int i = 1; i < MEXICAN_ISSUERS.length; i++) {
                if (MEXICAN_ISSUERS[i].equalsIgnoreCase(card.name.trim())) {
                    bank.setSelection(i);
                    break;
                }
            }
        }
        fields.addView(bank, margins(-1, dp(46), 0, 0));''', "dropdown banco")

rep('            String name = bank.getText().toString().trim();',
'''            if (bank.getSelectedItemPosition() <= 0) {
                toast("Selecciona un banco del listado.");
                return;
            }
            String name = MEXICAN_ISSUERS[bank.getSelectedItemPosition()];''', "validación dropdown")
rep('            if (name.isEmpty()) { bank.setError("Escribe el banco"); return; }\n','', "validación vieja")

rep('        if (s.contains("mercado")) return "mercado";',
'''        if (s.contains("mercado")) return "mercado";
        if (s.contains("hsbc")) return "hsbc";
        if (s.contains("santander")) return "santander";
        if (s.contains("banorte")) return "banorte";''', "keys logos nuevos")
rep('            case "mercadolibre": return new int[]{0xFF12396D, 0xFF315B96};',
'''            case "mercadolibre": return new int[]{0xFF12396D, 0xFF315B96};
            case "hsbc": return new int[]{0xFF3C4450, 0xFF626976};
            case "santander": return new int[]{0xFFB50F20, 0xFFE7273A};
            case "banorte": return new int[]{0xFF7F1232, 0xFFBC244D};''', "colores logos nuevos")

# Acceso visible desde Mis tarjetas, incluso cuando todavía no haya tarjetas.
rep('        List<Models.Card> cards = store.cards();\n        sectionTitle("Mis tarjetas  ·  " + cards.size());',
'''        body.addView(button("Seguridad y eliminación de datos", false,
            v -> showPrivacyDialog()), margins(-1, dp(47), 10, 2));
        List<Models.Card> cards = store.cards();
        sectionTitle("Mis tarjetas  ·  " + cards.size());''', "acceso a seguridad")

# Botón redundante dentro de la pantalla calendario para recuperar el acceso.
rep('        body.addView(button("Sincronizar mis pagos ahora", false, v -> syncAll(true)),\n                margins(-1, dp(48), 9, 0));',
'''        body.addView(button("Sincronizar mis pagos ahora", false, v -> syncAll(true)),
                margins(-1, dp(48), 9, 0));
        body.addView(button("Privacidad y eliminación de datos", false, v -> showPrivacyDialog()),
                margins(-1, dp(48), 10, 0));''', "acceso desde calendario")

privacy_methods = r'''
    private EditText passwordInput(String hint) {
        EditText field = textInput(hint, "");
        field.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        field.setSingleLine(true);
        return field;
    }

    private void showPrivacyDialog() {
        boolean configured = PrivacyGuard.isConfigured(this);
        new AlertDialog.Builder(this)
            .setTitle("Seguridad y datos")
            .setMessage("La contraseña protege únicamente la acción de borrar todo. " +
                "No cifra los datos almacenados en el teléfono.")
            .setItems(configured
                ? new String[]{"Cambiar contraseña de borrado", "Eliminar todos los datos"}
                : new String[]{"Crear contraseña de borrado", "Eliminar todos los datos"}, (d, selection) -> {
                if (selection == 0) {
                    if (configured) changeDeletePassword();
                    else setupDeletePassword();
                } else if (!configured) {
                    new AlertDialog.Builder(this).setTitle("Primero crea una contraseña")
                        .setMessage("Para poder borrar todos los datos debes configurar una contraseña y volver a ingresar a esta opción.")
                        .setNegativeButton("Cancelar", null)
                        .setPositiveButton("Crear contraseña", (dlg, which) -> setupDeletePassword()).show();
                } else confirmDeleteAll();
            })
            .setNegativeButton("Cerrar", null).show();
    }

    private void setupDeletePassword() {
        LinearLayout form = dialogContent();
        form.addView(label("Crea una contraseña de al menos 6 caracteres. " +
            "La necesitarás para eliminar todos los registros.", 13, MUTED, false));
        inputTitle(form, "Nueva contraseña");
        EditText first = passwordInput("Contraseña");
        form.addView(first);
        inputTitle(form, "Confirmar contraseña");
        EditText again = passwordInput("Repetir contraseña");
        form.addView(again);
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle("Proteger el borrado de datos").setView(form)
            .setNegativeButton("Cancelar", null).setPositiveButton("Guardar", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String a = first.getText().toString(), b = again.getText().toString();
            if (a.length() < 6) { first.setError("Mínimo 6 caracteres"); return; }
            if (!a.equals(b)) { again.setError("Las contraseñas no coinciden"); return; }
            try {
                PrivacyGuard.save(this, a.toCharArray());
                dialog.dismiss();
                toast("Contraseña de borrado configurada.");
            } catch (Exception ex) { toast("No se pudo crear la contraseña."); }
        }));
        dialog.show();
    }

    private void changeDeletePassword() {
        LinearLayout form = dialogContent();
        inputTitle(form, "Contraseña actual");
        EditText old = passwordInput("Actual");
        form.addView(old);
        inputTitle(form, "Contraseña nueva");
        EditText next = passwordInput("Mínimo 6 caracteres");
        form.addView(next);
        inputTitle(form, "Repetir contraseña nueva");
        EditText confirmation = passwordInput("Repetir");
        form.addView(confirmation);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Cambiar contraseña")
            .setView(form).setNegativeButton("Cancelar", null)
            .setPositiveButton("Cambiar", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            if (!PrivacyGuard.verify(this, old.getText().toString().toCharArray())) {
                old.setError("Contraseña actual incorrecta"); return;
            }
            String newValue = next.getText().toString();
            if (newValue.length() < 6) { next.setError("Mínimo 6 caracteres"); return; }
            if (!newValue.equals(confirmation.getText().toString())) {
                confirmation.setError("Las contraseñas no coinciden"); return;
            }
            try {
                PrivacyGuard.save(this, newValue.toCharArray());
                dialog.dismiss();
                toast("Contraseña actualizada.");
            } catch (Exception ex) { toast("No se pudo cambiar la contraseña."); }
        }));
        dialog.show();
    }

    private void confirmDeleteAll() {
        LinearLayout form = dialogContent();
        form.addView(label("Esta acción es irreversible. Eliminará todas las tarjetas, pagos, " +
            "ajustes y la contraseña. También intentará borrar los eventos de calendario " +
            "creados por CrediAgenda.", 13, RED, false));
        inputTitle(form, "Contraseña de borrado");
        EditText entered = passwordInput("Introduce tu contraseña");
        form.addView(entered);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Eliminar todos mis datos")
            .setView(form).setNegativeButton("Cancelar", null)
            .setPositiveButton("Continuar", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            if (!PrivacyGuard.verify(this, entered.getText().toString().toCharArray())) {
                entered.setError("Contraseña incorrecta"); return;
            }
            dialog.dismiss();
            new AlertDialog.Builder(this).setTitle("Última confirmación")
                .setMessage("Se borrarán permanentemente todas las tarjetas y pagos de esta aplicación. No se pueden recuperar. ¿Confirmas?")
                .setNegativeButton("Conservar mis datos", null)
                .setPositiveButton("BORRAR TODO", (d, which) -> eraseEverything()).show();
        }));
        dialog.show();
    }

    private void eraseEverything() {
        List<Models.Payment> entries = store.allPayments();
        int notRemoved = 0;
        for (Models.Payment p : entries) {
            if (p.eventId > 0 && !CalendarSync.removeEvent(this, p)) notRemoved++;
        }
        if (notRemoved > 0) {
            int count = notRemoved;
            new AlertDialog.Builder(this).setTitle("Hay eventos que no pudieron borrarse")
                .setMessage("No se pudieron eliminar " + count + " eventos en tu calendario. " +
                    "Puedes conservar los registros para reintentar o borrar solo los datos locales. " +
                    "En este último caso los eventos podrían permanecer en Samsung Calendar.")
                .setNegativeButton("Conservar registros", null)
                .setPositiveButton("Borrar solo datos locales", (d, which) -> eraseLocalData()).show();
        } else eraseLocalData();
    }

    private void eraseLocalData() {
        try {
            store.clearAllData();
            getPreferences(MODE_PRIVATE).edit().clear().commit();
            getSharedPreferences(CalendarSync.PREFS, MODE_PRIVATE).edit().clear().commit();
            PrivacyGuard.clear(this);
            selectedCardId = -1;
            visibleMonth = YearMonth.now();
            activeTab = NAV_CARDS;
            render();
            new AlertDialog.Builder(this).setTitle("Datos eliminados")
                .setMessage("Se borraron todas las tarjetas, los pagos y la configuración local. La contraseña de borrado también se restableció.")
                .setPositiveButton("Entendido", null).show();
        } catch (Exception ex) {
            new AlertDialog.Builder(this).setTitle("No se pudo completar el borrado")
                .setMessage("Android no permitió completar la operación. Conserva tus datos y vuelve a intentarlo.")
                .setPositiveButton("Entendido", null).show();
        }
    }
'''

idx=j.rfind("\n}")
if idx < 0: raise RuntimeError("Missing final brace")
j=j[:idx] + "\n" + privacy_methods + j[idx:]
main.write_text(j)
if "    void clearAllData()" in s: raise RuntimeError("Already patched")
idx=s.rfind("\n}")
s=s[:idx]+'''
    void clearAllData() {
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            db.delete("payments", null, null);
            db.delete("cards", null, null);
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }
'''+s[idx:]
store.write_text(s)

security_java=r'''package mx.crediagenda.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * Bloquea el borrado masivo, sin solicitar claves bancarias.
 * NO cifra la base de datos.
 */
final class PrivacyGuard {
    private static final String PREFS = "crediagenda_delete_password";
    private static final String SALT = "salt_v1";
    private static final String HASH = "hash_v1";
    private static final int ITERATIONS = 150000;
    private static final int KEY_BITS = 256;

    private static SharedPreferences pref(Context c) {
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    static boolean isConfigured(Context context) {
        return pref(context).contains(SALT) && pref(context).contains(HASH);
    }

    private static byte[] derive(char[] password, byte[] salt) throws Exception {
        PBEKeySpec spec = new PBEKeySpec(password, salt, ITERATIONS, KEY_BITS);
        try { return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded(); }
        finally { spec.clearPassword(); }
    }

    static void save(Context context, char[] password) throws Exception {
        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        byte[] hash = derive(password, salt);
        boolean success = pref(context).edit()
            .putString(SALT, Base64.encodeToString(salt, Base64.NO_WRAP))
            .putString(HASH, Base64.encodeToString(hash, Base64.NO_WRAP))
            .commit();
        Arrays.fill(hash, (byte)0);
        Arrays.fill(password, '\0');
        if (!success) throw new IllegalStateException("No se guardó la contraseña");
    }

    static boolean verify(Context context, char[] password) {
        if (!isConfigured(context)) { Arrays.fill(password, '\0'); return false; }
        try {
            byte[] salt = Base64.decode(pref(context).getString(SALT, ""), Base64.NO_WRAP);
            byte[] savedHash = Base64.decode(pref(context).getString(HASH, ""), Base64.NO_WRAP);
            byte[] incoming = derive(password, salt);
            boolean accepted = MessageDigest.isEqual(incoming, savedHash);
            Arrays.fill(incoming, (byte)0);
            return accepted;
        } catch (Exception e) { return false; }
        finally { Arrays.fill(password, '\0'); }
    }

    static void clear(Context context) {
        pref(context).edit().clear().commit();
    }
}
'''
(root / "PrivacyGuard.java").write_text(security_java)
print("Actualización 2.1: catálogo desplegable, protección de borrado por contraseña, limpieza de pagos y eventos.")
