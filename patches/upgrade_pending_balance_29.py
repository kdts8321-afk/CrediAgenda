"""Personal 2.9: el saldo pendiente solo se muestra mientras el pago está pendiente.

No cambia la estructura de la base de datos, no invierte valores guardados ni
elimina pagos, y no modifica las fechas de pago o corte.
"""
from pathlib import Path

path=Path("app/src/main/java/mx/crediagenda/app/MainActivity.java")
source=path.read_text()

def once(before, after, tag):
    global source
    count=source.count(before)
    if count != 1:
        raise RuntimeError(f"{tag}: se esperó 1 aparición y hubo {count}")
    source=source.replace(before, after, 1)

once(
'''        int paidCount = 0;
        long pending = 0;
        long paidTotal = 0;
        for (Models.Payment p : payments) {
            if (p.paid) { paidCount++; paidTotal += p.amountCents; }
            else pending += p.amountCents;
        }''',
'''        int paidCount = 0;
        long pending = 0;
        for (Models.Payment p : payments) {
            // El saldo pendiente incluye ÚNICAMENTE los pagos no realizados.
            if (p.paid) paidCount++;
            else pending += p.amountCents;
        }''',
"total pendiente")

once(
'''        LinearLayout a = miniStat("Pagado este mes", Models.money(paidTotal), GREEN);
        LinearLayout b = miniStat("Por pagar", String.valueOf(payments.size() - paidCount), ORANGE);''',
'''        LinearLayout a = miniStat("Pagos realizados", String.valueOf(paidCount), GREEN);
        LinearLayout b = miniStat("Por pagar", String.valueOf(payments.size() - paidCount), ORANGE);''',
"pagados ya no muestran un saldo monetario")

once(
'''        TextView money = label(Models.money(p.amountCents), 17, INK, true);
        money.setGravity(Gravity.RIGHT);
        line.addView(money);''',
'''        // Conservar en SQLite el importe original para poder deshacer «Ya pagué».
        // Visualmente no debe reaparecer un saldo cuando ya está liquidado.
        TextView money = label(p.paid
            ? "✓ Liquidado"
            : "Pendiente: " + Models.money(p.amountCents),
            p.paid ? 13 : 16, p.paid ? GREEN : INK, true);
        money.setGravity(Gravity.RIGHT);
        line.addView(money);''',
"saldo visible solo al estar pendiente")

# Verificar que se marca pagado / pendiente cambiando solamente la bandera.
assert "        p.paid = !p.paid;" in source
assert "        store.savePayment(p);" in source
assert 'cv.put("paid", payment.paid ? 1 : 0)' in Path(
    "app/src/main/java/mx/crediagenda/app/Store.java").read_text()

path.write_text(source)
print("Personal 2.9: los importes se conservan y solo se muestran como saldo si el pago está pendiente.")
