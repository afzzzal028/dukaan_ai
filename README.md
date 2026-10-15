# 🏪 Dukaan AI — किराना साथी

**Voice-first digital munim for Indian kirana shops.** Tap the big mic, speak
Hindi/Hinglish ("*Ramesh ko 500 rupaye udhaar diye*") — get a confirmation card, save
with one tap, and always know *kaun kitna baaki hai*.

> Built for **Hacktoberfest Hack Day: Lucknow × Integral University** (15–16 Oct 2026)
> — Category: **Business** · Partner challenge: **Best Use of Gemma 4** ·
> Uses **Hermes Agent** framework.

**Voice first · minimal typing · clear records · no transaction saved without confirmation.**

---

## 🎯 Problem

Kirana shops keep **no digital books** — udhaar (credit) lives in a paper *bahi-khata*
or in memory, so dues get forgotten. Existing billing software demands English UIs and
typing speed. Shopkeepers already *dictate* their day to someone — this turns that
dictation into a reliable, queryable ledger.

## ✨ What it does

| You say / do | What happens |
|---|---|
| 🎤 "*Ramesh ko 500 rupaye udhaar diye*" | Confirmation card: **Credit given · Ramesh · ₹500** — editable |
| ✓ "Confirm and save" | Entry written by deterministic money math (nothing saves without this tap) |
| ❓ Ambiguous sentence | Gemma asks one clarifying question instead of guessing |
| 📒 Ledger screen | Search, filter, date range, running totals, **Undo** (appends a reversal — history never edited) |
| 👥 Customers screen | Per-customer udhaar balance, entry count, full history drill-down |
| 📊 Reports screen | Today vs month: sales, received, credit, pending dues + daily closing summary |
| ⬇️ CSV | One-click export for the CA |

## 🏗 Architecture

```
Shopkeeper (Hindi/Hinglish — browser speech API or text fallback)
        │
        ▼
┌─────────────────────────────────────────────┐
│  Streamlit UI — deep-green "digital munim"  │
│  Overview · Voice Entry · Ledger ·          │
│  Customers · Reports · Settings             │
└─────────────────────────────────────────────┘
        │  transcript
        ▼
┌─────────────────────────────────────────────┐
│           Hermes Agent (Nous Research)      │
│  • skill: kirana-saathi (SKILL.md)          │
│  • model: gemma-4-26b-a4b-it  ← Gemma 4    │
│          via Gemini API (generativelanguage)│
└─────────────────────────────────────────────┘
        │  strict JSON {transactions, clarify}
        ▼
   Review card (human confirmation gate — no bypass)
        │  "✓ Confirm and save"
        ▼
   core.py — deterministic ledger engine
   (append-only entries · balances · undo · CSV)
        │
        ▼
   data/transactions.json · data/settings.json
```

## 💎 Why Gemma 4 (partner challenge)

- **Model:** `gemma-4-26b-a4b-it` (Gemma 4 MoE, 26B total / 4B active)
- **API:** Google **Gemini API** (`https://generativelanguage.googleapis.com/v1beta`)
- **Key:** set as `GEMINI_API_KEY` in `~/.hermes/.env` (never committed)
- **Switchable:** `gemma-4-31b-it` (dense 31B) via one config line

Open-weight, strong Hindi/Hinglish dictation parsing into strict JSON, and a free tier
(no credit card) — exactly what a low-margin kirana pilot needs.

## 🤖 Why Hermes Agent

- **Skill-based:** business rules live in `SKILL.md` (Hinglish grammar, entry taxonomy)
  — versionable and improvable
- **Deterministic money:** Gemma only parses intent — `core.py` computes every ₹
- **Model-agnostic:** Gemma 4 via Gemini API is one config line
- **Multi-surface:** same skill can later front a WhatsApp gateway

## 🚀 Run it

```bash
# 1. Prerequisites (already installed for the demo)
#    Hermes Agent → https://hermes-agent.nousresearch.com
pip install -r requirements.txt

# 2. Configure Gemini API key (never commit this)
echo 'GEMINI_API_KEY=your_key_here' >> ~/.hermes/.env

# 3. Launch
streamlit run app.py
```

Config (`~/.hermes/config.yaml`):

```yaml
model:
  default: "gemma-4-26b-a4b-it"
  provider: "gemini"
```

Skill lives at `~/.hermes/skills/business/kirana-saathi/` (SKILL.md + scripts/vyapar.py).

## 📊 Demo script (2 minutes)

1. **Voice entry:** tap the mic → "*Ramesh ko 500 rupaye udhaar diye*" →
   confirmation card appears (every field editable)
2. **Confirm:** "✓ Confirm and save" → success state → entry appears in **Ledger**
3. **Customers:** Ramesh's balance updates — tap "Kholo" for full history
4. **Reports:** aaj ka hisaab — sales ₹1,890 · received ₹300 · credit ₹925 ·
   pending dues ₹625 + daily closing summary
5. **Undo:** break an entry on purpose → reversal appended, original row preserved
6. **CSV:** download for the CA

## ⚠️ Free-tier note

Gemma 4 on the Gemini API free tier: **15 RPM / 16K TPM / 1500 RPD**. The agent prompt
is slimmed 53KB → 13KB so each extraction fits in **2 API calls** (~4K tokens each);
Ledger/Customers/Reports screens read local JSON directly — **zero API cost** — and the
UI parses 429 backoff and retries in Hindi.

## 📁 Project structure

```
dukaan-ai/
├── app.py                      # Streamlit UI (voice · ledger · customers · reports)
├── ai.py                       # Gemma 4 extraction via Hermes (strict JSON, 429 handling)
├── core.py                     # deterministic ledger engine (entries · undo · CSV)
├── README.md
├── PRD.md                      # Product Requirements Document
├── Dukaan-AI-HackDay.pptx      # Hack Day presentation deck
├── requirements.txt
├── data/                       # demo ledger + settings (local JSON)
└── skill/kirana-saathi/        # Hermes skill (copy of ~/.hermes/skills/...)
    ├── SKILL.md                # agent playbook (Hinglish rules, entry taxonomy)
    ├── scripts/vyapar.py       # ledger engine used by the skill CLI
    └── data/
```

Installed live copy: `~/.hermes/skills/business/kirana-saathi/` with
`~/.hermes/config.yaml` (`model.default: gemma-4-26b-a4b-it`, `provider: gemini`)
and `~/.hermes/.env` (`GEMINI_API_KEY`, never committed).

## 📜 License

MIT
