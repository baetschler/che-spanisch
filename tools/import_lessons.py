#!/usr/bin/env python3
"""Importiert ChatGPT-Voice-Session-Notizen als Lektionen in index.html.

Quelle:  ~/Documents/Codex/<datum>/<projekt>/outputs/*.md  (Format: docs/chatgpt-vorlage.md)
Ziel:    der LESSONS-Block zwischen den Markern in index.html

Grundsatz: lieber eine Datei überspringen und melden als halbes Material einbauen.
Falsches Material im Training merkt man erst, wenn man es schon geübt hat.

Exit-Codes:  0 = nichts zu tun · 10 = Lektionen geändert · 1 = Fehler
Ungültige Dateien allein sind kein Fehler-Exit, sie stehen im Report.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

START = "/* == LEKTIONEN:START == */"
ENDE = "/* == LEKTIONEN:ENDE == */"
PFLICHTFELDER = ("id", "titel", "emoji", "fecha", "tema")


# ---------------------------------------------------------------- Markdown

def md_zu_html(text):
    """Sehr kleiner Markdown-Teilmenge-Konverter: **fett**, *kursiv*, Absätze."""
    absaetze = [a.strip() for a in re.split(r"\n\s*\n", text.strip()) if a.strip()]
    raus = []
    for a in absaetze:
        a = html.escape(" ".join(line.strip() for line in a.splitlines()))
        a = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", a)
        a = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", a)
        raus.append("<p>" + a + "</p>")
    return "".join(raus)


def frontmatter_lesen(zeilen):
    if not zeilen or zeilen[0].strip() != "---":
        return None, zeilen
    for i in range(1, len(zeilen)):
        if zeilen[i].strip() == "---":
            fm = {}
            for z in zeilen[1:i]:
                if ":" in z:
                    k, _, v = z.partition(":")
                    fm[k.strip().lower()] = v.strip()
            return fm, zeilen[i + 1:]
    return None, zeilen


def abschnitte_lesen(zeilen):
    """{'Vocabulario': [zeilen], ...} anhand der ##-Überschriften."""
    out, aktuell = {}, None
    for z in zeilen:
        m = re.match(r"^##\s+(.+?)\s*$", z)
        if m and not z.startswith("###"):
            aktuell = m.group(1).strip()
            out[aktuell] = []
        elif aktuell:
            out[aktuell].append(z)
    return out


def vokabeln_lesen(zeilen, warnungen):
    vokabeln = []
    for z in zeilen:
        z = z.strip()
        if not z.startswith("|"):
            continue
        spalten = [s.strip() for s in z.strip("|").split("|")]
        if len(spalten) < 3:
            warnungen.append(f"Vokabelzeile ohne drei Spalten übersprungen: {z[:50]}")
            continue
        es, de, ej = spalten[0], spalten[1], spalten[2]
        if set(es) <= set("-: ") or es.lower() in ("español", "espanol"):
            continue  # Trenn- oder Kopfzeile
        if not es or not de:
            warnungen.append(f"Vokabelzeile unvollständig übersprungen: {z[:50]}")
            continue
        vokabeln.append({"es": es, "de": de, "ej": ej})
    return vokabeln


def grammatik_lesen(zeilen, warnungen):
    punkte, titel, puffer = [], None, []

    def abschliessen():
        if titel is None:
            return
        rest, kurz = [], ""
        for z in puffer:
            m = re.match(r"^\s*\*\*Kurz:\*\*\s*(.+?)\s*$", z)
            if m:
                kurz = m.group(1)
            else:
                rest.append(z)
        if not kurz:
            warnungen.append(f"Grammatikpunkt '{titel}' ohne **Kurz:**-Zeile uebernommen")
        koerper = md_zu_html("\n".join(rest))
        if koerper:
            punkte.append({"t": titel, "resumen": kurz or titel, "html": koerper})
        else:
            warnungen.append(f"Grammatikpunkt '{titel}' ohne Erklaerung uebersprungen")

    for z in zeilen:
        m = re.match(r"^###\s+(.+?)\s*$", z)
        if m:
            abschliessen()
            titel, puffer = m.group(1).strip(), []
        elif titel is not None:
            puffer.append(z)
    abschliessen()
    return punkte


def saetze_lesen(zeilen):
    out = []
    for z in zeilen:
        m = re.match(r"^\s*[-*]\s+(.+?)\s*$", z)
        if m:
            out.append(m.group(1))
    return out


def praxis_lesen(zeilen, warnungen):
    out = []
    for z in zeilen:
        m = re.match(r"^\s*(?:\d+[.)]|[-*])\s+(.+?)\s*$", z)
        if not m:
            continue
        inhalt = m.group(1)
        if "→" not in inhalt:
            warnungen.append(f"Übung ohne → übersprungen: {inhalt[:50]}")
            continue
        hueco, _, sol = inhalt.partition("→")
        hueco, sol = hueco.strip(), sol.strip()
        if not hueco or not sol:
            warnungen.append(f"Übung unvollständig übersprungen: {inhalt[:50]}")
            continue
        out.append({"hueco": hueco, "sol": sol})
    return out


def datei_lesen(pfad):
    """-> (lektion|None, warnungen, fehler)."""
    warnungen, fehler = [], []
    zeilen = pfad.read_text(encoding="utf-8").splitlines()

    fm, rest = frontmatter_lesen(zeilen)
    if fm is None:
        return None, warnungen, ["kein Frontmatter (--- am Dateianfang)"]
    fehlend = [f for f in PFLICHTFELDER if not fm.get(f)]
    if fehlend:
        return None, warnungen, ["Frontmatter unvollständig: " + ", ".join(fehlend)]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", fm["fecha"]):
        return None, warnungen, [f"fecha '{fm['fecha']}' ist nicht YYYY-MM-DD"]
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", fm["id"]):
        return None, warnungen, [f"id '{fm['id']}' ist kein Slug (a-z, 0-9, Bindestrich)"]

    abschnitte = abschnitte_lesen(rest)

    def hole(*namen):
        for n in namen:
            for k in abschnitte:
                if k.lower() == n.lower():
                    return abschnitte[k]
        return []

    vokabeln = vokabeln_lesen(hole("Vocabulario"), warnungen)
    if not vokabeln:
        fehler.append("Abschnitt '## Vocabulario' fehlt oder hat keine gueltige Tabellenzeile")
    grammatik = grammatik_lesen(hole("Gramática", "Gramatica"), warnungen)
    if not grammatik:
        fehler.append("Abschnitt '## Gramatica' fehlt oder hat keinen ###-Punkt")
    if fehler:
        return None, warnungen, fehler

    return {
        "id": f"{fm['id']}-{fm['fecha']}",
        "emoji": fm["emoji"],
        "t": fm["titel"],
        "d": f"ChatGPT-Session vom {fm['fecha'][8:10]}.{fm['fecha'][5:7]}. — jetzt aktiv üben",
        "fecha": fm["fecha"],
        "tema": fm["tema"],
        "vocab": vokabeln,
        "gramatica": grammatik,
        "frases": saetze_lesen(hole("Frases útiles", "Frases utiles")),
        "practica": praxis_lesen(hole("Práctica", "Practica"), warnungen),
        "_slug": fm["id"],
        "_quelle": str(pfad),
    }, warnungen, []


# ---------------------------------------------------------------- Ausgabe

def js_block(lektionen):
    def s(x):
        return json.dumps(x, ensure_ascii=False)

    z = [START, "const LESSONS = ["]
    for l in lektionen:
        z.append("  {")
        z.append(f"    id: {s(l['id'])},")
        z.append(f"    emoji: {s(l['emoji'])},")
        z.append(f"    t: {s(l['t'])},")
        z.append(f"    d: {s(l['d'])},")
        z.append(f"    fecha: {s(l['fecha'])},")
        z.append(f"    tema: {s(l['tema'])},")
        z.append("    vocab: [")
        for v in l["vocab"]:
            z.append(f"      {{ es: {s(v['es'])}, de: {s(v['de'])}, ej: {s(v['ej'])} }},")
        z.append("    ],")
        z.append("    gramatica: [")
        for g in l["gramatica"]:
            z.append(f"      {{ t: {s(g['t'])}, resumen: {s(g['resumen'])},")
            z.append(f"        html: {s(g['html'])} }},")
        z.append("    ],")
        z.append("    frases: [")
        for f in l["frases"]:
            z.append(f"      {s(f)},")
        z.append("    ],")
        z.append("    practica: [")
        for p in l["practica"]:
            z.append(f"      {{ hueco: {s(p['hueco'])}, sol: {s(p['sol'])} }},")
        z.append("    ],")
        z.append("  },")
    z.append("];")
    z.append(ENDE)
    return "\n".join(z)


def version_bumpen(app_html, readme):
    """Patch-Version an allen drei Stellen gleichzeitig hochziehen."""
    t = app_html.read_text(encoding="utf-8")
    m = re.search(r'const APP_VERSION = "(\d+)\.(\d+)\.(\d+)"', t)
    if not m:
        return None
    neu = f"{m.group(1)}.{m.group(2)}.{int(m.group(3)) + 1}"
    alt = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    t = t.replace(f'const APP_VERSION = "{alt}"', f'const APP_VERSION = "{neu}"')
    t = t.replace(f"¡Che! v{alt}", f"¡Che! v{neu}")
    app_html.write_text(t, encoding="utf-8")
    if readme.exists():
        r = readme.read_text(encoding="utf-8")
        readme.write_text(r.replace(f"Version {alt}", f"Version {neu}", 1), encoding="utf-8")
    return neu


def main():
    p = argparse.ArgumentParser(description="ChatGPT-Session-Notizen als Lektionen importieren")
    p.add_argument("--source", default=str(Path.home() / "Documents/Codex"))
    p.add_argument("--app", default=str(Path(__file__).resolve().parent.parent / "index.html"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    quelle, app_html = Path(args.source), Path(args.app)
    readme = app_html.parent / "README.md"

    if not quelle.is_dir():
        print(f"FEHLER: Quellordner nicht gefunden: {quelle}")
        return 1
    if not app_html.is_file():
        print(f"FEHLER: index.html nicht gefunden: {app_html}")
        return 1

    dateien = sorted(f for f in quelle.rglob("*.md") if f.parent.name == "outputs")
    lektionen, uebersprungen, alle_warnungen = [], [], []

    for f in dateien:
        try:
            lektion, warnungen, fehler = datei_lesen(f)
        except Exception as e:                                    # defekte Datei kippt nie den Lauf
            uebersprungen.append((f, [f"nicht lesbar: {e}"]))
            continue
        alle_warnungen += [f"{f.name}: {w}" for w in warnungen]
        if lektion:
            lektionen.append(lektion)
        else:
            uebersprungen.append((f, fehler))

    # Gleiche id mehrfach: die neuere fecha gewinnt
    nach_slug = {}
    for l in sorted(lektionen, key=lambda x: x["fecha"]):
        nach_slug[l["_slug"]] = l
    lektionen = sorted(nach_slug.values(), key=lambda x: x["fecha"], reverse=True)

    text = app_html.read_text(encoding="utf-8")
    if START not in text or ENDE not in text:
        print("FEHLER: Marker LEKTIONEN:START/ENDE fehlen in index.html")
        return 1
    vorher = text[text.index(START):text.index(ENDE) + len(ENDE)]
    nachher = js_block(lektionen)

    # Schutzschalter: aus dem Nichts alle Lektionen loeschen ist praktisch immer ein
    # Zugriffs- oder Pfadproblem (z.B. launchd ohne Full Disk Access auf ~/Documents),
    # nie eine echte Absicht. Lieber abbrechen als die App leerraeumen.
    if not lektionen and "id:" in vorher:
        print("FEHLER: keine gueltige Lektion gefunden, aber index.html enthaelt welche.")
        print(f"        Quelle lesbar? {quelle} — {len(dateien)} Datei(en) gesehen.")
        print("        Nichts geschrieben.")
        return 1

    print(f"{len(dateien)} Datei(en) gefunden, {len(lektionen)} Lektion(en) gültig, "
          f"{len(uebersprungen)} übersprungen")
    for f, gruende in uebersprungen:
        print(f"  ÜBERSPRUNGEN {f.name}: {'; '.join(gruende)}")
    for w in alle_warnungen:
        print(f"  hinweis {w}")
    for l in lektionen:
        print(f"  ok {l['id']}: {len(l['vocab'])} Vokabeln, {len(l['gramatica'])} Grammatik, "
              f"{len(l['frases'])} Sätze, {len(l['practica'])} Übungen")

    if vorher == nachher:
        print("Lektionen unverändert.")
        return 0
    if args.dry_run:
        print("(dry-run, nichts geschrieben)")
        return 10

    app_html.write_text(text.replace(vorher, nachher), encoding="utf-8")
    version = version_bumpen(app_html, readme)
    print(f"index.html aktualisiert, Version jetzt {version}")
    return 10


if __name__ == "__main__":
    sys.exit(main())
