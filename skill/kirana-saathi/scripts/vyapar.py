#!/usr/bin/env python3
"""Vyapar Saathi - Kirana shop ledger, GST and stock manager.

Data stored in JSON files next to this script's data/ directory:
  data/ledger.json   - sales & purchase entries
  data/stock.json    - stock items with quantities

Usage:
  python vyapar.py add-sale --item "Aata 10kg" --qty 2 --price 450 --payment upi
  python vyapar.py add-purchase --item "Aata bag" --qty 10 --price 2200 --supplier "Reliance"
  python vyapar.py ledger --from 2026-10-01 --to 2026-10-15
  python vyapar.py gst-summary --period monthly
  python vyapar.py stock
  python vyapar.py stock-update --item "Aata 10kg" --delta -2
  python vyapar.py export --format csv
  python vyapar.py parse --text "aaj 50kg aata becha 2000 rupaye upi se"
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
LEDGER_FILE = DATA_DIR / "ledger.json"
STOCK_FILE = DATA_DIR / "stock.json"

# GST slabs for common kirana items (India)
GST_RATES = {
    "atta": 0, "rice": 0, "dal": 0, "aata": 0, "chawal": 0, "dal pulses": 0,
    "milk": 0, "doodh": 0, "egg": 0, "anda": 0, "fresh": 0,
    "vegetables": 0, "sabzi": 0, "fruit": 0, "phal": 0,
    "salt": 0, "namak": 0, "sugar": 5, "cheeni": 5, "gur": 5,
    "oil": 5, "tel": 5, "ghee": 12, "butter": 12,
    "tea": 5, "chai": 5, "coffee": 5,
    "biscuits": 18, "namkeen": 12, "chips": 12, "chocolate": 18,
    "soap": 18, "shampoo": 18, "detergent": 18, "toothpaste": 18,
    "spices": 5, "masala": 5, "haldi": 5, "mirch": 5,
    "soap detergent": 18, "personal care": 18,
    "cold drinks": 28, "soft drinks": 28, "cold drink": 28,
    "cigarette": 28, "ciggerate": 28, "tobacco": 28,
    "flour": 0, "wheat": 0, "paneer": 12, "curd": 5, "dahi": 5,
}

DEFAULT_GST = 18  # fallback slab


def ensure_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LEDGER_FILE.exists():
        LEDGER_FILE.write_text("[]", encoding="utf-8")
    if not STOCK_FILE.exists():
        STOCK_FILE.write_text("[]", encoding="utf-8")


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def guess_gst_rate(item_name):
    name = item_name.lower()
    for key, rate in GST_RATES.items():
        if key in name:
            return rate
    return DEFAULT_GST


def add_entry(entry_type, item, qty, price, payment="cash", supplier="", customer="", notes=""):
    ensure_data()
    ledger = load_json(LEDGER_FILE)
    amount = qty * price
    gst_rate = guess_gst_rate(item)
    gst_amount = round(amount * gst_rate / (100 + gst_rate), 2) if gst_rate > 0 else 0
    entry = {
        "id": len(ledger) + 1,
        "type": entry_type,  # sale | purchase
        "date": date.today().isoformat(),
        "time": datetime.now().strftime("%H:%M"),
        "item": item,
        "qty": qty,
        "price": price,
        "amount": round(amount, 2),
        "payment": payment,  # cash | upi | credit | udhaar
        "gst_rate": gst_rate,
        "gst_amount": gst_amount,
        "supplier": supplier,
        "customer": customer,
        "notes": notes,
    }
    ledger.append(entry)
    save_json(LEDGER_FILE, ledger)
    # auto-update stock
    update_stock(item, -qty if entry_type == "sale" else qty, silent=True)
    return entry


def update_stock(item, delta, silent=False):
    ensure_data()
    stock = load_json(STOCK_FILE)
    for s in stock:
        if s["item"].lower() == item.lower():
            s["qty"] = max(0, s["qty"] + delta)
            s["updated"] = date.today().isoformat()
            save_json(STOCK_FILE, stock)
            if not silent:
                return s
            return s
    # new item
    new_item = {"item": item, "qty": max(0, delta), "updated": date.today().isoformat(),
                "gst_rate": guess_gst_rate(item)}
    stock.append(new_item)
    save_json(STOCK_FILE, stock)
    if not silent:
        return new_item
    return new_item


def view_ledger(date_from=None, date_to=None, entry_type=None):
    ledger = load_json(LEDGER_FILE)
    rows = ledger
    if date_from:
        rows = [r for r in rows if r["date"] >= date_from]
    if date_to:
        rows = [r for r in rows if r["date"] <= date_to]
    if entry_type:
        rows = [r for r in rows if r["type"] == entry_type]
    total_sale = sum(r["amount"] for r in rows if r["type"] == "sale")
    total_purchase = sum(r["amount"] for r in rows if r["type"] == "purchase")
    total_gst = sum(r["gst_amount"] for r in rows if r["type"] == "sale")
    return {
        "entries": rows,
        "count": len(rows),
        "total_sales": round(total_sale, 2),
        "total_purchases": round(total_purchase, 2),
        "total_gst_collected": round(total_gst, 2),
        "net": round(total_sale - total_purchase, 2),
    }


def gst_summary(period="monthly"):
    ledger = load_json(LEDGER_FILE)
    today = date.today()
    if period == "monthly":
        prefix = today.strftime("%Y-%m")
        rows = [r for r in ledger if r["date"].startswith(prefix)]
        label = today.strftime("%B %Y")
    elif period == "weekly":
        week_ago = (today - __import__("datetime").timedelta(days=7)).isoformat()
        rows = [r for r in ledger if r["date"] >= week_ago]
        label = "Last 7 days"
    else:
        rows = ledger
        label = "All time"

    # Group by GST rate
    by_rate = {}
    for r in rows:
        rate = str(r["gst_rate"]) + "%"
        if rate not in by_rate:
            by_rate[rate] = {"taxable": 0.0, "gst": 0.0, "count": 0}
        by_rate[rate]["taxable"] += r["amount"] - r["gst_amount"] if r["type"] == "sale" else 0
        by_rate[rate]["gst"] += r["gst_amount"] if r["type"] == "sale" else 0
        by_rate[rate]["count"] += 1

    total_output_gst = sum(v["gst"] for v in by_rate.values())
    # Input GST on purchases (ITC)
    input_gst = sum(r["gst_amount"] for r in rows if r["type"] == "purchase")
    net_payable = round(total_output_gst - input_gst, 2)

    return {
        "period": label,
        "gstrates": {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in by_rate.items()},
        "output_gst": round(total_output_gst, 2),
        "input_gst_itc": round(input_gst, 2),
        "net_gst_payable": net_payable,
        "entries": len(rows),
    }


def view_stock():
    stock = load_json(STOCK_FILE)
    low = [s for s in stock if s["qty"] <= 5]
    return {"items": stock, "total": len(stock), "low_stock": low}


def export_csv():
    ensure_data()
    ledger = load_json(LEDGER_FILE)
    out = DATA_DIR / f"ledger_export_{date.today().isoformat()}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Date", "Time", "Type", "Item", "Qty", "Price", "Amount",
                         "Payment", "GST Rate %", "GST Amt", "Supplier/Customer"])
        for r in ledger:
            party = r["supplier"] if r["type"] == "purchase" else r["customer"]
            writer.writerow([r["id"], r["date"], r["time"], r["type"], r["item"], r["qty"],
                             r["price"], r["amount"], r["payment"], r["gst_rate"],
                             r["gst_amount"], party])
    return {"file": str(out), "rows": len(ledger)}


def parse_hinglish(text):
    """Best-effort parse of Hinglish voice-note text into a structured entry.
    This is a rule-based fallback; the LLM should normally structure the entry itself
    and call add-sale/add-purchase directly."""
    text = text.lower().strip()
    entry_type = "sale"
    if any(w in text for w in ["kharida", "खरीदा", "purchase", "liya", "लिया", "stock aaya", "mangwaya"]):
        entry_type = "purchase"

    payment = "cash"
    if "upi" in text or "gpay" in text or "phonepe" in text:
        payment = "upi"
    elif "udhaar" in text or "उधार" in text or "credit" in text or "baki" in text:
        payment = "credit"

    # quantity: number followed by kg/ltr/pcs/dozen/packet/bag or standalone number
    qty_m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|kilo|लीटर|ltr|litre|pcs|piece|dozen|dus|packet|bag|bora|thaili|पैकेट)?", text)
    qty = float(qty_m.group(1)) if qty_m else 1.0

    # amount: number followed by rupaye/rs/₹ or the largest number
    amt_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:rupaye|rupees|rs\.?|₹|रुपये|rupay)", text)
    if not amt_m:
        numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
        amount = max(numbers) if numbers else 0
    else:
        amount = float(amt_m.group(1))

    # item: try to find common kirana items
    items = ["aata", "atta", "चावल", "chawal", "rice", "dal", "दाल", "cheeni", "sugar", "चीनी",
             "tel", "oil", "तेल", "doodh", "milk", "दूध", "chai", "tea", "चाय", "biscuit",
             "namkeen", "soap", "sabzi", "pyaz", "onion", "प्याज", "aloo", "potato", "आलू",
             "tamatar", "tomato", "टमाटर", "paneer", "ghee", "masala", "namak", "salt", "नमक"]
    item = ""
    for it in items:
        if it in text:
            item = it.title()
            break
    if not item:
        # grab words before qty unit
        words = re.findall(r"[a-z\u0900-\u097F]+", text)
        item = " ".join(words[:2]).title() if words else "Unknown Item"

    price = round(amount / qty, 2) if qty else amount
    return {"type": entry_type, "item": item, "qty": qty, "amount": amount,
            "price": price, "payment": payment, "raw_text": text}


def main():
    p = argparse.ArgumentParser(description="Vyapar Saathi - kirana ledger")
    sub = p.add_subparsers(dest="cmd")

    a1 = sub.add_parser("add-sale")
    a1.add_argument("--item", required=True)
    a1.add_argument("--qty", type=float, default=1)
    a1.add_argument("--price", type=float, required=True)
    a1.add_argument("--payment", default="cash")
    a1.add_argument("--customer", default="")

    a2 = sub.add_parser("add-purchase")
    a2.add_argument("--item", required=True)
    a2.add_argument("--qty", type=float, default=1)
    a2.add_argument("--price", type=float, required=True)
    a2.add_argument("--payment", default="cash")
    a2.add_argument("--supplier", default="")

    a3 = sub.add_parser("ledger")
    a3.add_argument("--from", dest="date_from", default=None)
    a3.add_argument("--to", dest="date_to", default=None)
    a3.add_argument("--type", dest="entry_type", default=None)

    a4 = sub.add_parser("gst-summary")
    a4.add_argument("--period", default="monthly", choices=["weekly", "monthly", "all"])

    a5 = sub.add_parser("stock")

    a6 = sub.add_parser("stock-update")
    a6.add_argument("--item", required=True)
    a6.add_argument("--delta", type=float, required=True)

    a7 = sub.add_parser("export")
    a7.add_argument("--format", default="csv")

    a8 = sub.add_parser("parse")
    a8.add_argument("--text", required=True)

    args = p.parse_args()

    if args.cmd == "add-sale":
        e = add_entry("sale", args.item, args.qty, args.price, args.payment, customer=args.customer)
        print(json.dumps(e, ensure_ascii=False, indent=2))
    elif args.cmd == "add-purchase":
        e = add_entry("purchase", args.item, args.qty, args.price, args.payment, supplier=args.supplier)
        print(json.dumps(e, ensure_ascii=False, indent=2))
    elif args.cmd == "ledger":
        print(json.dumps(view_ledger(args.date_from, args.date_to, args.entry_type),
                         ensure_ascii=False, indent=2))
    elif args.cmd == "gst-summary":
        print(json.dumps(gst_summary(args.period), ensure_ascii=False, indent=2))
    elif args.cmd == "stock":
        print(json.dumps(view_stock(), ensure_ascii=False, indent=2))
    elif args.cmd == "stock-update":
        print(json.dumps(update_stock(args.item, args.delta), ensure_ascii=False, indent=2))
    elif args.cmd == "export":
        print(json.dumps(export_csv(), ensure_ascii=False, indent=2))
    elif args.cmd == "parse":
        print(json.dumps(parse_hinglish(args.text), ensure_ascii=False, indent=2))
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
