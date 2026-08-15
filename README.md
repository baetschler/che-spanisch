# ¡Che! — Spanisch-Sprechtrainer

Version 0.2.0

Eine Single-File-Web-App (`index.html`) zum Spanisch-Sprechen-Üben, gebaut für Kai:
Rioplatense (Voseo, Uruguay) als Standard, Spanien-Modus zuschaltbar.

## Features

- **Voice-Konversation**: Web Speech API (Mikrofon → Transkript → Claude → Antwort vorgelesen)
- **8 Szenarien**: Asado mit der Familie, Surfshop Zarautz, Camping-Check-in, Pintxos-Bar, Mercado, Mate-Runde, frei, Zufall
- **Voseo-Modus** 🇺🇾 / **España-Modus** 🇪🇸 umschaltbar
- **Korrekturen**: max. 2 pro Turn, dezent als Chip, Erklärung auf Deutsch
- **Fehler-Gedächtnis**: wiederkehrende Fehler landen in localStorage und fließen in künftige Gespräche ein (der Tutor baut sie unauffällig wieder ein)
- **Modelle**: Claude Opus 5 (Standard) oder Haiku 4.5 (schnell/günstig), umschaltbar

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
