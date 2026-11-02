"""Validaciones de Personal 2.5 (apodos, migración de DB y calendario)."""
from pathlib import Path
import re

root=Path("app/src/main/java/mx/crediagenda/app")
m=(root/"Models.java").read_text()
s=(root/"Store.java").read_text()
j=(root/"MainActivity.java").read_text()
c=(root/"CalendarSync.java").read_text()

assert ('null, 5)' in s or 'null, 6)' in s)
assert "nickname TEXT NOT NULL DEFAULT ''" in s
assert "oldVersion < 5" in s
assert "SELECT id,name,last4,digital_last4,color,network,nickname FROM cards" in s
assert 'cv.put("nickname", card.nickname)' in s
assert 'String nickname;' in m
assert 'this.nickname = nickname' in m
assert '"Apodo de la tarjeta · opcional"' in j
assert 'String nick = nickname.getText()' in j
assert 'new Models.Card(edit ? card.id : 0, name, physical, td, bankColor(name), selectedNetwork, nick)' in j
assert 'for (Models.Payment pay : store.paymentsForCard(id)) CalendarSync.upsert(this, store, pay);' in j
assert 'card.nickname' in j
assert 'return "P " + (nick.isEmpty() ? card.name + " " + card.last4 : nick);' in c
assert 'CalendarContract.Events.ALL_DAY, 1' in c
assert ('CalendarContract.Events.EVENT_COLOR, PREFERRED_RED' in c and
        'CalendarContract.Events.EVENT_COLOR_KEY' in c)
assert 'CalendarContract.Events.EVENT_TIMEZONE, "UTC"' in c
assert 'CalendarContract.Events.DTEND, endMillis(payment)' in c
assert 'plusDays(1).atStartOfDay(ZoneOffset.UTC)' in c
assert 'CalendarContract.EXTRA_EVENT_ALL_DAY, true' in c
assert 'resolver.update(CalendarContract.Events.CONTENT_URI' in c
assert '"card_cutoffs"' in s and 'cutoffDate(' in s
assert 'CalendarSync.upsert' not in j[j.index('    /** Las fechas de corte'):j.rfind('\n}')]
print("TEST PERSONAL 2.5 OK: apodos persistentes; eventos todo el dia y color por evento; re-sincronización tras editar apodo; cortes independientes.")
