"""Personal 2.7: validación de cortes al mes siguiente y ciclo de vida de sesión."""
from pathlib import Path
root=Path("app/src/main/java/mx/crediagenda/app")
s=(root/"Store.java").read_text()
j=(root/"MainActivity.java").read_text()
calendar=(root/"CalendarSync.java").read_text()

assert "java.time.YearMonth actual = java.time.YearMonth.from(parsed);" in s
assert "actual.isBefore(selected) || actual.isAfter(selected.plusMonths(1))" in s
assert "month.plusMonths(2).atDay(1)" in j
assert "actualMonth.isBefore(month) || actualMonth.isAfter(month.plusMonths(1))" in j
assert "Ciclo: " in j
assert "formattedCutoff(value)" in j
assert "formattedCutoff(cutoff)" in j
assert "d MMM yyyy" in j
assert "onPause()" in j and "onStop()" in j and "onUserLeaveHint()" in j

pause=j[j.index("    @Override protected void onPause() {"):j.index("    @Override protected void onStop() {")]
stop=j[j.index("    @Override protected void onStop() {"):j.index("    @Override protected void onStop() {")+700]
assert "accessUnlocked = false" not in pause
assert "clearPendingAccess()" not in pause
assert "showAccessScreen()" not in pause
assert "accessUnlocked = false" in stop
assert "showAccessScreen()" in stop
assert "biometricCancellation" in stop
leave=j[j.index("    @Override protected void onUserLeaveHint() {"):j.index("    @Override protected void onStop() {")]
assert "accessUnlocked = false" in leave
assert "showAccessScreen()" in leave
assert "super.onUserLeaveHint()" in leave
assert "card_cutoffs" not in calendar
assert "CalendarSync.upsert" not in j[j.index("    /** Las fechas de corte"):j.rfind("\n}")]
print("VALIDACION 2.7 OK: corte ciclo noviembre -> diciembre y diciembre -> enero; sin calendario; seguridad tras salir, no por pausas.")
