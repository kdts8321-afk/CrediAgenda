"""Personal 2.7: corte en el mes del ciclo o el siguiente; sesión bloqueada al salir realmente."""
from pathlib import Path

root = Path("app/src/main/java/mx/crediagenda/app")
main = root / "MainActivity.java"
store = root / "Store.java"
j=main.read_text()
s=store.read_text()

def replace1(body, old, new, tag):
    count=body.count(old)
    if count!=1: raise RuntimeError("%s: se esperó una ocurrencia, hay %d" % (tag,count))
    return body.replace(old,new,1)

s=replace1(s,
    '''        if (!java.time.YearMonth.from(parsed).equals(selected)) {
            throw new IllegalArgumentException("La fecha debe pertenecer al mes indicado");
        }''',
    '''        java.time.YearMonth actual = java.time.YearMonth.from(parsed);
        // El ciclo mostrado puede cerrar en su propio mes o en el siguiente.
        // Ejemplo: ciclo 2026-11 -> corte entre 2026-11-01 y 2026-12-31.
        if (actual.isBefore(selected) || actual.isAfter(selected.plusMonths(1))) {
            throw new IllegalArgumentException("Corte fuera del ciclo o del mes siguiente");
        }''',
    "validacion corte proximo mes")

j=replace1(j,
    '''    @Override protected void onPause() {
        accessUnlocked = false;
        clearPendingAccess();
        if (!biometricPromptActive && store != null && body != null) showAccessScreen();
        super.onPause();
    }''',
    '''    @Override protected void onPause() {
        // Una pausa momentanea (p. ej., dialogos del sistema o ventanas internas)
        // no es una salida de la aplicacion. La sesión se cierra en onStop.
        super.onPause();
    }''',
    "no bloquear en pausas momentaneas")

# onStop sigue bloqueando por completo al salir de Personal.
assert '    @Override protected void onStop() {' in j
assert '        accessUnlocked = false;\n        // Si el usuario se cambia de app durante el diálogo' in j

j=replace1(j,
    '''        headline("Fechas de corte", "Consulta y actualiza el corte de cada tarjeta, mes por mes.");''',
    '''        headline("Fechas de corte", "Registra los cortes de cada ciclo. Pueden caer en este mes o en el siguiente.");''',
    "explicacion fechas")

j=replace1(j,
    '''        body.addView(label("Las fechas de corte no se agregan a Samsung Calendar y no generan recordatorios.",
            13, MUTED, false), margins(-1, -2, 0, 10));''',
    '''        body.addView(label("El mes de arriba indica el ciclo. Puedes elegir una fecha del propio mes o del siguiente. No se agrega a Samsung Calendar.",
            13, MUTED, false), margins(-1, -2, 0, 10));''',
    "indicar mes de ciclo")

j=replace1(j,
    '''            area.addView(label("Mes: " + monthLabel(month), 13, MUTED, false),''',
    '''            area.addView(label("Ciclo: " + monthLabel(month), 13, MUTED, false),''',
    "nombre ciclo")

j=replace1(j,
    '''        area.addView(label(value == null ? "Sin fecha de corte registrada" :
            shortDate(LocalDate.parse(value)), value == null ? 15 : 22,''',
    '''        area.addView(label(value == null ? "Sin fecha de corte registrada" :
            formattedCutoff(value), value == null ? 15 : 22,''',
    "mostrar fecha completa")

j=replace1(j,
    '''        surface.addView(label(cutoff == null ? "Corte este mes: sin registrar" :
            "Corte este mes: " + shortDate(LocalDate.parse(cutoff)),''',
    '''        surface.addView(label(cutoff == null ? "Corte ciclo actual: sin registrar" :
            "Corte ciclo actual: " + formattedCutoff(cutoff),''',
    "mostrar corte en tarjeta")

j=replace1(j,
    '''            if (!YearMonth.from(newDate).equals(month)) {
                toast("Selecciona una fecha del mes indicado.");
                return;
            }''',
    '''            YearMonth actualMonth = YearMonth.from(newDate);
            if (actualMonth.isBefore(month) || actualMonth.isAfter(month.plusMonths(1))) {
                toast("Selecciona una fecha de este mes o del siguiente.");
                return;
            }''',
    "validacion picker")

j=replace1(j,
    '''                toast("Fecha de corte guardada para " + monthLabel(month));''',
    '''                toast("Corte del ciclo " + monthLabel(month) + ": " + formattedCutoff(newDate.toString()));''',
    "notificacion corte")

j=replace1(j,
    '''        picker.setTitle("Corte de " + card.name + " · " + monthLabel(month));''',
    '''        picker.setTitle("Corte del ciclo " + monthLabel(month) + " · " + card.name);''',
    "titulo picker")

j=replace1(j,
    '''        picker.getDatePicker().setMaxDate(month.plusMonths(1).atDay(1).atStartOfDay(
            java.time.ZoneId.systemDefault()).toInstant().toEpochMilli() - 1);''',
    '''        picker.getDatePicker().setMaxDate(month.plusMonths(2).atDay(1).atStartOfDay(
            java.time.ZoneId.systemDefault()).toInstant().toEpochMilli() - 1);''',
    "rango fecha mes siguiente")

anchor='    private void editCutoffDate(Models.Card card, YearMonth month) {'
j=replace1(j,anchor,
    '''    private String formattedCutoff(String isoDate) {
        LocalDate date = LocalDate.parse(isoDate);
        return date.format(java.time.format.DateTimeFormatter.ofPattern(
            "d MMM yyyy", new Locale("es", "MX")));
    }

'''+anchor,"formato corte con año")

main.write_text(j)
store.write_text(s)
print("Personal 2.7: ciclo y siguiente mes habilitados; PIN/patrón/biometría solo al salir de la app.")
