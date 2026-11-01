from pathlib import Path
import re

root = Path("app/src/main/java/mx/crediagenda/app")
main = root / "MainActivity.java"
models = root / "Models.java"
store = root / "Store.java"

def must_replace(s, a, b, label):
    if a not in s:
        raise RuntimeError("No se encontro: " + label)
    return s.replace(a, b)

m = models.read_text()
m = must_replace(m, "        int color;\n\n        Card(long id, String name, String last4, String digitalLast4, int color) {",
    '        int color;\n        String network;\n\n        Card(long id, String name, String last4, String digitalLast4, int color, String network) {',
    "modelo campo")
m = must_replace(m, "            this.color = color;\n        }\n    }\n\n    static final class Payment",
    '            this.color = color;\n            this.network = network == null ? "" : network;\n        }\n    }\n\n    static final class Payment',
    "modelo constructor")
models.write_text(m)

s = store.read_text()
s = must_replace(s, 'super(context, "crediagenda.db", null, 2)', 'super(context, "crediagenda.db", null, 3)', "DB version")
s = must_replace(s, 'digital_last4 TEXT NOT NULL DEFAULT \'\', color INTEGER NOT NULL DEFAULT 0)',
    'digital_last4 TEXT NOT NULL DEFAULT \'\', color INTEGER NOT NULL DEFAULT 0, network TEXT NOT NULL DEFAULT \'\')', "create DB")
s = must_replace(s, 'if (oldVersion < 2) db.execSQL("ALTER TABLE cards ADD COLUMN digital_last4 TEXT NOT NULL DEFAULT \'\'");',
    'if (oldVersion < 2) db.execSQL("ALTER TABLE cards ADD COLUMN digital_last4 TEXT NOT NULL DEFAULT \'\'");\n        if (oldVersion < 3) db.execSQL("ALTER TABLE cards ADD COLUMN network TEXT NOT NULL DEFAULT \'\'");', "migracion")
s = must_replace(s, 'SELECT id,name,last4,digital_last4,color FROM cards', 'SELECT id,name,last4,digital_last4,color,network FROM cards', "select network")
s = must_replace(s, 'c.getLong(0), c.getString(1), c.getString(2), c.getString(3), c.getInt(4)))',
    'c.getLong(0), c.getString(1), c.getString(2), c.getString(3), c.getInt(4), c.getString(5)))', "card query all")
s = must_replace(s, 'c.getLong(0), c.getString(1), c.getString(2), c.getString(3), c.getInt(4));',
    'c.getLong(0), c.getString(1), c.getString(2), c.getString(3), c.getInt(4), c.getString(5));', "card query one")
s = must_replace(s, 'cv.put("color", card.color);', 'cv.put("color", card.color);\n        cv.put("network", card.network);', "network save")
store.write_text(s)

j = main.read_text()
j = must_replace(j, 'import android.widget.FrameLayout;', 'import android.widget.FrameLayout;\nimport android.widget.ImageView;', "import")
j = must_replace(j, '    private YearMonth visibleMonth = YearMonth.now();',
    '    private YearMonth visibleMonth = YearMonth.now();\n    private long selectedCardId = -1;', "selectedCardId")
j = must_replace(j, 'else if (activeTab == NAV_CARDS) showCards();',
    'else if (activeTab == NAV_CARDS) { if (selectedCardId > 0) showCardDetail(); else showCards(); }', "render cards")
j = must_replace(j, '            activeTab = tab;\n            render();',
    '            activeTab = tab;\n            if (tab == NAV_CARDS) selectedCardId = -1;\n            render();', "nav cards")
j = must_replace(j, '        b.setTextAllCaps(false);', '        b.setAllCaps(false);', "compile button")
j = must_replace(j, '        if (lower.contains("nu")) return 0xFF7A39B2;',
    '        if (lower.equals("nu") || lower.contains("nubank")) return 0xFF7928B1;\n        if (lower.contains("stori")) return 0xFF006957;\n        if (lower.contains("mercado")) return 0xFF0084B9;', "bank colors")

start = j.index('    private void showCards() {')
end = j.index('    private EditText textInput(', start)
new_cards = r'''    private String bankKey(String name) {
        String s = name.toLowerCase(Locale.ROOT).trim();
        if (s.contains("bbva") || s.contains("bancomer")) return "bbva";
        if (s.contains("banamex") || s.contains("citi")) return "banamex";
        if (s.contains("stori")) return "stori";
        if (s.equals("nu") || s.contains("nubank")) return "nu";
        if (s.contains("mercado libre")) return "mercadolibre";
        if (s.contains("mercado")) return "mercado";
        return "otro";
    }

    private int[] cardColors(String key) {
        switch (key) {
            case "bbva": return new int[]{0xFF073D94, 0xFF1366D3};
            case "banamex": return new int[]{0xFF092B55, 0xFF164474};
            case "stori": return new int[]{0xFF003E42, 0xFF077766};
            case "nu": return new int[]{0xFF6520A1, 0xFF9850C5};
            case "mercado": return new int[]{0xFF087BA8, 0xFF159CCB};
            case "mercadolibre": return new int[]{0xFF12396D, 0xFF315B96};
            default: return new int[]{0xFF293955, 0xFF526589};
        }
    }

    private GradientDrawable cardBackground(String key) {
        GradientDrawable gd = new GradientDrawable(GradientDrawable.Orientation.TL_BR, cardColors(key));
        gd.setCornerRadius(dp(23));
        return gd;
    }

    private ImageView logoImage(String asset, int width, int height) {
        int id = getResources().getIdentifier(asset, "drawable", getPackageName());
        if (id == 0) return null;
        ImageView image = new ImageView(this);
        image.setImageResource(id);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setAdjustViewBounds(true);
        image.setPadding(dp(8), dp(8), dp(8), dp(8));
        image.setBackground(shape(WHITE, 11));
        image.setLayoutParams(new LinearLayout.LayoutParams(dp(width), dp(height)));
        return image;
    }

    private String networkKey(String network) {
        if (network == null) return "";
        if (network.equalsIgnoreCase("Visa")) return "visa";
        if (network.equalsIgnoreCase("Mastercard")) return "mastercard";
        return "";
    }

    private long defaultCardId(List<Models.Card> cards) {
        long saved = getPreferences(MODE_PRIVATE).getLong("default_card", -1);
        for (Models.Card c : cards) if (c.id == saved) return saved;
        return cards.isEmpty() ? -1 : cards.get(0).id;
    }

    private void cardPreview(Models.Card c) {
        String key = bankKey(c.name);
        LinearLayout surface = column();
        surface.setPadding(dp(21), dp(18), dp(21), dp(16));
        surface.setBackground(cardBackground(key));
        surface.setElevation(dp(4));
        surface.setClipToOutline(true);

        LinearLayout header = row();
        ImageView bankLogo = logoImage("bank_" + key, 148, 46);
        if (bankLogo != null) {
            header.addView(bankLogo);
        } else {
            TextView name = label(c.name.toUpperCase(new Locale("es", "MX")), 19, WHITE, true);
            header.addView(name, new LinearLayout.LayoutParams(0, -2, 1));
        }
        View gap = new View(this);
        header.addView(gap, new LinearLayout.LayoutParams(0, dp(3), 1));
        String network = networkKey(c.network);
        if (!network.isEmpty()) {
            ImageView networkLogo = logoImage("network_" + network, 63, 44);
            if (networkLogo != null) header.addView(networkLogo);
            else header.addView(label(c.network, 12, WHITE, true));
        }
        surface.addView(header);
        TextView fLabel = label("TARJETA FÍSICA", 10, 0xFFD1E2FA, true);
        fLabel.setLetterSpacing(0.11f);
        surface.addView(fLabel, margins(-1, -2, 25, 2));
        surface.addView(label("••••  " + c.last4, 24, WHITE, true));

        if (c.digitalLast4 != null && !c.digitalLast4.isEmpty()) {
            LinearLayout digit = row();
            TextView digitTitle = label("DIGITAL", 11, 0xFFD9E9FA, true);
            digit.addView(digitTitle);
            TextView digitValue = label("••••  " + c.digitalLast4, 15, WHITE, true);
            LinearLayout.LayoutParams valueParams = new LinearLayout.LayoutParams(-2, -2);
            valueParams.leftMargin = dp(13);
            digit.addView(digitValue, valueParams);
            surface.addView(digit, margins(-1, -2, 8, 0));
        }

        LinearLayout footer = row();
        if (c.id == defaultCardId(store.cards())) {
            TextView def = label("  ★  Predeterminada  ", 10, WHITE, true);
            def.setBackground(shape(0x557FFFFF, 8));
            footer.addView(def);
        }
        View space = new View(this);
        footer.addView(space, new LinearLayout.LayoutParams(0, dp(1), 1));
        footer.addView(label("Ver pagos  ›", 12, 0xFFE9F1FF, true));
        surface.addView(footer, margins(-1, -2, 16, 0));
        surface.setContentDescription(c.name + ", física terminación " + c.last4 +
            (c.digitalLast4.isEmpty() ? "" : ", digital terminación " + c.digitalLast4) +
            (c.network.isEmpty() ? "" : ", " + c.network) + ". Ver detalle.");
        surface.setClickable(true);
        surface.setOnClickListener(v -> { selectedCardId = c.id; activeTab = NAV_CARDS; render(); });
        body.addView(surface, margins(-1, -2, 0, 17));
    }

    private void showCards() {
        headline("Mis tarjetas", "Tus tarjetas, identificadas de un vistazo.");
        body.addView(button("+  Agregar tarjeta", true, v -> showCardDialog(null)),
                margins(-1, dp(50), 0, 3));
        List<Models.Card> cards = store.cards();
        sectionTitle("Mis tarjetas  ·  " + cards.size());
        if (cards.isEmpty()) {
            showEmpty("Agrega tu primera tarjeta", "Solo guarda el banco y los últimos cuatro dígitos; la tarjeta digital es opcional.");
            return;
        }
        for (Models.Card c : cards) cardPreview(c);
        TextView safe = label("Solo guardamos las terminaciones que escribes. No introduzcas números completos, NIP o CVV.", 12, MUTED, false);
        body.addView(safe, margins(-1, -2, 6, 0));
    }

    private void showCardDetail() {
        Models.Card c = store.card(selectedCardId);
        if (c == null) { selectedCardId = -1; showCards(); return; }
        TextView back = label("‹  Todas mis tarjetas", 15, INDIGO, true);
        back.setOnClickListener(v -> { selectedCardId = -1; render(); });
        body.addView(back, margins(-1, -2, 0, 14));
        cardPreview(c);
        body.addView(label("Movimientos y pagos", 23, INK, true), margins(-1, -2, 8, 4));
        List<Models.Payment> related = store.paymentsForCard(c.id);
        Collections.sort(related, (a, b) -> b.dueDate.compareTo(a.dueDate));
        int pendingCount = 0;
        long pendingAmount = 0;
        for (Models.Payment p : related) if (!p.paid) { pendingCount++; pendingAmount += p.amountCents; }
        LinearLayout stats = miniStat("Por pagar · " + pendingCount, Models.money(pendingAmount), INDIGO);
        body.addView(stats, margins(-1, -2, 10, 0));
        body.addView(button("+  Programar pago de esta tarjeta", true, v -> startPaymentDialog(null)),
                margins(-1, dp(52), 13, 7));
        if (related.isEmpty()) {
            showEmpty("Sin pagos registrados", "Programa el primer vencimiento de esta tarjeta para verlo aquí.");
        } else {
            for (Models.Payment p : related) addPaymentRow(p, c, false);
        }
        sectionTitle("Configuración de tarjeta");
        if (defaultCardId(store.cards()) != c.id) {
            body.addView(button("★  Hacer predeterminada", false, v -> {
                getPreferences(MODE_PRIVATE).edit().putLong("default_card", c.id).apply();
                render();
            }), margins(-1, dp(50), 0, 7));
        } else {
            body.addView(label("★  Esta es tu tarjeta predeterminada", 13, GREEN, true),
                margins(-1, -2, 5, 11));
        }
        body.addView(button("Editar datos de tarjeta", false, v -> showCardDialog(c)),
                margins(-1, dp(50), 0, 7));
        body.addView(button("Eliminar tarjeta", false, v -> confirmDeleteCard(c)),
                margins(-1, dp(50), 0, 12));
    }

'''
j = j[:start] + new_cards + j[end:]

start = j.index("    private void showCardDialog(")
end = j.index("    private void confirmDeleteCard(", start)
new_dialog = r'''    private void showCardDialog(Models.Card card) {
        boolean edit = card != null;
        LinearLayout fields = dialogContent();
        inputTitle(fields, "Banco o emisor");
        EditText bank = textInput("BBVA, Banamex, Stori, Nu, Mercado Libre...", edit ? card.name : "");
        bank.setFilters(new InputFilter[]{new InputFilter.LengthFilter(35)});
        fields.addView(bank);
        inputTitle(fields, "Red de la tarjeta");
        Spinner network = new Spinner(this);
        String[] networks = {"Sin especificar", "Visa", "Mastercard"};
        ArrayAdapter<String> networkAdapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, networks);
        network.setAdapter(networkAdapter);
        if (edit && card.network.equalsIgnoreCase("Visa")) network.setSelection(1);
        if (edit && card.network.equalsIgnoreCase("Mastercard")) network.setSelection(2);
        fields.addView(network, margins(-1, dp(46), 0, 0));
        inputTitle(fields, "Últimos 4 dígitos de tarjeta física");
        EditText last4 = textInput("3456", edit ? card.last4 : "");
        last4.setInputType(InputType.TYPE_CLASS_NUMBER);
        last4.setFilters(new InputFilter[]{new InputFilter.LengthFilter(4)});
        fields.addView(last4);
        inputTitle(fields, "Últimos 4 dígitos de tarjeta digital · opcional");
        EditText digital = textInput("6656", edit ? card.digitalLast4 : "");
        digital.setInputType(InputType.TYPE_CLASS_NUMBER);
        digital.setFilters(new InputFilter[]{new InputFilter.LengthFilter(4)});
        fields.addView(digital);
        fields.addView(label("Si no tienes tarjeta digital, deja ese campo vacío y no aparecerá en la tarjeta.", 12, MUTED, false),
                margins(-1, -2, 13, 8));
        ScrollView scroll = new ScrollView(this);
        scroll.addView(fields);
        AlertDialog dlg = new AlertDialog.Builder(this)
            .setTitle(edit ? "Editar tarjeta" : "Nueva tarjeta")
            .setView(scroll)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Guardar", null).create();
        dlg.setOnShowListener(ignore -> dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String name = bank.getText().toString().trim();
            String physical = last4.getText().toString().trim();
            String td = digital.getText().toString().trim();
            String selectedNetwork = network.getSelectedItemPosition() == 1 ? "Visa" :
                network.getSelectedItemPosition() == 2 ? "Mastercard" : "";
            if (name.isEmpty()) { bank.setError("Escribe el banco"); return; }
            if (!physical.matches("[0-9]{4}")) { last4.setError("Escribe exactamente 4 dígitos"); return; }
            if (!td.isEmpty() && !td.matches("[0-9]{4}")) {
                digital.setError("La terminación digital debe tener 4 dígitos"); return;
            }
            Models.Card saved = new Models.Card(edit ? card.id : 0, name, physical, td, bankColor(name), selectedNetwork);
            long id = store.saveCard(saved);
            if (edit && CalendarSync.hasPermissions(this) && CalendarSync.chosenCalendar(this) >= 0) {
                for (Models.Payment pay : store.paymentsForCard(id)) CalendarSync.upsert(this, store, pay);
            }
            dlg.dismiss();
            render();
        }));
        dlg.show();
    }

'''
j = j[:start] + new_dialog + j[end:]
j = must_replace(j, "store.deleteCard(card.id); render();", "store.deleteCard(card.id); selectedCardId = -1; render();", "delete card")
j = must_replace(j, 'if (original != null && original.cardId == c.id) selected = i;',
    'if (original != null && original.cardId == c.id) selected = i;\n            else if (original == null && activeTab == NAV_CARDS && selectedCardId == c.id) selected = i;', "selected spinner")
j = must_replace(j, '            activeTab = NAV_SUMMARY;\n            render();\n            if (CalendarSync.hasPermissions(this)',
    '            activeTab = selectedCardId > 0 && activeTab == NAV_CARDS ? NAV_CARDS : NAV_SUMMARY;\n            render();\n            if (CalendarSync.hasPermissions(this)', "persist detail")
main.write_text(j)
print("Applied card redesign, bank and network support, detail page, schema 3")
