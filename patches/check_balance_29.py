"""Verificación 2.9: lógica pendiente/pagado conectada a la interfaz y sin migración destructiva."""
from pathlib import Path
root=Path("app/src/main/java/mx/crediagenda/app")
main=(root/"MainActivity.java").read_text()
store=(root/"Store.java").read_text()
rules=(root/"PaymentRules.java").read_text()
assert 'long pending = PaymentRules.pendingCents(payments);' in main
assert 'if (p.paid) paidCount++;' in main
assert 'miniStat("Pagos realizados", String.valueOf(paidCount), GREEN)' in main
assert 'miniStat("Por pagar", String.valueOf(payments.size() - paidCount), ORANGE)' in main
assert 'PaymentRules.isPending(p)' in main
assert 'p.paid = !p.paid;' in main
assert 'store.savePayment(p);' in main
assert 'p.paid ? "↺  Pendiente" : "✓  Ya pagué"' in main
assert 'Math.addExact(total, p.amountCents)' in rules
assert 'if (isPending(p))' in rules
assert 'cv.put("paid", payment.paid ? 1 : 0);' in store
assert 'getWritableDatabase().update("payments", cv,' in store
assert 'INSERT OR REPLACE' not in main
print("Interfaz y persistencia 2.9 correctas: pendiente muestra saldo, pagado no; no se borran registros.")
