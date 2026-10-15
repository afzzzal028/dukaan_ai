"""Data layer: transactions, customers, balances, daily summary, undo, settings.

Transaction model (all money is float-rounded to 2dp on write):
  id, ts (ISO), type in {sale, credit, payment, purchase, reversal},
  party (customer name or ""), amount, item, payment in {cash, upi, credit},
  note, gst_rate, gst_amount, corrects (id of the entry this reverses).

Dues effect (dir): credit +1, payment -1, sale-on-credit +1, everything else 0;
a reversal takes the opposite dir of the entry it corrects — financial history is
never silently overwritten, corrections append adjustments.
"""

import json
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
TX_FILE = DATA_DIR / "transactions.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

TYPES = ["sale", "credit", "payment", "purchase", "reversal"]
TYPE_LABELS = {
    "sale": "Sale",
    "credit": "Credit given",
    "payment": "Payment received",
    "purchase": "Purchase",
    "reversal": "Correction",
}


def _ensure():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TX_FILE.exists():
        _seed()


def _load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def load_tx():
    _ensure()
    return _load(TX_FILE, [])


def save_tx(tx):
    _save(TX_FILE, tx)


def load_settings():
    _ensure()
    s = _load(SETTINGS_FILE, {})
    s.setdefault("shop_name", "Sharma Kirana Store")
    s.setdefault("owner", "Ramesh")
    s.setdefault("language", "Hinglish")
    s.setdefault("voice_lang", "hi-IN")
    return s


def save_settings(s):
    _save(SETTINGS_FILE, s)


def add_tx(entry: dict) -> dict:
    """Append a confirmed transaction. Only confirmed data reaches the ledger."""
    tx = load_tx()
    entry["id"] = max((t["id"] for t in tx), default=0) + 1
    entry.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    entry.setdefault("party", "")
    entry.setdefault("item", "")
    entry.setdefault("payment", "")
    entry.setdefault("note", "")
    entry.setdefault("gst_rate", 0)
    entry.setdefault("gst_amount", 0)
    entry.setdefault("corrects", None)
    entry["amount"] = round(float(entry["amount"]), 2)
    tx.append(entry)
    save_tx(tx)
    return entry


def _dir(t: dict, by_id: dict) -> float:
    if t["type"] == "credit":
        return 1.0
    if t["type"] == "payment":
        return -1.0
    if t["type"] == "sale" and t.get("payment") == "credit":
        return 1.0
    if t["type"] == "reversal":
        target = by_id.get(t.get("corrects"))
        return -_dir(target, by_id) if target else 0.0
    return 0.0


def balance_of(name: str) -> float:
    tx = load_tx()
    by_id = {t["id"]: t for t in tx}
    return round(sum(_dir(t, by_id) * t["amount"] for t in tx
                     if (t.get("party") or "").casefold() == name.casefold()), 2)


def customers():
    tx = load_tx()
    by_id = {t["id"]: t for t in tx}
    names = {}
    for t in tx:
        p = (t.get("party") or "").strip()
        if not p or t["type"] == "reversal" and not t.get("party"):
            continue
        rec = names.setdefault(p.casefold(), {"name": p, "balance": 0.0,
                                              "last": "", "count": 0})
        rec["balance"] += _dir(t, by_id) * t["amount"]
        rec["count"] += 1
        if t["ts"] > rec["last"]:
            rec["last"] = t["ts"]
            rec["name"] = p
    out = list(names.values())
    for r in out:
        r["balance"] = round(r["balance"], 2)
    out.sort(key=lambda r: -r["balance"])
    return out


def match_customer(party: str):
    """Exact (casefold) then substring match against known customers."""
    if not party:
        return None
    known = customers()
    key = party.casefold().strip()
    for c in known:
        if c["name"].casefold() == key:
            return c["name"]
    for c in known:
        k = c["name"].casefold()
        if key in k or k in key:
            return c["name"]
    return party.strip()


def _day(ts: str, d: date) -> bool:
    return ts[:10] == d.isoformat()


def summary(d: date | None = None) -> dict:
    """Today's sales, money received, credit given, purchases, counts."""
    d = d or date.today()
    tx = load_tx()
    by_id = {t["id"]: t for t in tx}
    rows = [t for t in tx if _day(t["ts"], d) or
            (t["type"] == "reversal" and by_id.get(t.get("corrects"))
             and _day(by_id[t["corrects"]]["ts"], d))]
    s = {"sales": 0.0, "received": 0.0, "credit": 0.0, "purchases": 0.0,
         "outstanding": 0.0, "count": 0, "reversed": 0}
    for t in rows:
        sign = _dir(t, by_id)
        if t["type"] == "sale" or (t["type"] == "reversal"
                                   and by_id.get(t.get("corrects"), {}).get("type") == "sale"):
            # reversals of sales subtract
            is_rev = t["type"] == "reversal"
            amt = -t["amount"] if is_rev else t["amount"]
            s["sales"] += amt
        elif t["type"] == "payment" or (t["type"] == "reversal"
                                        and by_id.get(t.get("corrects"), {}).get("type") == "payment"):
            amt = -t["amount"] if t["type"] == "reversal" else t["amount"]
            s["received"] += amt
        elif t["type"] == "credit" or (t["type"] == "reversal"
                                       and by_id.get(t.get("corrects"), {}).get("type") == "credit"):
            amt = -t["amount"] if t["type"] == "reversal" else t["amount"]
            s["credit"] += amt
        elif t["type"] == "purchase":
            s["purchases"] += t["amount"]
        if t["type"] == "reversal":
            s["reversed"] += 1
        s["count"] += 1
        _ = sign
    s["outstanding"] = round(sum(c["balance"] for c in customers()
                                 if c["balance"] > 0), 2)
    for k in ("sales", "received", "credit", "purchases"):
        s[k] = round(s[k], 2)
    return s


def ledger_rows(q: str = "", type_filter: str = "All",
                date_from: date | None = None, date_to: date | None = None):
    tx = load_tx()
    by_id = {t["id"]: t for t in tx}
    rows = list(reversed(tx))  # newest first
    if q:
        k = q.casefold().strip()
        rows = [t for t in rows if k in (t.get("party") or "").casefold()
                or k in (t.get("item") or "").casefold()
                or k in (t.get("note") or "").casefold()
                or k in str(t["amount"])]
    if type_filter != "All":
        rows = [t for t in rows if t["type"] == type_filter]
    if date_from:
        rows = [t for t in rows if t["ts"][:10] >= date_from.isoformat()]
    if date_to:
        rows = [t for t in rows if t["ts"][:10] <= date_to.isoformat()]
    out = []
    for t in rows:
        out.append({**t, "target_type": (by_id.get(t.get("corrects")) or {}).get("type")})
    return out


def can_undo(t: dict) -> bool:
    if t["type"] == "reversal":
        return False
    return not any(x.get("corrects") == t["id"] for x in load_tx())


def undo(tx_id: int, reason: str = "") -> dict:
    """Append a compensating reversal — never delete or edit money history."""
    tx = load_tx()
    target = next((t for t in tx if t["id"] == tx_id), None)
    if not target:
        raise ValueError("entry not found")
    if not can_undo(target):
        raise ValueError("already corrected")
    return add_tx({
        "type": "reversal",
        "party": target.get("party", ""),
        "amount": target["amount"],
        "item": target.get("item", ""),
        "payment": target.get("payment", ""),
        "note": reason or f"Undo of #{target['id']} ({TYPE_LABELS.get(target['type'], target['type'])})",
        "corrects": target["id"],
    })


def customer_history(name: str):
    tx = load_tx()
    by_id = {t["id"]: t for t in tx}
    rows = [t for t in tx if (t.get("party") or "").casefold() == name.casefold()]
    out = []
    for t in reversed(rows):
        out.append({**t, "dir": _dir(t, by_id),
                    "target_type": (by_id.get(t.get("corrects")) or {}).get("type")})
    return out


def export_csv() -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ID", "Timestamp", "Type", "Party", "Item", "Amount",
                "Payment", "Note", "Corrects"])
    for t in load_tx():
        w.writerow([t["id"], t["ts"], t["type"], t.get("party", ""),
                    t.get("item", ""), t["amount"], t.get("payment", ""),
                    t.get("note", ""), t.get("corrects") or ""])
    return buf.getvalue()


def _seed():
    """Demo shop data so the UI is alive on first open."""
    now = date.today().isoformat()
    rows = [
        {"type": "sale", "party": "", "amount": 1250.0, "item": "Groceries",
         "payment": "cash", "note": "Counter sale", "ts": f"{now}T09:15:00"},
        {"type": "credit", "party": "Ramesh", "amount": 500.0, "item": "",
         "payment": "credit", "note": "Udhaar diya", "ts": f"{now}T10:05:00"},
        {"type": "payment", "party": "Ramesh", "amount": 300.0, "item": "",
         "payment": "cash", "note": "Purana hisaab wapas", "ts": f"{now}T11:40:00"},
        {"type": "credit", "party": "Suresh", "amount": 200.0, "item": "",
         "payment": "credit", "note": "Udhaar diya", "ts": f"{now}T12:20:00"},
        {"type": "sale", "party": "Anita", "amount": 640.0, "item": "Sabzi",
         "payment": "upi", "note": "UPI se", "ts": f"{now}T13:10:00"},
        {"type": "purchase", "party": "Gupta Wholesale", "amount": 4200.0,
         "item": "Stock refill", "payment": "upi", "note": "Wholesale",
         "ts": f"{now}T14:00:00"},
        {"type": "credit", "party": "Anita", "amount": 150.0, "item": "",
         "payment": "credit", "note": "Udhaar diya", "ts": f"{now}T15:30:00"},
    ]
    tx = []
    for i, r in enumerate(rows, 1):
        r = {**r, "id": i, "gst_rate": 0, "gst_amount": 0, "corrects": None}
        tx.append(r)
    save_tx(tx)
    if not SETTINGS_FILE.exists():
        save_settings(load_settings())
