"""AI extraction: Hinglish sentence → structured transactions (JSON) via Hermes + Gemma 4."""

import json
import re
import subprocess
import time
from datetime import date

HERMES = r"C:\Users\afzal\AppData\Local\hermes\bin\hermes.exe"
WORKDIR = r"C:\Users\afzal\dukaan-ai"

SYSTEM = """You are the extraction engine of a shopkeeper's digital ledger (digital munim).
Convert ONE user sentence (Hindi, Hinglish or English) into structured transactions.

Reply with ONLY a JSON object, no prose, no markdown fences:
{"transactions":[{"party":"","amount":0,"type":"sale|credit|payment|purchase","item":"","payment":"cash|upi|credit","note":"","date":"YYYY-MM-DD"}],"clarify":""}

type rules:
- "credit" = udhaar diya / baaki diye / credit given (money OUT on credit, increases customer's dues)
- "payment" = paisa mila / wapas mile / payment received (money IN, reduces dues)
- "sale" = maal becha against cash/upi (money IN, no dues change)
- "purchase" = maal kharida / supplier ko diye (money OUT to supplier)

Other rules:
- party = customer/supplier name, keep original spelling; "" only for walk-in counter sales.
- amount = number only (rupees). Never invent amounts.
- date: today is {today} unless the sentence says another date (use YYYY-MM-DD).
- One sentence may contain MULTIPLE transactions — return each separately.
- If a required amount or party is missing/ambiguous, return {{"transactions":[],"clarify":"<one short Hindi question>"}}.
- note: short Hindi/Hinglish summary of what happened.
"""


def _build_prompt(user_text: str) -> str:
    return (SYSTEM.replace("{today}", date.today().isoformat())
            + "\nUser sentence: " + user_text.strip())


def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model reply")
    obj = json.loads(m.group(0))
    if "transactions" not in obj:
        raise ValueError("missing transactions key")
    obj.setdefault("clarify", "")
    cleaned = []
    for t in obj["transactions"][:5]:
        amt = float(t.get("amount") or 0)
        if amt <= 0:
            continue
        typ = str(t.get("type") or "").lower().strip()
        if typ not in ("sale", "credit", "payment", "purchase"):
            continue
        cleaned.append({
            "party": str(t.get("party") or "").strip(),
            "amount": amt,
            "type": typ,
            "item": str(t.get("item") or "").strip(),
            "payment": str(t.get("payment") or "").strip().lower(),
            "note": str(t.get("note") or "").strip(),
            "date": str(t.get("date") or date.today().isoformat())[:10],
        })
    obj["transactions"] = cleaned
    return obj


def run_hermes(prompt: str, max_retries: int = 1, timeout: int = 240):
    """Run Hermes -z; returns stdout. Raises RuntimeError on rate limit/timeout."""
    last_err = ""
    for attempt in range(max_retries + 1):
        try:
            proc = subprocess.run(
                [HERMES, "-z", prompt],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout, cwd=WORKDIR,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            if "429" in out or "RESOURCE_EXHAUSTED" in out:
                last_err = "rate_limit"
                if attempt < max_retries:
                    m = re.search(r"retry in ([\d.]+)s", out)
                    wait = min((float(m.group(1)) + 5) if m else 60, 90)
                    time.sleep(wait)
                    continue
                raise RuntimeError("rate_limit")
            if proc.returncode == 0 and out.strip():
                out = re.sub(r"\x1b\[[0-9;]*m", "", out)
                out = re.sub(r"^Query:.*\n", "", out, flags=re.M).strip()
                return out
            last_err = "empty"
        except subprocess.TimeoutExpired:
            last_err = "timeout"
    raise RuntimeError(last_err or "unknown")


def extract(user_text: str) -> dict:
    """→ {"transactions": [...], "clarify": str}. Raises RuntimeError on failure."""
    reply = run_hermes(_build_prompt(user_text))
    return _extract_json(reply)
