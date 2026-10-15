# PRD — Dukaan AI (किराना साथी)

| | |
|---|---|
| **Product** | Dukaan AI — voice-first digital munim for kirana shops |
| **Event** | Hacktoberfest Hack Day: Lucknow × Integral University (15–16 Oct 2026) |
| **Category** | Business · Partner challenge: Best Use of Gemma 4 |
| **Team** | `Hello World` — `Mohd Hamza`, `Mohammad Anas`, `Afzal Siddiqui` |
| **College** | Integral University, Lucknow |
| **Contact** | `[email@example.com]` |
| **Version** | 2.0 (Hack Day MVP — voice-first ledger) |
| **Date** | 15 Oct 2026 |

---

## 1. Summary

**Dukaan AI** is a Hindi/Hinglish **voice-first digital munim** (ledger keeper) for Indian
kirana (grocery) shopkeepers. The shopkeeper taps one big mic and speaks the way they
already talk about their day ("*Ramesh ko 500 rupaye udhaar diye*") — the assistant turns
that into a structured ledger entry, shows it on a **confirmation card**, and saves it
**only after an explicit "✓ Confirm and save"**.

The product follows one rule end to end: **voice first, minimal typing, clear records,
no transaction saved without confirmation.**

It runs on **Hermes Agent** (skill-based agent framework) with **Gemma 4**
(`gemma-4-26b-a4b-it` via the Google Gemini API) as the language model, and a
deterministic Python engine (`core.py`) for all money math so every rupee is computed by
code, never by the model.

## 2. Problem

- **~13 million kirana shops** in India; the vast majority keep **no digital books** —
  udhaar (credit) lives in a paper *bahi-khata* or in the shopkeeper's memory.
- Forgotten dues are the direct cost: money given on credit that is never collected
  because nobody can reconstruct *who owes how much* at week's end.
- Existing billing software assumes English UI, typing speed, and digital literacy —
  all barriers for the average shopkeeper (often 40+, Hindi-first).
- Shopkeepers already *dictate* their day ("*5 packet biscuit becha 250 ka upi se*") to a
  family member or ledger-wala. That information is lost or written in unstructured
  notebooks.

**Opportunity:** capture the dictation that already happens, and make it a reliable,
queryable ledger — without asking the shopkeeper to fill a single form from scratch.

## 3. Goals (Hack Day MVP)

| # | Goal | Metric |
|---|---|---|
| G1 | Parse Hinglish dictation (sale / udhaar / payment received / purchase) into a structured entry | ≥90% accuracy on common shop phrases |
| G2 | Nothing saves without confirmation | 100% of entries pass the review card; zero silent writes |
| G3 | Query the ledger: per-customer balance, day/month totals | Correct totals on demo dataset |
| G4 | Undo a wrong entry without editing history | Compensating adjustment recorded, original preserved |
| G5 | Daily closing summary ("*aaj ka hisaab*") on one screen | Correct sales / received / credit / dues |
| G6 | Zero-cost ops on free tier | Gemini API free tier only (no card) |

**Non-goals (v1):** GST filing, inventory/stock tracking, multi-shop chains, WhatsApp
delivery (roadmap), Tally sync (roadmap), regional languages beyond Hindi/Hinglish
(roadmap).

## 4. Personas

**P1 — Ramesh bhaiya (primary).** 52, runs a kirana shop in Lucknow. Uses UPI daily.
Gives udhaar to regular customers. Wants to know at closing time: *aaj kitna becha, kitna
mila, kitna baaki hai*. Comfortable speaking into WhatsApp voice notes, not forms.

**P2 — Priya (secondary).** 28, helps father with books in the evening. Wants the week's
dues list without flipping through a paper register. Comfortable with a simple web UI.

**P3 — CA / tax filer (downstream).** Needs a clean CSV of the ledger per client.

## 5. User stories

| ID | As a… | I want to… | So that… |
|---|---|---|---|
| US1 | Shopkeeper | Say "*Ramesh ko 500 rupaye udhaar diye*" | The credit is recorded without opening a form |
| US2 | Shopkeeper | See the parsed entry on a card and confirm it | I never record a wrong amount by accident |
| US3 | Shopkeeper | Ask "*Ramesh ka kitna baaki hai*" (Customers screen) | I know exactly who owes me money |
| US4 | Shopkeeper | Press **Undo** on a wrong entry | The mistake is corrected but the history stays honest |
| US5 | Shopkeeper | Open Reports at closing | I see today's sales, received, credit, pending dues in one view |
| US6 | Priya | Download a CSV of the ledger | I can hand it to our CA |

## 6. Features

### MVP (shipped at Hack Day)

| Feature | Where | Behaviour |
|---|---|---|
| **Voice entry** | Voice entry / Overview | Big mic → browser speech recognition (Hindi/Hinglish) → text fallback if mic unavailable |
| **Confirmation card** | Review step | Parsed fields (party, amount, type, payment, date, note) shown editable; **nothing saves without "✓ Confirm and save"**; Cancel / re-speak always available |
| **Clarifying question** | Review step | Ambiguous dictation → Gemma returns `clarify` instead of a guess → one short question, no bad entry |
| **Ledger** | Ledger screen | All entries, search, type filter, date range, running view totals, **Undo** |
| **Customer accounts** | Customers screen | Per-customer outstanding balance, entry count, last activity, full history drill-down |
| **Daily summary** | Reports screen | Today vs month: sales, received, credit given, pending dues + "Daily closing summary" |
| **Undo / adjustment** | Ledger | Compensating `reversal` entry appended — history is append-only and auditable |
| **CSV export** | Ledger / Settings | One-click download for the CA |
| **Design** | All screens | Deep green `#176B45` on off-white `#F8FAF7`, Hindi/Hinglish microcopy, big touch targets |

### P1 (next 30 days)

- WhatsApp voice-note delivery (Hermes gateway adapter)
- On-device / Whisper speech recognition for offline reliability
- Daily auto-summary at closing time (Hermes cron)
- Udhaar follow-up reminders ("*Ramesh ko 500 yaad dilayein?*")

### P2 (90 days)

- GST summary + GSTR-1 export; stock with low-stock alerts
- Expense & salary entries; multi-day / monthly views
- Tally/Busy sync; ONDC seller onboarding data pack
- Regional languages (Bhojpuri, Awadhi, Urdu script)

## 7. Product experience

1. Shopkeeper opens **Dukaan AI** and taps the **big green mic** (or types in the text
   fallback — minimal typing either way).
2. Browser speech recognition captures the Hinglish sentence and hands the transcript to
   **Gemma 4** via **Hermes Agent** (`kirana-saathi` skill), which returns a strict JSON:
   `{"transactions": [...], "clarify": ""}`.
3. The app renders a **confirmation card** — every field editable, Cancel one click away.
4. **"✓ Confirm and save"** → `core.py` writes the entry with deterministic money math.
5. Ledger / Customers / Reports update instantly (local JSON — no extra API calls).
6. Wrong entry? **Undo** appends a compensating adjustment — the original line stays.

**Error handling:** ambiguous dictation → one clarifying question, never a guessed entry.
Rate-limit (free tier) → friendly Hindi pause message with parsed backoff and retry.

## 8. Technical architecture

```
Shopkeeper (Hindi/Hinglish, browser speech API)
        │
        ▼
Streamlit UI (deep-green "digital munim" design)
  screens: Overview · Voice Entry · Ledger · Customers · Reports · Settings
        │  transcript / typed text
        ▼
Hermes Agent (Nous Research)
  ├─ Skill: kirana-saathi (SKILL.md playbook — Hinglish grammar, entry rules)
  └─ Model: gemma-4-26b-a4b-it via Gemini API   ← Gemma 4
        │  strict JSON {transactions, clarify}
        ▼
Review card (human confirmation gate — no bypass)
        │  "✓ Confirm and save"
        ▼
core.py — deterministic ledger engine (append-only entries, balances, undo, CSV)
        │
        ▼
data/transactions.json · data/settings.json · CSV export
```

**Design principles**

- **Confirmation gate is the product.** The LLM proposes; the shopkeeper disposes.
  No entry is written without an explicit tap.
- **Deterministic money math.** The LLM only parses intent; every ₹ balance and total is
  computed by `core.py` (JSON-file backed, zero DB ops for the demo).
- **Append-only history.** Corrections are compensating entries — the audit trail is the
  feature.
- **Skills as prompts.** Business rules (Hinglish grammar, entry taxonomy, confirmation
  style) live in `SKILL.md` — editable, versionable, improvable by the agent itself.
- **Free-tier engineering.** Gemma 4 free tier = 15 RPM / 16K TPM / 1500 RPD. We cut the
  agent prompt from 53KB → 13KB so each extraction fits in **2 API calls**; data screens
  bypass the API entirely; the UI retries with parsed backoff on HTTP 429.

**Stack:** Python 3.13 · Hermes Agent · Gemma 4 (`gemma-4-26b-a4b-it`) via Gemini API ·
Streamlit · browser Web Speech API · JSON storage. MIT licensed.

## 9. Success metrics (post-pilot)

| Metric | Target (pilot, 20 shops, 30 days) |
|---|---|
| Entries recorded per shop per day | ≥15 |
| Parse accuracy after confirmation (accepted as-is) | ≥90% |
| Entries corrected via review before saving | <20% (card caught them) |
| Dues collected that would have been forgotten (self-reported) | ≥1/week/shop |
| Shops still active after 30 days | ≥70% |
| Cost per shop per month (API) | ₹0 on free tier; <₹50 on paid tier |

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| LLM mis-parses party/amount | Confirmation card on every entry; fields editable; ambiguous → `clarify` question, never a guess |
| Free-tier rate limits | Deterministic data screens + retry UI; paid tier is 1 config line |
| Undo abuse / double-undo | Reversal links to original id; idempotent guard |
| Browser speech support varies | Text fallback beside the mic; same extraction path |
| Data loss (file storage) | Nightly CSV export; cloud sync on roadmap |
| Hindi dialect coverage | Skill rules tuned on Lucknow-market phrases; corrections improve SKILL.md |

## 11. Business model (sketch)

- **Free:** local-only assistant (as demoed) — acquisition channel.
- **Pro (₹199/mo):** cloud backup, WhatsApp voice, multi-user, reminders.
- **B2B:** CA firms pay per-client for structured intake (the CA persona).
- **Platform:** ONDC/credit partners pay for verified ledger data (with consent).

## 12. Why Gemma 4 + Hermes

- **Gemma 4** (`gemma-4-26b-a4b-it`): open-weight MoE (26B total / 4B active), native
  tool-calling, strong Hindi/Hinglish — parses *kirana dictation* into strict JSON
  reliably, free tier via Gemini API — zero cost to pilot in Lucknow.
- **Hermes Agent:** skill-based **playbooks** (business rules as markdown the agent can
  refine), model-agnostic (Gemma 4 today, swap anytime), multi-surface (same skill fronts
  this web UI today, WhatsApp/Telegram gateway tomorrow).

## 13. Milestones

| When | What |
|---|---|
| Hack Day (15–16 Oct) | MVP shipped: voice entry + confirmation gate, ledger, customers, reports, undo, CSV, green-first UI |
| +2 weeks | WhatsApp bot pilot with 3 shops; on-device speech; udhaar reminders |
| +1 month | 20-shop Lucknow pilot; GST summary view; GSTR-1 export |
| +3 months | Paid tier; CA-firm channel; stock tracking; 2nd language |

## 14. Open questions

1. Should udhaar entries trigger automated reminders? (P1)
2. Preferred accounting export: Tally XML vs Busy vs CSV-only for pilot CAs?
3. Data residency: laptop-local (current) vs Indian-cloud bucket for WhatsApp mode?

---

*Prototype:* `streamlit run app.py` · *Model:* `gemma-4-26b-a4b-it` via Gemini API ·
*Framework:* Hermes Agent · MIT License · API keys never committed.
