"""Demo: Laya triage rápido via laya-serve (decisão + latência em ms).

Não usa Playwright — só HTTP em /v1/systemone.
Para descoberta de seletores DOM, use examples/laya_find.py (ver examples/README.md).

Requer o server no ar (docs/setup.md):
  .\\.venv\\Scripts\\laya-serve.exe

Uso:
  .\\.venv\\Scripts\\python.exe examples\\fast_triage.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE_URL}/v1/systemone"

QUESTIONS = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this?",
        "criteria": {
            "billing": "invoices, payments, refunds, charges",
            "technical": "bugs, crashes, outages, login, password",
            "other": "everything else",
        },
    },
    "refund": {
        "type": "noul",
        "instructions": "Is the user asking for a refund or chargeback?",
    },
}

TICKETS = [
    "Fui cobrado duas vezes em março. Quero o reembolso hoje ou cancelo o plano.",
    "The app crashes every time I open Settings.",
    "Esqueci minha senha e não consigo entrar na conta.",
    "Where can I download the annual invoice PDF?",
    "La aplicación se cierra al abrir la configuración.",
]


def predict(state: str) -> tuple[dict, float]:
    payload = json.dumps(
        {
            "state": {"body": state},
            "questions": QUESTIONS,
            "model": "multilingual",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    ms = (time.perf_counter() - t0) * 1000
    return body, ms


def fmt_answers(answers: dict) -> str:
    dept = answers["department"]["choice"]
    refund = answers["refund"]["noul"]
    return f"dept={dept:<10} refund_p={refund:.2f}"


def main() -> int:
    # Evita mojibake de PT/ES no console Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=5) as resp:
            health = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"Server offline em {BASE_URL}: {exc}", file=sys.stderr)
        print("Suba com: .\\.venv\\Scripts\\laya-serve.exe", file=sys.stderr)
        return 1

    print(f"laya-serve ok · loaded={health.get('loaded')} · device={health.get('device')}")
    print("-" * 72)

    latencies: list[float] = []
    for i, ticket in enumerate(TICKETS, 1):
        result, ms = predict(ticket)
        latencies.append(ms)
        preview = ticket if len(ticket) <= 58 else ticket[:55] + "..."
        print(f"{i}. {preview}")
        print(f"   {fmt_answers(result['answers'])}  {ms:7.1f} ms")
        print(f"   route={result.get('routing', {}).get('model', '?')}")
        print()

    print("-" * 72)
    print(
        f"latência · média={statistics.mean(latencies):.1f} ms"
        f" · mediana={statistics.median(latencies):.1f} ms"
        f" · n={len(latencies)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
