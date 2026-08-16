# ¡Che! — Spanisch-Sprechtrainer

Version 0.5.3

Eine Single-File-Web-App (`index.html`) zum Spanisch-Sprechen-Üben, gebaut für Kai:
Rioplatense (Voseo, Uruguay) als Standard, Spanien-Modus zuschaltbar.

## Features

- **Voice-Konversation**: Web Speech API (Mikrofon → Transkript → Claude → Antwort vorgelesen)
- **8 Szenarien**: Asado mit der Familie, Surfshop Zarautz, Camping-Check-in, Pintxos-Bar, Mercado, Mate-Runde, frei, Zufall
- **Voseo-Modus** 🇺🇾 / **España-Modus** 🇪🇸 umschaltbar
- **Korrekturen**: max. 2 pro Turn, dezent als Chip, Erklärung auf Deutsch
- **Fehler-Gedächtnis**: wiederkehrende Fehler landen in localStorage und fließen in künftige Gespräche ein (der Tutor baut sie unauffällig wieder ein)
- **Konversation → Übungen**: Grammatikfehler speisen das 🏋️ Grammatik-Training (Muster-Analyse), fehlende/falsche Wörter aus Gesprächen landen automatisch im 🃏 Vokabel-Deck
- **Gespräche fortsetzen**: die letzten 12 Unterhaltungen werden lokal gespeichert und sind vom Home-Screen aus fortsetzbar
- **„Über dich"**: frei editierbares Profil in den Einstellungen, das der Tutor immer kennt
- **Lektionen aus ChatGPT-Voice-Sessions**: Kai spricht mit ChatGPT Voice und lässt sich die
  Findings als Markdown geben (`~/Documents/Codex/<datum>/<projekt>/outputs/*.md`). Der Stoff
  wandert in den `LESSONS`-Block in `index.html` und taucht dreifach auf: Vokabeln automatisch
  im 🃏 Deck, Grammatik im 📖 Spickzettel, plus eigene Übungskarte unter „Aus deinen Sessions",
  in der der Tutor genau dieses Material abfragt und danach frei darüber weiterredet.
- **Modelle**: Claude Opus 5 (Standard) oder Haiku 4.5 (schnell/günstig), umschaltbar

## Lektionen automatisch importieren

Kai spricht mit ChatGPT Voice und lässt sich am Ende eine Zusammenfassung nach fester
Vorlage geben ([`docs/chatgpt-vorlage.md`](docs/chatgpt-vorlage.md)). Die Datei landet unter
`~/Documents/Codex/<datum>/<projekt>/outputs/*.md`.

```bash
python3 tools/import_lessons.py --dry-run    # zeigt nur, was passieren würde
python3 tools/import_lessons.py              # schreibt den LESSONS-Block, bumpt die Patch-Version
```

Der Importer ersetzt ausschließlich den Bereich zwischen `LEKTIONEN:START` und
`LEKTIONEN:ENDE` in `index.html`. Dateien, die nicht zur Vorlage passen, werden mit
Begründung übersprungen statt halb übernommen.

Automatisch läuft das per launchd alle 30 Minuten
(`~/Scripts/che-lektionen/import.sh`, Label `com.kaibachler.che-lektionen`): Trockenlauf,
und nur bei echten Änderungen Commit und Push. Der Job hält an, wenn die Arbeitskopie
nicht sauber ist oder `origin/main` voraus ist, und meldet sich per iMessage bei neuer
Lektion, ungültiger Datei oder Fehler.

## Technik

- Kein Build, kein Backend. Direkter Browser-Call an `api.anthropic.com/v1/messages`
  mit Header `anthropic-dangerous-direct-browser-access: true`.
- API-Key nur im localStorage des Geräts.
- Structured Outputs (`output_config.format`, JSON-Schema) für zuverlässige
  `{respuesta, correcciones[]}`-Antworten.
- Prompt Caching: stabiler System-Block mit `cache_control`, dynamische
  Fehlerliste als zweiter Block dahinter (Cache bleibt erhalten).
- Opus 5: `effort: "low"` für schnelle Gesprächsantworten.

## Lokal starten

```bash
python3 -m http.server 8742 --directory .
```

Dann http://localhost:8742 öffnen. **Achtung:** Mikrofon (Spracherkennung)
funktioniert nur über `https://` oder `localhost` — fürs iPhone braucht die App
also ein Hosting mit HTTPS (z.B. GitHub Pages).

## iPhone-Installation (nach Hosting)

1. URL in Safari öffnen
2. Teilen → „Zum Home-Bildschirm"
3. API-Key einmalig eintragen — fertig
