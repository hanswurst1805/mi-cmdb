from typing import List

import anthropic

from app.config import settings
from app.services.rag.retriever import search_all

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _format_context(results: List[dict]) -> str:
    lines = []
    for r in results:
        item = r["item"]
        score = r["score"]
        if r["type"] == "machine":
            lines.append(
                f"[Server, Relevanz {score:.0%}] {item.to_text()}"
            )
        else:
            lines.append(
                f"[Netzwerk, Relevanz {score:.0%}] {item.to_text()}"
            )
    return "\n".join(lines)


def chat(message: str, db) -> dict:
    results = search_all(message, db, top_k=5)
    context = _format_context(results)

    system = (
        "Du bist ein hilfreicher IT-Infrastruktur-Assistent für eine CMDB (Configuration Management Database). "
        "Beantworte Fragen ausschließlich auf Basis der bereitgestellten Infrastruktur-Daten. "
        "Wenn die Daten keine Antwort erlauben, sage das klar. "
        "Antworte präzise und strukturiert auf Deutsch."
    )

    prompt = f"""Relevante Infrastruktur-Daten:
{context if context else "Keine relevanten Einträge gefunden."}

Frage: {message}"""

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    sources = [
        {
            "type": r["type"],
            "name": r["item"].fqdn if r["type"] == "machine" else r["item"].name,
            "score": r["score"],
        }
        for r in results
    ]

    return {
        "answer": response.content[0].text,
        "sources": sources,
    }


def analyze_anomalies(machine, similar_machines: List[dict]) -> str:
    if not similar_machines:
        return "Keine ähnlichen Maschinen gefunden – kein Vergleich möglich."

    lines = [f"Ziel-Maschine: {machine.to_text()}", "", "Ähnliche Maschinen:"]
    for s in similar_machines:
        m = s["machine"]
        lines.append(f"  - {m.to_text()} (Ähnlichkeit: {s['score']:.0%})")

    prompt = "\n".join(lines) + (
        "\n\nAnalysiere die obigen Maschinen und identifiziere Abweichungen oder Anomalien "
        "im Vergleich zur Ziel-Maschine (z.B. ungewöhnliche RAM/CPU-Konfiguration, "
        "abweichendes OS, anderer Owner). Fasse kurz und strukturiert zusammen."
    )

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
