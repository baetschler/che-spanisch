# Ausgabe-Vorlage für ChatGPT Voice

Damit `tools/import_lessons.py` die Session-Notizen automatisch in die App übernehmen kann,
müssen die Markdown-Dateien immer gleich aufgebaut sein. Diese Datei ist der Vertrag.

## Einrichtung (einmalig)

Den folgenden Text in ChatGPT als Projektanweisung hinterlegen (Projekt „Español" o.ä.),
dann gilt er für jede Session in diesem Projekt.

---

> Wenn ich am Ende einer Sprech-Session „Zusammenfassung" sage, gib mir eine Markdown-Datei
> nach exakt diesem Schema aus. Keine zusätzlichen Überschriften, keine Einleitung, kein
> Schlusswort. Halte die Reihenfolge der Abschnitte ein und benutze genau diese
> Überschriften-Namen, auch wenn ein Abschnitt kurz ausfällt.
>
> ```markdown
> ---
> id: <kurzer-slug-ohne-umlaute>
> titel: <Titel auf Spanisch>
> emoji: <ein einzelnes Emoji zum Thema>
> fecha: <YYYY-MM-DD>
> tema: <ein bis zwei Sätze auf Spanisch: worum ging es, welche Entscheidung/Situation>
> ---
>
> ## Vocabulario
>
> | Español | Alemán | Ejemplo |
> |---|---|---|
> | <wort> | <übersetzung> | <beispielsatz auf spanisch> |
>
> ## Gramática
>
> ### <Titel des Grammatikpunkts auf Deutsch>
> **Kurz:** <eine Zeile, was die Regel besagt>
> <Zwei bis vier Sätze Erklärung auf Deutsch. Spanische Beispiele *kursiv*, Schlüsselformen **fett**.>
>
> ## Frases útiles
>
> - <ganzer Satz auf Spanisch, den ich benutzt habe oder brauchte>
>
> ## Práctica
>
> 1. <Satz mit ___ als Lücke> → <Lösung>
> ```
>
> Regeln für den Inhalt:
> - Nur was in DIESER Session wirklich vorkam. Nichts dazuerfinden, um die Liste zu füllen.
> - Vocabulario: Wörter, die ich nicht wusste oder falsch benutzt habe. Keine Wörter, die ich
>   sicher beherrsche.
> - Gramática: die Muster, an denen ich gehakt habe. Ein bis vier Punkte, je einer als `###`.
> - Frases útiles: ganze Sätze, keine Fragmente.
> - Práctica: drei bis sechs Lücken, jede mit `→` und der Lösung dahinter.
> - Rioplatense: voseo benutzen (vos tenés, vos sos), nicht tú.

---

## Wohin die Datei gehört

```
~/Documents/Codex/<YYYY-MM-DD>/<projekt>/outputs/<name>.md
```

Der Importer scannt diesen Ordner rekursiv nach `outputs/*.md`.

## Was der Importer prüft

Eine Datei wird nur übernommen, wenn sie vollständig passt:

| Prüfung | Wenn verletzt |
|---|---|
| Frontmatter vorhanden, mit `id`, `titel`, `emoji`, `fecha`, `tema` | Datei wird übersprungen |
| `fecha` im Format `YYYY-MM-DD` | Datei wird übersprungen |
| Abschnitt `## Vocabulario` mit mindestens einer Tabellenzeile | Datei wird übersprungen |
| Vocabulario-Tabelle hat drei Spalten | Zeile wird übersprungen |
| Abschnitt `## Gramática` mit mindestens einem `###`-Punkt | Datei wird übersprungen |
| Jeder Grammatikpunkt hat eine `**Kurz:**`-Zeile | Punkt wird ohne Kurzfassung übernommen |
| `## Frases útiles` und `## Práctica` | dürfen fehlen, dann bleiben sie leer |
| `id` doppelt über mehrere Dateien | die neuere `fecha` gewinnt |

Übersprungene Dateien landen mit Begründung im Log und in der iMessage. Der Importer bricht
lieber ab, als halbe Lektionen einzubauen: falsches Material im Training merkt man erst, wenn
man es schon geübt hat.

## Beispiel

Eine vollständige, gültige Datei liegt in [`beispiel-lektion.md`](beispiel-lektion.md).
