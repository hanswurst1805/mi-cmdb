# Mini-CMDB

Leichtgewichtige Configuration Management Database mit KI-gestützter Suche.

## Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy
- **Datenbank:** PostgreSQL 15 + pgvector
- **RAG:** Anthropic Claude API + Voyage AI Embeddings
- **Web-UI:** Jinja2 + Bootstrap 5

## Schnellstart

```bash
cp .env.example .env
# .env mit echten API-Keys befüllen

docker-compose up --build
```

Danach erreichbar unter:
- Web-UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Chat: http://localhost:8000/chat

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET/POST | `/api/v1/machines` | Maschinen auflisten / anlegen |
| GET/PUT/DELETE | `/api/v1/machines/{id}` | Maschine verwalten |
| GET | `/api/v1/machines/{id}/nics` | NICs einer Maschine |
| GET/POST | `/api/v1/networks` | Netzwerke |
| GET | `/api/v1/networks/{id}/free` | Freie IPs im Subnetz |
| POST | `/api/v1/search` | Semantische Suche |
| POST | `/api/v1/chat` | KI-Chat über Infrastruktur |
| GET | `/api/v1/anomalies/{machine_id}` | Anomalie-Erkennung |
| POST | `/api/v1/reindex` | Alle Embeddings neu erzeugen |

## Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `DATABASE_URL` | PostgreSQL-Verbindungsstring |
| `ANTHROPIC_API_KEY` | API-Key für Claude |
| `VOYAGE_API_KEY` | API-Key für Voyage AI Embeddings |
| `SECRET_KEY` | Geheimer Schlüssel für Sessions |
