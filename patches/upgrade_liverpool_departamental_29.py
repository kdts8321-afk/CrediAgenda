"""Personal 2.9: Liverpool como emisor y Departamental como tipo de red.

Se aplica despues de las migraciones 2.1 a 2.9. No modifica pagos guardados.
"""
from pathlib import Path

main = Path("app/src/main/java/mx/crediagenda/app/MainActivity.java")
code = main.read_text(encoding="utf-8")

def once(before, after, label):
    global code
    count = code.count(before)
    if count != 1:
        raise RuntimeError(f"{label}: se esperaba 1 ocurrencia, hubo {count}")
    code = code.replace(before, after, 1)

once(
    '"Banorte", "Stori", "Nu", "Mercado Libre"',
    '"Banorte", "Stori", "Nu", "Mercado Libre", "Liverpool"',
    "Liverpool en seleccion de emisores")

once(
    '        if (s.contains("mercado")) return "mercado";',
    '        if (s.contains("mercado")) return "mercado";\n        if (s.contains("liverpool")) return "liverpool";',
    "Liverpool en identificador visual")

once(
    '            case "mercadolibre": return new int[]{0xFF12396D, 0xFF315B96};',
    '            case "mercadolibre": return new int[]{0xFF12396D, 0xFF315B96};\n            case "liverpool": return new int[]{0xFF6B173F, 0xFFA42B65};',
    "Gradiente caracteristico Liverpool")

once(
    '        if (lower.contains("banorte")) return 0xFFC92138;',
    '        if (lower.contains("banorte")) return 0xFFC92138;\n        if (lower.contains("liverpool")) return 0xFF9E245D;',
    "Color guardado de Liverpool")

once(
    'String[] networks = {"Sin especificar", "Visa", "Mastercard"};',
    'String[] networks = {"Sin especificar", "Visa", "Mastercard", "Departamental"};',
    "Tipo de tarjeta departamental")

once(
    '        if (edit && card.network.equalsIgnoreCase("Mastercard")) network.setSelection(2);',
    '        if (edit && card.network.equalsIgnoreCase("Mastercard")) network.setSelection(2);\n        if (edit && card.network.equalsIgnoreCase("Departamental")) network.setSelection(3);',
    "Restaurar tipo Departamental al editar")

once(
    'network.getSelectedItemPosition() == 2 ? "Mastercard" : "";',
    'network.getSelectedItemPosition() == 2 ? "Mastercard" :\n                network.getSelectedItemPosition() == 3 ? "Departamental" : "";',
    "Guardar tipo Departamental")

once(
    '        surface.addView(header);',
    '''        surface.addView(header);
        if ("Departamental".equalsIgnoreCase(c.network)) {
            TextView departmental = label("TARJETA DEPARTAMENTAL", 11, WHITE, true);
            departmental.setLetterSpacing(0.08f);
            surface.addView(departmental, margins(-1, -2, 8, 0));
        }''',
    "Etiqueta visual Departamental")

# Los botones deben identificar la ACCION y no el estado previo.
assert 'p.paid ? "↺  Pendiente" : "✓  Ya pagué"' in code
assert "        p.paid = !p.paid;" in code
assert 'long pending = PaymentRules.pendingCents(payments);' in code
assert 'PaymentRules.isPending(p)' in code
assert '"Liverpool"' in code and '"Departamental"' in code

main.write_text(code, encoding="utf-8")
print("Personal 2.9: Liverpool, tipo Departamental, y Pendiente/Ya pagué verificados")
