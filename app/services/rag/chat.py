from typing import List

from openai import OpenAI

from app.config import settings
from app.services.rag.retriever import search_all

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client


def _format_context(results: List[dict]) -> str:
    lines = []
    for r in results:
        item = r["item"]
        score = r["score"]
        if r["type"] == "machine":
            lines.append(f"[Server, Relevanz {score:.0%}] {item.to_text()}")
        else:
            lines.append(f"[Netzwerk, Relevanz {score:.0%}] {item.to_text()}")
    return "\n".join(lines)


def chat(message: str, db) -> dict:
    results = search_all(message, db, top_k=5)
    context = _format_context(results)

    system = (
        "Du bist ein hilfreicher IT-Infrastruktur-Assistent für eine CMDB. "
        "Beantworte Fragen ausschließlich auf Basis der bereitgestellten Infrastruktur-Daten. "
        "Wenn die Daten keine Antwort erlauben, sage das klar. "
        "Antworte präzise und strukturiert auf Deutsch."
    )

    prompt = f"""Relevante Infrastruktur-Daten:
{context if context else "Keine relevanten Einträge gefunden."}

Frage: {message}"""

    response = _get_client().chat.completions.create(
        model=settings.openrouter_chat_model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
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
        "answer": response.choices[0].message.content,
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

    response = _get_client().chat.completions.create(
        model=settings.openrouter_chat_model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
