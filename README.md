# eBay Laptop/PC Elden-Ring Bot (100% kostenlos)

Dieser Bot sucht mit der **eBay Browse API** nach **Laptops oder PCs** bis zu einem konfigurierbaren Budget (Standard: **200€**) und bewertet lokal, ob **Elden Ring** voraussichtlich spielbar ist.

## Was bedeutet „100% kostenlos“?
- Keine OpenAI/Claude/sonstige Paid-API
- Optionales lokales LLM via **Ollama** (ebenfalls kostenlos lokal betreibbar)
- Fallback auf lokale Heuristik, falls kein Ollama verfügbar ist

## Features
- Umschaltbar zwischen **Laptop**- und **PC**-Suche (Reiter)
- Sortierung wählbar: **Beste zuerst (Gut → Schlecht)**, Preis auf/absteigend
- Ansicht wählbar: **Karten** oder **Kompakt**
- Umschaltbarer Prüfmodus:
  - `auto` (nutzt Ollama, fällt sonst auf Heuristik zurück)
  - `ollama` (nur lokales LLM)
  - `heuristic` (nur Regelwerk)
- eBay-Suche mit Preisfilter in EUR
- Lokale Bewertung je Angebot (`geeignet`, `bedingt geeignet`, `ungeeignet`)
- Fallback ohne eBay-Token: Demo-Angebote zum Testen

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional `.env` anlegen:
```env
EBAY_BEARER_TOKEN=...
# optional für lokales LLM:
OLLAMA_API_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b
```

## Ollama (für akkurateren KI-Modus)
```bash
# Ollama lokal installieren (siehe ollama.com)
ollama pull llama3.1:8b
ollama serve
```

Dann im UI `Prüfmodus = Auto` oder `Nur Ollama` wählen.

## Start
```bash
uvicorn app.main:app --reload --port 8000
```

Dann öffnen: `http://localhost:8000`

## Hinweis zu eBay API
Für Live-Ergebnisse brauchst du ein gültiges OAuth Bearer Token für die eBay Buy Browse API. Ohne Token zeigt die App Demo-Daten.
