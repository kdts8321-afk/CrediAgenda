"""Personal 2.5: apodos por tarjeta y eventos de pago rojo de día completo."""
from pathlib import Path
import re

root = Path("app/src/main/java/mx/crediagenda/app")
models_path = root / "Models.java"
store_path = root / "Store.java"
main_path = root / "MainActivity.java"
calendar_path = root / "CalendarSync.java"
m = models_path.read_text()
s = store_path.read_text()
j = main_path.read_text()
c = calendar_path.read_text()

def replacement(text, old, new, label, expected=1):
    count = text.count(old)
    if count != expected:
        raise RuntimeError("Falla reemplazo %s: esperado %s, encontrado %s" % (label, expected, count))
    return text.replace(old, new)

# Un campo opcional, respetando la base de datos actual y su historial de cortes.
m = replacement(m, "        String network;\n", "        String network;\n        String nickname;\n", "Modelo nickname")
m = replacement(m,
    "Card(long id, String name, String last4, String digitalLast4, int color, String network) {",
    "Card(long id, String name, String last4, String digitalLast4, int color, String network, String nickname) {",
    "Constructor tarjeta")
m = replacement(m,
    '            this.network = network == null ? "" : network;',
    '            this.network = network == null ? "" : network;\n            this.nickname = nickname == null ? "" : nickname;',
    "Asignar nickname")
models_path.write_text(m)

s = replacement(s, 'super(context, "crediagenda.db", null, 4)',
    'super(context, "crediagenda.db", null, 5)', "Schema version")
s = replacement(s,
    "color INTEGER NOT NULL DEFAULT 0, network TEXT NOT NULL DEFAULT ''",
    "color INTEGER NOT NULL DEFAULT 0, network TEXT NOT NULL DEFAULT '', nickname TEXT NOT NULL DEFAULT ''",
    "Crear columna nickname")
# insert migration inside onUpgrade, after existing migrations.
rx = re.compile(r"(?ms)(    @Override public void onUpgrade\(SQLiteDatabase db, int oldVersion, int newVersion\) \{)(.*?)(^    \})")
found = rx.search(s)
if not found: raise RuntimeError("No se encontro onUpgrade de DB")
if 'oldVersion < 4' not in found.group(2): raise RuntimeError("Falta migración de cortes")
migration = """
        if (oldVersion < 5) db.execSQL("ALTER TABLE cards ADD COLUMN nickname TEXT NOT NULL DEFAULT '';");
"""
s = s[:found.start()] + found.group(1) + found.group(2) + migration + '\n' + found.group(3) + s[found.end():]
s = replacement(s, 'SELECT id,name,last4,digital_last4,color,network FROM cards',
    'SELECT id,name,last4,digital_last4,color,network,nickname FROM cards',
    "SELECT apodos", expected=2)
s = replacement(s, "c.getInt(4), c.getString(5)))",
    "c.getInt(4), c.getString(5), c.getString(6)))",
    "Modelo en lista")
s = replacement(s, "c.getInt(4), c.getString(5));",
    "c.getInt(4), c.getString(5), c.getString(6));",
    "Modelo individual")
s = replacement(s, 'cv.put("network", card.network);',
    'cv.put("network", card.network);\n        cv.put("nickname", card.nickname);',
    "Guardar apodo")
store_path.write_text(s)

# Mostrar el apodo sin sustituir el banco ni las terminaciones, y permitir editarlo.
j = replacement(j, '        surface.addView(header);\n',
    '''        surface.addView(header);
        if (c.nickname != null && !c.nickname.trim().isEmpty()) {
            TextView nick = label(c.nickname.trim(), 16, WHITE, true);
            surface.addView(nick, margins(-1, -2, 4, 2));
        }
''', "Mostrar apodo en tarjetas")
j = replacement(j,
    '        fields.addView(bank, margins(-1, dp(46), 0, 0));',
    '''        fields.addView(bank, margins(-1, dp(46), 0, 0));
        inputTitle(fields, "Apodo de la tarjeta · opcional");
        EditText nickname = textInput("Ej. BBv2, BMEX 1, Nu diaria",
            edit ? card.nickname : "");
        nickname.setSingleLine(true);
        nickname.setFilters(new InputFilter[]{new InputFilter.LengthFilter(24)});
        fields.addView(nickname);
        fields.addView(label("Se usará para identificar los pagos en el calendario: P + apodo.",
            12, MUTED, false), margins(-1, -2, 5, 0));''',
    "Campo de apodo")
j = replacement(j,
    '            String name = MEXICAN_ISSUERS[bank.getSelectedItemPosition()];',
    '''            String name = MEXICAN_ISSUERS[bank.getSelectedItemPosition()];
            String nick = nickname.getText().toString().trim().replace("\\n", " ").replace("\\r", " ");''',
    "Leer apodo")
j = replacement(j,
    'new Models.Card(edit ? card.id : 0, name, physical, td, bankColor(name), selectedNetwork);',
    'new Models.Card(edit ? card.id : 0, name, physical, td, bankColor(name), selectedNetwork, nick);',
    "Guardar tarjeta con apodo")
# Ensanchamos identificacion en lista de fechas de corte, sin alterar funcionamiento.
j = replacement(j,
    '            area.addView(label(card.name + "  •••• " + card.last4, 17, INK, true));',
    '''            String cardLabel = card.nickname == null || card.nickname.trim().isEmpty()
                ? card.name : card.nickname.trim() + " · " + card.name;
            area.addView(label(cardLabel + "  •••• " + card.last4, 17, INK, true));''',
    "Apodo en fechas de corte")
main_path.write_text(j)

# Día completo en UTC, para prevenir desplazamientos por zona horaria.
c = replacement(c,
    "import java.time.ZoneId;\nimport java.time.ZonedDateTime;",
    "import java.time.LocalDate;\nimport java.time.ZoneOffset;",
    "Importación para día completo")
c = replacement(c, "import java.util.TimeZone;\n", "", "Eliminar timezone de hora local")
c = replacement(c,
    '''    private static long startMillis(Models.Payment payment) {
        ZonedDateTime when = payment.date().atTime(9, 0).atZone(ZoneId.systemDefault());
        return when.toInstant().toEpochMilli();
    }''',
    '''    private static long startMillis(Models.Payment payment) {
        return payment.date().atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
    }

    private static long endMillis(Models.Payment payment) {
        return payment.date().plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
    }''',
    "Fecha todo el día UTC")
c = replacement(c,
    '''    private static String title(Models.Payment p, Models.Card card) {
        return (p.paid ? "Pagado: " : "Pagar: ") + card.name + Models.masked(card) + " · " + Models.money(p.amountCents);
    }''',
    '''    private static String title(Models.Payment p, Models.Card card) {
        String nick = card.nickname == null ? "" : card.nickname.trim();
        // Siempre P + apodo. Si no hay apodo, mostramos banco y cuatro dígitos.
        return "P " + (nick.isEmpty() ? card.name + " " + card.last4 : nick);
    }''',
    "Título P apodo")
c = replacement(c,
    '''        values.put(CalendarContract.Events.DTEND, startMillis(payment) + 30L * 60_000L);
        values.put(CalendarContract.Events.EVENT_TIMEZONE, TimeZone.getDefault().getID());''',
    '''        values.put(CalendarContract.Events.DTEND, endMillis(payment));
        values.put(CalendarContract.Events.ALL_DAY, 1);
        values.put(CalendarContract.Events.EVENT_TIMEZONE, "UTC");
        values.put(CalendarContract.Events.EVENT_END_TIMEZONE, "UTC");
        // Color del EVENTO, nunca del calendario completo.
        values.put(CalendarContract.Events.EVENT_COLOR, 0xFFE53935);''',
    "Evento rojo todo el día")
c = replacement(c,
    '''                .putExtra(CalendarContract.EXTRA_EVENT_END_TIME, start + 30L * 60_000L);''',
    '''                .putExtra(CalendarContract.EXTRA_EVENT_END_TIME, endMillis(payment))
                .putExtra(CalendarContract.EXTRA_EVENT_ALL_DAY, true);''',
    "Intent manual todo el día")
calendar_path.write_text(c)

assert 'CalendarSync.upsert' not in (root / "MainActivity.java").read_text().split("    /** Las fechas de corte")[1].split("\n}")[0]
print("Personal 2.5: apodo opcional en la base, fecha de corte intacta, eventos P + apodo, todo el día y rojos.")
