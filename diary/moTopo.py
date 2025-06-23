import polib

# Άνοιξε το .po αρχείο
po = polib.pofile("locale/en/LC_MESSAGES/django.po")

# Αφαίρεσε διπλότυπα
seen = set()
cleaned = polib.POFile()
cleaned.metadata = po.metadata or {
    "Project-Id-Version": "Reflectivo",
    "Language": "en",
    "Content-Type": "text/plain; charset=UTF-8",
    "Content-Transfer-Encoding": "8bit",
}

for entry in po:
    if entry.msgid not in seen:
        seen.add(entry.msgid)
        cleaned.append(entry)

# Αποθήκευσε καθαρό .po και δημιούργησε .mo
cleaned.save("locale/en/LC_MESSAGES/final_django.po")
cleaned.save_as_mofile("locale/en/LC_MESSAGES/final_django.mo")

print("✅ Έτοιμα τα αρχεία .po και .mo!")
