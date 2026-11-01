from pathlib import Path

root = Path("app/src/main/java/mx/crediagenda/app")
store_file = root / "Store.java"
main_file = root / "MainActivity.java"
s = store_file.read_text()
j = main_file.read_text()

def replace_once(contents, before, after, name):
    if before not in contents:
        raise RuntimeError("No se encontro ancla: " + name)
    return contents.replace(before, after, 1)

s = replace_once(s, 'super(context, "crediagenda.db", null, 3)',
    'super(context, "crediagenda.db", null, 4)', "version DB 4")

# Nueva tabla independiente de payments: no event_id, nunca se sincroniza con calendarios.
s = replace_once(s, '        db.execSQL("CREATE INDEX ix_payments_due ON payments(due_date)");',
    '''        db.execSQL("CREATE TABLE card_cutoffs (" +
            "card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE, " +
            "month TEXT NOT NULL, cutoff_date TEXT NOT NULL, " +
            "PRIMARY KEY(card_id, month))");
        db.execSQL("CREATE INDEX ix_payments_due ON payments(due_date)");''', "tabla nueva")

s = replace_once(s,
    '        if (oldVersion < 3) db.execSQL("ALTER TABLE cards ADD COLUMN network TEXT NOT NULL DEFAULT \\'\\'");',
    '''        if (oldVersion < 3) db.execSQL("ALTER TABLE cards ADD COLUMN network TEXT NOT NULL DEFAULT ''");
        if (oldVersion < 4) db.execSQL("CREATE TABLE IF NOT EXISTS card_cutoffs (" +
            "card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE, " +
            "month TEXT NOT NULL, cutoff_date TEXT NOT NULL, " +
            "PRIMARY KEY(card_id, month))");''', "migracion schema 4")

s = replace_once(s, '            db.delete("payments", null, null);\n            db.delete("cards", null, null);',
    '''            db.delete("payments", null, null);
            db.delete("card_cutoffs", null, null);
            db.delete("cards", null, null);''', "borrado total")

store_code = '''
    // Fecha de corte explícita por mes; los pagos y sus eventos se guardan aparte.
    String cutoffDate(long cardId, String month) {
        try (Cursor cursor = getReadableDatabase().rawQuery(
            "SELECT cutoff_date FROM card_cutoffs WHERE card_id=? AND month=?",
            new String[]{String.valueOf(cardId), month})) {
            return cursor.moveToFirst() ? cursor.getString(0) : null;
        }
    }

    void saveCutoffDate(long cardId, String month, String date) {
        java.time.LocalDate parsed = java.time.LocalDate.parse(date);
        java.time.YearMonth selected = java.time.YearMonth.parse(month);
        if (!java.time.YearMonth.from(parsed).equals(selected)) {
            throw new IllegalArgumentException("La fecha debe pertenecer al mes indicado");
        }
        if (card(cardId) == null) throw new IllegalArgumentException("La tarjeta no existe");
        ContentValues values = new ContentValues();
        values.put("card_id", cardId);
        values.put("month", month);
        values.put("cutoff_date", date);
        getWritableDatabase().insertWithOnConflict(
            "card_cutoffs", null, values, SQLiteDatabase.CONFLICT_REPLACE);
    }

    void removeCutoffDate(long cardId, String month) {
        getWritableDatabase().delete("card_cutoffs", "card_id=? AND month=?",
            new String[]{String.valueOf(cardId), month});
    }
'''
idx = s.rfind("\n}")
if idx < 0: raise RuntimeError("Cierre de Store.java no encontrado")
s = s[:idx] + store_code + s[idx:]
store_file.write_text(s)

j = replace_once(j, "    private static final int NAV_CALENDAR = 2;",
    "    private static final int NAV_CALENDAR = 2;\n    private static final int NAV_CUTOFFS = 3;", "navegacion cortes")
j = replace_once(j, '    private YearMonth visibleMonth = YearMonth.now();',
    '    private YearMonth visibleMonth = YearMonth.now();\n    private YearMonth cutoffMonth = YearMonth.now();',
    "mes independiente")
j = replace_once(j,
    '        else if (activeTab == NAV_CARDS) { if (selectedCardId > 0) showCardDetail(); else showCards(); }\n        else showCalendarSettings();',
    '''        else if (activeTab == NAV_CARDS) { if (selectedCardId > 0) showCardDetail(); else showCards(); }
        else if (activeTab == NAV_CUTOFFS) showCutoffs();
        else showCalendarSettings();''', "render cortes")

j = replace_once(j, '        addNav("▣  Tarjetas", NAV_CARDS);\n        addNav("▦  Calendario", NAV_CALENDAR);',
    '        addNav("▣  Tarjetas", NAV_CARDS);\n        addNav("✂  Cortes", NAV_CUTOFFS);\n        addNav("▦  Calendario", NAV_CALENDAR);',
    "cuarta pestana")

# En detalle se identifica el corte y se permite editar desde esta tarjeta.
j = replace_once(j,
    '        body.addView(label("Movimientos y pagos", 23, INK, true), margins(-1, -2, 8, 4));',
    '''        addCutoffInfo(c, cutoffMonth, true);
        body.addView(label("Movimientos y pagos", 23, INK, true), margins(-1, -2, 8, 4));''',
    "detalle tarjeta")

# En tarjeta se indica el corte del mes actual, sin inventar día para tarjetas no configuradas.
j = replace_once(j,
    '        surface.addView(footer, margins(-1, -2, 16, 0));',
    '''        surface.addView(footer, margins(-1, -2, 16, 0));
        String cutoff = store.cutoffDate(c.id, YearMonth.now().toString());
        surface.addView(label(cutoff == null ? "Corte este mes: sin registrar" :
            "Corte este mes: " + shortDate(LocalDate.parse(cutoff)),
            12, 0xFFE2EDFF, false), margins(-1, -2, 9, 0));''',
    "fecha corte en vista tarjeta")

cutoff_code = r'''
    /** Las fechas de corte NO se convierten en eventos y NO piden permisos de calendario. */
    private void showCutoffs() {
        headline("Fechas de corte", "Consulta y actualiza el corte de cada tarjeta, mes por mes.");
        LinearLayout monthBar = row();
        TextView previous = label("‹", 33, INDIGO, true);
        previous.setGravity(Gravity.CENTER);
        previous.setOnClickListener(v -> { cutoffMonth = cutoffMonth.minusMonths(1); render(); });
        monthBar.addView(previous, new LinearLayout.LayoutParams(dp(48), dp(53)));
        TextView title = label(monthLabel(cutoffMonth), 18, INK, true);
        title.setGravity(Gravity.CENTER);
        monthBar.addView(title, new LinearLayout.LayoutParams(0, -2, 1));
        TextView next = label("›", 33, INDIGO, true);
        next.setGravity(Gravity.CENTER);
        next.setOnClickListener(v -> { cutoffMonth = cutoffMonth.plusMonths(1); render(); });
        monthBar.addView(next, new LinearLayout.LayoutParams(dp(48), dp(53)));
        body.addView(monthBar, margins(-1, -2, 2, 10));
        body.addView(label("Las fechas de corte no se agregan a Samsung Calendar y no generan recordatorios.",
            13, MUTED, false), margins(-1, -2, 0, 10));
        List<Models.Card> cards = store.cards();
        if (cards.isEmpty()) {
            showEmpty("Aún no hay tarjetas", "Primero registra una tarjeta para guardar sus fechas de corte.");
            body.addView(button("Ir a mis tarjetas", false, v -> {
                selectedCardId = -1; activeTab = NAV_CARDS; render();
            }), margins(-1, dp(48), 9, 0));
            return;
        }
        int registered = 0;
        for (Models.Card card : cards) {
            String value = store.cutoffDate(card.id, cutoffMonth.toString());
            if (value != null) registered++;
            addCutoffInfo(card, cutoffMonth, false);
        }
        body.addView(label("Fechas registradas: " + registered + " de " + cards.size() +
            ". Las fechas de meses anteriores se conservan.", 12, MUTED, false),
            margins(-1, -2, 12, 0));
    }

    private void addCutoffInfo(Models.Card card, YearMonth month, boolean inDetail) {
        String value = store.cutoffDate(card.id, month.toString());
        LinearLayout area = panel();
        if (inDetail) {
            area.addView(label("Fecha de corte", 19, INK, true));
            area.addView(label("Mes: " + monthLabel(month), 13, MUTED, false),
                margins(-1, -2, 4, 0));
        } else {
            area.addView(label(card.name + "  •••• " + card.last4, 17, INK, true));
        }
        area.addView(label(value == null ? "Sin fecha de corte registrada" :
            shortDate(LocalDate.parse(value)), value == null ? 15 : 22,
            value == null ? MUTED : INDIGO, value != null), margins(-1, -2, 12, 10));
        area.addView(button(value == null ? "Registrar corte" : "Cambiar fecha de corte",
            false, v -> editCutoffDate(card, month)), margins(-1, dp(45), 0, 0));
        if (value != null) {
            area.addView(button("Quitar fecha de corte de este mes", false, v -> {
                new AlertDialog.Builder(this)
                    .setTitle("¿Quitar esta fecha de corte?")
                    .setMessage("Se eliminará únicamente el corte de " + monthLabel(month) +
                        " de " + card.name + ". No afectará tus pagos.")
                    .setNegativeButton("Cancelar", null)
                    .setPositiveButton("Quitar", (dialog, which) -> {
                        store.removeCutoffDate(card.id, month.toString());
                        render();
                    }).show();
            }), margins(-1, dp(45), 8, 0));
        }
        body.addView(area, margins(-1, -2, 0, 13));
    }

    private void editCutoffDate(Models.Card card, YearMonth month) {
        String existing = store.cutoffDate(card.id, month.toString());
        LocalDate selected = existing == null ?
            month.atDay(Math.min(15, month.lengthOfMonth())) : LocalDate.parse(existing);
        DatePickerDialog picker = new DatePickerDialog(this, (view, year, monthIndex, day) -> {
            LocalDate newDate = LocalDate.of(year, monthIndex + 1, day);
            if (!YearMonth.from(newDate).equals(month)) {
                toast("Selecciona una fecha del mes indicado.");
                return;
            }
            try {
                store.saveCutoffDate(card.id, month.toString(), newDate.toString());
                // Deliberadamente no se usa CalendarSync: esta fecha es solo informativa.
                toast("Fecha de corte guardada para " + monthLabel(month));
                render();
            } catch (Exception ex) {
                toast("No se pudo guardar la fecha de corte.");
            }
        }, selected.getYear(), selected.getMonthValue()-1, selected.getDayOfMonth());
        picker.setTitle("Corte de " + card.name + " · " + monthLabel(month));
        picker.getDatePicker().setMinDate(month.atDay(1).atStartOfDay(
            java.time.ZoneId.systemDefault()).toInstant().toEpochMilli());
        // Se añade un día para evitar errores de zona horaria en el límite del mes.
        picker.getDatePicker().setMaxDate(month.plusMonths(1).atDay(1).atStartOfDay(
            java.time.ZoneId.systemDefault()).toInstant().toEpochMilli() - 1);
        picker.show();
    }
'''

# Añadir métodos al final de la clase sin depender de funciones de calendario.
last = j.rfind("\n}")
if last < 0: raise RuntimeError("Cierre de MainActivity.java no encontrado")
j = j[:last] + "\n" + cutoff_code + j[last:]
main_file.write_text(j)

# Comprobar que las fechas de corte no tengan event_id ni llamadas al calendario.
assert "CalendarSync" not in cutoff_code.replace("CalendarSync: esta fecha", "solo informativo: esta fecha")
assert "event_id" not in store_code
print("Fechas de corte 2.3: esquema v4, CRUD independiente, pestaña Cortes y detalle por tarjeta.")
