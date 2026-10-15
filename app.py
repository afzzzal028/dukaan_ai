"""Dukaan AI — voice-first digital munim for local shopkeepers.

Voice entry → Gemma 4 extraction (Hermes Agent) → review card → confirm → ledger.
Nothing is saved without explicit confirmation. Ledger/GST reads are local (zero API).
"""

import json
from datetime import date, datetime

import streamlit as st

import ai
import core

st.set_page_config(page_title="Dukaan AI — Digital Munim", page_icon="📒",
                   layout="wide", initial_sidebar_state="auto")

# ─────────────────────────────────────────────────────────────
# Design system — deep green · warm off-white · charcoal
# ─────────────────────────────────────────────────────────────
st.markdown(
    r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600&display=swap');

:root {
  --green: #176B45;
  --green-dark: #115638;
  --bg: #F8FAF7;
  --surface: #FFFFFF;
  --text: #202923;
  --muted: #68736B;
  --border: #E2E8E2;
  --amber: #B45309;
  --red: #B91C1C;
}

.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', 'Noto Sans Devanagari', system-ui, sans-serif;
    /* Streamlit theme tokens — recolors primary buttons, radios, links */
    --primary-color: #176B45;
    --primary-color-15: rgba(23,107,69,0.15);
    --primary-color-20: rgba(23,107,69,0.20);
    --primary-color-30: rgba(23,107,69,0.30);
    --primary-color-50: rgba(23,107,69,0.50);
    --secondary-background-color: #FFFFFF;
    --text-color: #202923;
    --font: 'Inter', 'Noto Sans Devanagari', system-ui, sans-serif;
}

/* force green primary buttons (button + form submit) */
[data-testid="stBaseButton-primary"], button[kind="primary"],
[data-testid="stBaseButton-primaryFormSubmit"], button[kind="primaryFormSubmit"] {
    background: #176B45 !important; color: #fff !important; border-color: #176B45 !important;
}
[data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover, button[kind="primaryFormSubmit"]:hover {
    background: #115638 !important; border-color: #115638 !important;
}
/* radio + checkbox accent */
[data-testid="stRadio"] input[type="radio"], [data-testid="stCheckbox"] input {
    accent-color: #176B45;
}
/* custom radio paint (native accent-color unreliable) */
label[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child {
    background: #176B45 !important;
    border-color: #176B45 !important;
}
label[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div {
    background: #FFFFFF !important;
}
label[data-testid="stRadioOption"]:hover > div > div:first-child {
    border-color: #176B45 !important;
}
[data-testid="stRadio"] input[type="radio"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 15px !important; height: 15px !important;
    border: 2px solid #C4CEC6 !important;
    background: #FFFFFF !important;
    border-radius: 50% !important;
    position: relative !important;
    margin: 0 !important;
    flex-shrink: 0;
}
[data-testid="stRadio"] input[type="radio"]:checked {
    border-color: #176B45 !important;
    background: #176B45 !important;
}
[data-testid="stRadio"] input[type="radio"]:checked::after {
    content: "";
    position: absolute;
    top: 2px; left: 2px; right: 2px; bottom: 2px;
    background: #FFFFFF;
    border-radius: 50%;
}
/* inputs stay white */
[data-baseweb="base-input"], [data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInputField"], [data-testid="stDateInputFieldsScroller"] {
    background: #FFFFFF !important;
}
/* input text stays dark even if a dark browser theme sneaks in */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="base-input"] input, [data-baseweb="base-input"] textarea,
[data-testid="stNumberInput"] input, [data-testid="stDateInputField"] input,
[data-testid="stSelectbox"] input {
    color: #202923 !important;
    caret-color: #176B45 !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #6B7268 !important; opacity: 1;
}

/* row card flattened when wrapped in bordered container */
.trow.flat {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}

[data-testid="stHeader"], [data-testid="stToolbar"] {display: none;}
[data-testid="stDecoration"] {display: none;}
[data-testid="stStatusWidget"] {display: none;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar */
section[data-testid="StSidebar"], section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container {padding-top: 1.6rem; padding-left: 1.1rem; padding-right: 1.1rem;}
.brand h1 {font-size: 1.25rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; margin: 0;}
.brand .sub {font-size: 0.74rem; color: var(--muted); font-weight: 500; margin-top: 0.1rem;}
.nav-label {
    font-size: 0.66rem; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.08em; margin: 1.4rem 0 0.5rem;
}
div[data-testid="stRadio"] label {
    background: transparent; border: 1px solid transparent; border-radius: 8px;
    padding: 0.42rem 0.7rem; margin-bottom: 2px; font-weight: 500; font-size: 0.9rem;
    color: var(--muted); width: 100%;
}
div[data-testid="stRadio"] label:hover {background: #F1F5F1; color: var(--text);}
div[data-testid="stRadio"] input:checked + label {
    background: #E8F2EC; border-color: #BEDCCE; color: var(--green); font-weight: 600;
}
div[data-testid="stRadio"] [role="radiogroup"] {gap: 2px;}
.side-foot {
    margin-top: 1.8rem; padding-top: 0.9rem; border-top: 1px solid var(--border);
    font-size: 0.7rem; color: var(--muted); line-height: 1.6;
}
.side-foot code {background: #F1F5F1; padding: 1px 4px; border-radius: 4px; font-size: 0.66rem;}

/* Page header */
.page-head {display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.2rem;}
.page-head h2 {font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; color: var(--text);}
.page-head .sub {font-size: 0.85rem; color: var(--muted); margin-top: 0.25rem;}

/* Stat cards */
.stat-row {display: flex; gap: 0.8rem; margin-bottom: 1.3rem; flex-wrap: wrap;}
.stat-card {
    flex: 1 1 180px; background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 0.95rem 1.05rem; box-shadow: 0 1px 2px rgba(32,41,35,0.04);
}
.stat-card .label {font-size: 0.68rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em;}
.stat-card .value {font-size: 1.45rem; font-weight: 700; letter-spacing: -0.02em; margin-top: 0.25rem; color: var(--text);}
.stat-card .hint {font-size: 0.7rem; color: var(--muted); margin-top: 0.15rem;}
.stat-card.pos .value {color: var(--green);}
.stat-card.warn .value {color: var(--amber);}

.sec-label {
    font-size: 0.68rem; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.07em; margin: 0.5rem 0 0.55rem;
}

/* Hero (voice) */
.hero-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    padding: 1.4rem 1.5rem; text-align: center;
    box-shadow: 0 1px 3px rgba(32,41,35,0.05); margin-bottom: 0.8rem;
}
.hero-card h3 {margin: 0; font-size: 1.15rem; font-weight: 700; color: var(--text);}
.hero-card p {margin: 0.35rem 0 0; font-size: 0.88rem; color: var(--muted);}
.example-chip {
    display: inline-block; background: #F1F5F1; color: var(--green-dark);
    border: 1px solid var(--border); border-radius: 999px;
    padding: 0.26rem 0.72rem; font-size: 0.79rem; margin: 0.3rem 0.15rem 0;
}

/* mic block (st.html) */
.mic-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    padding: 1.6rem 1.2rem 1.2rem; text-align: center; margin-bottom: 0.8rem;
    box-shadow: 0 1px 3px rgba(32,41,35,0.05);
}

/* Review */
.review-head {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--surface); border: 1px solid #BEDCCE; border-radius: 12px;
    padding: 0.7rem 1.05rem; margin-bottom: 0.5rem;
}
.badge {display: inline-block; border-radius: 6px; padding: 0.14rem 0.55rem;
        font-size: 0.72rem; font-weight: 600;}
.b-sale, .b-payment {background: #E8F2EC; color: var(--green);}
.b-credit {background: #FEF3E2; color: var(--amber);}
.b-purchase {background: #EEF1F4; color: var(--muted);}
.b-reversal {background: #EEF1F4; color: var(--muted);}
.rc-amt {font-size: 1.2rem; font-weight: 700; color: var(--text);}

/* tables */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--border); border-radius: 10px; background: var(--surface);
}

/* transaction / customer rows */
.trow {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.68rem 0.9rem; border: 1px solid var(--border); border-radius: 10px;
    background: var(--surface); margin-bottom: 0.5rem;
}
.trow .who {font-weight: 600; font-size: 0.92rem; color: var(--text);}
.trow .desc {font-size: 0.78rem; color: var(--muted); margin-top: 0.1rem;}
.trow .amt {font-weight: 700; font-size: 0.95rem; color: var(--text); text-align: right;}
.trow .amt.due {color: var(--amber);}
.trow .amt.in {color: var(--green);}
.trow .when {font-size: 0.72rem; color: var(--muted); text-align: right; margin-top: 0.1rem;}

/* buttons */
.stButton>button, .stDownloadButton>button {
    background: var(--surface); border: 1px solid var(--border); color: var(--text);
    border-radius: 8px; font-weight: 500; font-size: 0.85rem;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    border-color: var(--green); color: var(--green); background: #F1F5F1;
}
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] {
    background: var(--green) !important; color: #fff !important;
    border-color: var(--green) !important; font-weight: 600;
}
.stButton>button[kind="primary"]:hover {background: var(--green-dark) !important;}

[data-testid="stAlert"] {border-radius: 10px; font-size: 0.87rem;}

.empty {text-align:center; padding: 3rem 1rem; color: var(--muted);}
.empty .big {font-weight: 600; color: var(--text); margin-bottom: 0.3rem;}

/* mic button states (st.html content) */
#dmic {
    background-color: #176B45;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='34' height='34' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z'/%3E%3Cpath d='M19 10v2a7 7 0 0 1-14 0v-2'/%3E%3Cline x1='12' x2='12' y1='19' y2='22'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
}
#dmic.rec {
    background-color: #B91C1C !important;
    box-shadow: 0 0 0 8px rgba(185,28,28,0.15) !important;
    animation: dpulse 1.4s ease-in-out infinite;
}
@keyframes dpulse {
    0%, 100% {transform: scale(1);}
    50% {transform: scale(1.05);}
}

hr {border: none; border-top: 1px solid var(--border); margin: 1.1rem 0;}

@media (max-width: 768px) {
    .stat-card {flex: 1 1 45%;}
    .page-head {flex-direction: column; align-items: flex-start; gap: 0.6rem;}
}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def inr(n) -> str:
    """₹ with Indian digit grouping (1,23,456)."""
    n = float(n)
    neg = n < 0
    n = abs(round(n))
    s = f"{n:,}".replace(",", "")
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        s = ",".join(parts + [last3])
    return f"{'-' if neg else ''}₹{s}"


def stat_cards(cards):
    html = '<div class="stat-row">'
    for label, value, hint, cls in cards:
        h = f'<div class="hint">{hint}</div>' if hint else ""
        html += (f'<div class="stat-card {cls}"><div class="label">{label}</div>'
                 f'<div class="value">{value}</div>{h}</div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _goto_voice():
    st.session_state.nav = "Voice entry"
    st.session_state.stage = "idle"


def page_head(title, sub, add_btn=True):
    st.markdown(
        f'<div class="page-head"><div><h2>{title}</h2>'
        f'<div class="sub">{sub}</div></div></div>',
        unsafe_allow_html=True,
    )
    if add_btn:
        st.button("＋ Add entry", key="hdr_add", type="primary",
                  on_click=_goto_voice)


def empty_state(big, small):
    st.markdown(f'<div class="empty"><div class="big">{big}</div>{small}</div>',
                unsafe_allow_html=True)


def type_badge(t: str) -> str:
    cls = {"sale": "b-sale", "credit": "b-credit", "payment": "b-payment",
           "purchase": "b-purchase", "reversal": "b-reversal"}.get(t, "b-purchase")
    return f'<span class="badge {cls}">{core.TYPE_LABELS.get(t, t)}</span>'


def voice_html(lang: str, attempt: int) -> str:
    """Mic card. Runs in the MAIN page (st.html + JS). On final transcript it
    fills the text-fallback form and clicks submit → normal Streamlit rerun."""
    return f"""
<div class="mic-card" id="dukaan-mic-{attempt}">
  <button id="dmic" aria-label="Tap to speak" title="Tap to speak" style="
    width:88px;height:88px;border-radius:50%;border:none;cursor:pointer;
    background-color:#176B45;color:#fff;display:inline-flex;align-items:center;justify-content:center;
    box-shadow:0 4px 14px rgba(23,107,69,0.35);
    background-image:url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='34' height='34' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z'/%3E%3Cpath d='M19 10v2a7 7 0 0 1-14 0v-2'/%3E%3Cline x1='12' x2='12' y1='19' y2='22'/%3E%3C/svg%3E&quot;);
    background-repeat:no-repeat;background-position:center;">
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>
    </svg>
  </button>
  <div id="dstatus" style="margin-top:0.7rem;font-size:0.9rem;font-weight:600;color:#202923;">Tap to speak</div>
  <div id="dlive" style="margin-top:0.35rem;font-size:0.95rem;color:#176B45;min-height:1.3em;
       max-width:520px;margin-left:auto;margin-right:auto;"></div>
  <button id="dstop" style="margin-top:0.6rem;display:none;background:#fff;border:1px solid #E2E8E2;
    border-radius:8px;padding:0.4rem 0.9rem;font-size:0.82rem;font-weight:600;color:#202923;cursor:pointer;">
    Rokkar dekhein
  </button>
  <div id="derr" style="margin-top:0.5rem;font-size:0.8rem;color:#B91C1C;max-width:520px;
       margin-left:auto;margin-right:auto;"></div>
</div>
<style>
  #dmic.rec {{background:#B91C1C !important;box-shadow:0 0 0 8px rgba(185,28,28,0.15) !important;
    animation:dpulse 1.4s ease-in-out infinite;}}
  @keyframes dpulse {{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.05)}}}}
</style>
<script>
(function () {{
  const micBtn = document.getElementById("dmic");
  if (!micBtn) return;
  /* bind once per DOM node (node is recreated on screen switch) */
  if (micBtn.dataset.dBound) return;
  micBtn.dataset.dBound = "1";
  const lang = "{lang}";
  const status = document.getElementById("dstatus");
  const live = document.getElementById("dlive");
  const err = document.getElementById("derr");
  const stopBtn = document.getElementById("dstop");
  /* ensure mic glyph even if sanitizer dropped the inline background */
  micBtn.style.backgroundColor = "#176B45";
  micBtn.style.backgroundImage = "url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2234%22 height=%2234%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22white%22 stroke-width=%222%22 stroke-linecap=%22round%22 stroke-linejoin=%22round%22%3E%3Cpath d=%22M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z%22/%3E%3Cpath d=%22M19 10v2a7 7 0 0 1-14 0v-2%22/%3E%3Cline x1=%2212%22 x2=%2212%22 y1=%2219%22 y2=%2222%22/%3E%3C/svg%3E')";
  micBtn.style.backgroundRepeat = "no-repeat";
  micBtn.style.backgroundPosition = "center";
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let finalT = "", rec = null, submitted = false;

  function submitText(text) {{
    if (submitted) return;
    submitted = true;
    const form = document.querySelector('[data-testid="stForm"]');
    if (!form) {{
      status.textContent = "Text box dhundh nahi saka — neeche khud likhein";
      return;
    }}
    const inp = form.querySelector("input, textarea");
    if (!inp) {{ status.textContent = "Input nahi mila"; return; }}
    const proto = inp.tagName === "TEXTAREA" ? window.HTMLTextAreaElement : window.HTMLInputElement;
    const setter = Object.getOwnPropertyDescriptor(proto.prototype, "value").set;
    setter.call(inp, text);
    inp.dispatchEvent(new Event("input", {{bubbles: true}}));
    status.textContent = "Entry bhej rahe hain…";
    const btn = form.querySelector('[data-testid="stFormSubmitButton"] button');
    if (btn) {{ btn.click(); }}
  }}

  if (!SR) {{
    status.textContent = "Speech recognition is mein browser me nahi hai";
    err.textContent = "Neeche likhkar entry karein. Chrome use karein.";
    micBtn.style.opacity = "0.4";
    return;
  }}
  function start() {{
    rec = new SR();
    rec.lang = lang;
    rec.interimResults = true;
    rec.continuous = false;
    rec.maxAlternatives = 1;
    rec.onstart = function () {{
      micBtn.classList.add("rec");
      status.textContent = "Listening… boliye";
      stopBtn.style.display = "inline-block";
      err.textContent = "";
    }};
    rec.onresult = function (e) {{
      let interim = "";
      for (const r of e.results) {{
        if (r.isFinal) finalT += r[0].transcript;
        else interim += r[0].transcript;
      }}
      live.textContent = finalT || interim;
    }};
    rec.onerror = function (ev) {{
      if (ev.error === "not-allowed" || ev.error === "service-not-allowed") {{
        status.textContent = "Mic permission deny ho gayi";
        err.textContent = "Browser me microphone allow karein, ya neeche likhein.";
        micBtn.classList.remove("rec");
      }} else if (ev.error === "network") {{
        status.textContent = "Speech service se connection nahi hua";
        err.textContent = "Internet check karein, ya neeche likhein.";
        micBtn.classList.remove("rec");
      }}
    }};
    rec.onend = function () {{
      micBtn.classList.remove("rec");
      stopBtn.style.display = "none";
      if (finalT.trim()) {{
        submitText(finalT.trim());
      }} else {{
        status.textContent = "Kuch sunayi nahi diya — dobara try karein";
      }}
    }};
    try {{ rec.start(); }}
    catch (e) {{ status.textContent = "Mic start nahi hua: " + e; }}
  }}
  micBtn.onclick = start;
  stopBtn.onclick = function () {{ try {{ rec && rec.stop(); }} catch (e) {{}} }};
}})();
</script>
"""


# ─────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────
st.session_state.setdefault("nav", "Overview")
st.session_state.setdefault("stage", "idle")  # idle|processing|clarify|review|success|error
st.session_state.setdefault("transcript", "")
st.session_state.setdefault("pending", [])
st.session_state.setdefault("saved", [])
st.session_state.setdefault("attempt", 0)
st.session_state.setdefault("voice_error", "")
st.session_state.setdefault("flash", None)
st.session_state.setdefault("clarify", "")
st.session_state.setdefault("sel_customer", None)
st.session_state.setdefault("voice_lang", None)

settings = core.load_settings()
if st.session_state.voice_lang is None:
    st.session_state.voice_lang = settings.get("voice_lang", "hi-IN")


def start_extract(text: str):
    """Stage the transcript; extraction happens in the render loop (spinner)."""
    st.session_state.transcript = text
    st.session_state.stage = "processing"
    st.rerun()


def do_extract():
    """Run AI extraction for the staged transcript (called under a spinner)."""
    text = st.session_state.transcript
    try:
        result = ai.extract(text)
    except Exception as e:
        st.session_state.voice_error = str(e)
        st.session_state.stage = "error"
        return
    if result.get("clarify") and not result["transactions"]:
        st.session_state.clarify = result["clarify"]
        st.session_state.stage = "clarify"
        return
    st.session_state.pending = [
        {**t, "party": t.get("party") or ""}
        for t in result["transactions"]
    ]
    st.session_state.saved = []
    if st.session_state.pending:
        st.session_state.stage = "review"
    else:
        st.session_state.voice_error = "parse"
        st.session_state.stage = "error"


def reset_voice():
    st.session_state.stage = "idle"
    st.session_state.transcript = ""
    st.session_state.pending = []
    st.session_state.saved = []
    st.session_state.clarify = ""
    st.session_state.voice_error = ""
    st.session_state.attempt += 1


def _goto_ledger():
    reset_voice()
    st.session_state.nav = "Ledger"


def _goto_customers():
    st.session_state.nav = "Customers"


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div class="brand"><h1>{settings["shop_name"]}</h1>'
        '<div class="sub">Dukaan AI · digital munim</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="nav-label">Menu</div>', unsafe_allow_html=True)
    st.radio(
        "Nav",
        ["Overview", "Voice entry", "Ledger", "Customers", "Reports", "Settings"],
        label_visibility="collapsed", key="nav",
    )
    st.markdown(
        '<div class="side-foot">'
        "Bolkar entry — confirm karke save.<br>"
        "Powered by <b>Gemma 4</b> · Hermes Agent<br>"
        "<code>gemma-4-26b-a4b-it</code> via Gemini API"
        "</div>",
        unsafe_allow_html=True,
    )

nav = st.session_state.nav

# flash (top of main area)
if st.session_state.get("flash"):
    kind, msg = st.session_state.flash
    (st.success if kind == "ok" else st.error)(msg)
    st.session_state.flash = None


# ─────────────────────────────────────────────────────────────
# Voice section (Overview hero + Voice entry screen)
# ─────────────────────────────────────────────────────────────
def render_voice_section():
    lang = st.session_state.voice_lang

    # ── idle: hero + mic + lang + text fallback ──
    if st.session_state.stage == "idle":
        examples = [
            "“Ramesh ko 500 rupaye udhaar diye.”",
            "“Aaj Ramesh se 500 mile, Suresh ko 200 ka udhaar.”",
            "“10 packet biscuit becha 250 ka upi se.”",
        ]
        chips = "".join(f'<span class="example-chip">{e}</span>' for e in examples)
        st.markdown(
            '<div class="hero-card"><h3>Add an entry by speaking</h3>'
            "<p>Speak naturally. Your ledger updates after confirmation.</p>"
            f'<div style="margin-top:0.6rem">{chips}</div></div>',
            unsafe_allow_html=True,
        )
        st.html(voice_html(lang, st.session_state.attempt),
                unsafe_allow_javascript=True)

        lc1, lc2, lc3 = st.columns([2.2, 1.6, 2.2])
        with lc2:
            picked = st.selectbox(
                "Voice language", ["hi-IN", "en-IN"],
                index=0 if lang == "hi-IN" else 1, key="_vl",
                label_visibility="collapsed",
                help="Hindi/Hinglish (hi-IN) ya English (en-IN)",
                format_func=lambda x: f"{'Hindi / Hinglish' if x == 'hi-IN' else 'English'} ({x})",
            )
        if picked != lang:
            st.session_state.voice_lang = picked
            st.session_state.attempt += 1
            st.rerun()

        with st.form("text_fallback", clear_on_submit=True):
            st.caption("Ya likhein (text fallback) — mic kaam na kare to")
            tc1, tc2 = st.columns([4, 1])
            txt = tc1.text_input("Entry", label_visibility="collapsed",
                                 placeholder="e.g. Ramesh ko 500 rupaye udhaar diye")
            tc2.form_submit_button("AI se banwao", type="primary")
            if txt and txt.strip():
                st.session_state.transcript = txt.strip()
                st.session_state.stage = "processing"
        if st.session_state.stage == "processing":
            st.rerun()
        return

    # ── processing ──
    if st.session_state.stage == "processing":
        st.markdown(
            '<div class="hero-card"><h3>Understanding your entry…</h3>'
            f"<p>“{st.session_state.transcript}”</p></div>",
            unsafe_allow_html=True,
        )
        with st.spinner("Gemma 4 samajh raha hai…"):
            do_extract()
        st.rerun()

    # ── clarify ──
    if st.session_state.stage == "clarify":
        st.markdown('<div class="hero-card"><h3>Ek chhota sawaal</h3>'
                    "<p>Kuch clear nahi tha — save nahi hua hai.</p></div>",
                    unsafe_allow_html=True)
        st.info(st.session_state.clarify)
        with st.form("clarify_form", clear_on_submit=True):
            txt = st.text_input("Jawab",
                                placeholder="e.g. 500 ka udhaar Ramesh ko")
            cc1, cc2 = st.columns([1, 1])
            ok = cc1.form_submit_button("Bhejo", type="primary")
            cancel = cc2.form_submit_button("Cancel")
        if ok and txt.strip():
            start_extract(txt.strip())
        if cancel:
            reset_voice()
            st.rerun()
        return

    # ── error ──
    if st.session_state.stage == "error":
        st.markdown('<div class="hero-card"><h3>Entry samajh nahi aayi</h3>'
                    "<p>Kuch bhi save nahi hua hai.</p></div>",
                    unsafe_allow_html=True)
        st.error("Interpret nahi kar paye. Dobara bolein ya likhein.")
        st.caption(f"Sunaa gaya: “{st.session_state.transcript}”")
        if st.session_state.voice_error in ("rate_limit", "timeout"):
            st.caption("Free-tier rate limit — ek minute baad try karein.")
        e1, e2 = st.columns([1, 1])
        if e1.button("Dobara try karein", type="primary", key="err_retry"):
            st.session_state.stage = "processing"
            st.rerun()
        if e2.button("Shuru se", key="err_reset"):
            reset_voice()
            st.rerun()
        return

    # ── review ──
    if st.session_state.stage == "review":
        n = len(st.session_state.pending)
        st.markdown(
            '<div class="hero-card"><h3>Review your transaction</h3>'
            f"<p>“{st.session_state.transcript}” — {n} transaction"
            f"{'s' if n > 1 else ''}. Kuch bhi save hone se pehle check karein.</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("Cancel / Dobara boliye", key="rev_cancel"):
            reset_voice()
            st.rerun()

        for i, t in enumerate(list(st.session_state.pending)):
            tid = f"rev_{st.session_state.attempt}_{i}"
            st.markdown(
                f'<div class="review-head">{type_badge(t["type"])}'
                f'<div class="rc-amt">{inr(t["amount"])}</div></div>',
                unsafe_allow_html=True,
            )
            types = ["sale", "credit", "payment", "purchase"]
            with st.form(tid):
                f1, f2 = st.columns([2, 1])
                party = f1.text_input(
                    "Customer / supplier",
                    value=t.get("party") or "",
                    placeholder="(khali = counter sale)",
                )
                amount = f2.number_input("Amount ₹", min_value=0.0, step=10.0,
                                         value=float(t["amount"]))
                f3, f4, f5 = st.columns([2, 1, 1])
                typ = f3.selectbox(
                    "Type", types, index=types.index(t["type"]),
                    format_func=lambda x: core.TYPE_LABELS[x],
                )
                pays = ["cash", "upi", "credit"]
                pay = f4.selectbox(
                    "Payment", pays,
                    index=pays.index(t["payment"]) if t.get("payment") in pays else 0,
                )
                default_d = t.get("date") or date.today().isoformat()
                dt = f5.date_input("Date", value=date.fromisoformat(default_d[:10]))
                note = st.text_input("Note", value=t.get("note") or "")
                a1, a2 = st.columns([1, 1])
                save = a1.form_submit_button("✓ Confirm and save", type="primary")
                skip = a2.form_submit_button("Skip")
            if save:
                if not amount or amount <= 0:
                    st.warning("Amount zaroori hai — save nahi hua.")
                    st.stop()
                if typ in ("credit", "payment") and not (party or "").strip():
                    st.warning("Credit/payment ke liye customer naam zaroori hai — save nahi hua.")
                    st.stop()
                entry = core.add_tx({
                    "type": typ,
                    "party": (party or "").strip(),
                    "amount": float(amount),
                    "item": t.get("item", ""),
                    "payment": pay,
                    "note": note or t.get("note", ""),
                    "ts": f"{dt.isoformat()}T{datetime.now().strftime('%H:%M:%S')}",
                })
                st.session_state.pending.pop(i)
                st.session_state.saved.append(entry)
                if st.session_state.pending:
                    st.session_state.flash = (
                        "ok", f"Saved #{entry['id']} · abhi {len(st.session_state.pending)} "
                              "transaction(s) aur review karein.")
                    st.rerun()
                st.session_state.stage = "success"
                st.rerun()
            if skip:
                st.session_state.pending.pop(i)
                if not st.session_state.pending:
                    if st.session_state.saved:
                        st.session_state.stage = "success"
                    else:
                        reset_voice()
                st.rerun()
        return

    # ── success ──
    if st.session_state.stage == "success":
        saved = st.session_state.saved
        st.markdown(
            '<div class="hero-card"><h3 style="color:#176B45">✓ Entry added successfully</h3>'
            "<p>Ledger aur customer balance dono update ho gaye.</p></div>",
            unsafe_allow_html=True,
        )
        for s in saved:
            who = s.get("party") or "Counter sale"
            amt_cls = "due" if s["type"] == "credit" else ("in" if s["type"] == "payment" else "")
            st.markdown(
                f'<div class="trow"><div><div class="who">{who}</div>'
                f'<div class="desc">{core.TYPE_LABELS[s["type"]]}'
                f'{" · " + s["note"] if s.get("note") else ""}</div></div>'
                f'<div><div class="amt {amt_cls}">{inr(s["amount"])}</div>'
                f'<div class="when">#{s["id"]}</div></div></div>',
                unsafe_allow_html=True,
            )
        if saved and saved[0].get("party"):
            bal = core.balance_of(saved[0]["party"])
            st.caption(f"{saved[0]['party']} ki outstanding balance ab: **{inr(bal)}**")
        c1, c2 = st.columns([1, 1])
        if c1.button("＋ Next entry", type="primary", key="succ_next"):
            reset_voice()
            st.rerun()
        c2.button("Ledger dekhein", key="succ_ledger", on_click=_goto_ledger)
        return


# ─────────────────────────────────────────────────────────────
# Screens
# ─────────────────────────────────────────────────────────────
if nav == "Overview":
    today = date.today()
    s = core.summary(today)
    page_head(f"Namaste, {settings['owner']}",
              today.strftime("%A, %d %B %Y") + " · aaj ki dukaan")
    stat_cards([
        ("Today's sales", inr(s["sales"]), "maal becha", "pos"),
        ("Money received", inr(s["received"]), "cash + UPI", ""),
        ("Credit given", inr(s["credit"]), "udhaar diya", "warn"),
        ("Total outstanding", inr(s["outstanding"]), "customers per baaki", "warn"),
    ])

    render_voice_section()

    st.markdown('<div class="sec-label">Recent transactions</div>', unsafe_allow_html=True)
    rows = core.ledger_rows()[:6]
    if not rows:
        empty_state("Koi transaction nahi", "Upar bolkar pehli entry karein.")
    for t in rows:
        who = t.get("party") or t.get("item") or "Counter sale"
        amt_cls = "due" if t["type"] == "credit" else ("in" if t["type"] == "payment" else "")
        st.markdown(
            f'<div class="trow"><div><div class="who">{who}</div>'
            f'<div class="desc">{core.TYPE_LABELS.get(t["type"], t["type"])}'
            f'{" · " + t["note"] if t.get("note") else ""}</div></div>'
            f'<div><div class="amt {amt_cls}">{inr(t["amount"])}</div>'
            f'<div class="when">{t["ts"][11:16]} · {t["ts"][8:10]}/{t["ts"][5:7]} · #{t["id"]}</div>'
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="sec-label">Customers with dues</div>', unsafe_allow_html=True)
    dues = [c for c in core.customers() if c["balance"] > 0][:5]
    if not dues:
        st.caption("Kisi ko udhaar baaki nahi.")
    for c in dues:
        st.markdown(
            f'<div class="trow"><div><div class="who">{c["name"]}</div>'
            f'<div class="desc">Aakhri entry {c["last"][:10]} · {c["count"]} entries</div></div>'
            f'<div><div class="amt due">{inr(c["balance"])}</div>'
            f'<div class="when">baaki</div></div></div>',
            unsafe_allow_html=True,
        )
    if dues:
        st.button("View all customers", key="view_all_cust",
                  on_click=_goto_customers)

# ─────────────────────────────────────────────────────────────
elif nav == "Voice entry":
    page_head("Voice entry", "Boliye — review karke save karein", add_btn=False)
    render_voice_section()

# ─────────────────────────────────────────────────────────────
elif nav == "Ledger":
    page_head("Ledger", "Sab entries — search, filter, undo")
    st.text_input("Search (name, item, amount)", key="led_q", placeholder="Ramesh…")
    fc1, fc2, fc3, fc4 = st.columns([1.3, 1, 1, 1])
    ftype = fc1.selectbox(
        "Type", ["All"] + core.TYPES, key="led_type",
        format_func=lambda x: "All types" if x == "All" else core.TYPE_LABELS[x],
    )
    dfrom = fc2.date_input("From", value=None, key="led_from")
    dto = fc3.date_input("To", value=None, key="led_to")
    fc4.caption("")

    rows = core.ledger_rows(
        q=st.session_state.get("led_q", ""),
        type_filter=ftype,
        date_from=dfrom if isinstance(dfrom, date) else None,
        date_to=dto if isinstance(dto, date) else None,
    )
    vis = [r for r in rows if r["type"] != "reversal"]
    stat_cards([
        ("Entries", str(len(rows)), "filter ke hisaab se", ""),
        ("Sales in view", inr(sum(r["amount"] for r in vis if r["type"] == "sale")), "", "pos"),
        ("Credit in view", inr(sum(r["amount"] for r in vis if r["type"] == "credit")), "", "warn"),
    ])

    if not rows:
        empty_state("Koi entry nahi mili", "Filter badlein.")
    for t in rows:
        who = t.get("party") or t.get("item") or "Counter sale"
        with st.container(border=True):
            c1, c2, c3 = st.columns([3.6, 1.3, 1.1])
            c1.markdown(
                f'<div class="trow flat"><div><div class="who">{who}</div>'
                f'<div class="desc">{type_badge(t["type"])} &nbsp; '
                f'{t["ts"][:16].replace("T", " ")}'
                f'{" · " + t["note"] if t.get("note") else ""}</div></div></div>',
                unsafe_allow_html=True,
            )
            amt_color = "#B45309" if t["type"] == "credit" else "#176B45" if t["type"] == "payment" else "#202923"
            sign = "−" if t["type"] == "reversal" else ""
            c2.markdown(
                f'<div style="text-align:right;padding-top:0.4rem;font-weight:700;color:{amt_color}">'
                f"{sign}{inr(t['amount'])}</div>",
                unsafe_allow_html=True,
            )
            if core.can_undo(t):
                if c3.button("Undo", key=f"undo_{t['id']}", use_container_width=True):
                    try:
                        core.undo(t["id"])
                        st.session_state.flash = (
                            "ok", f"#{t['id']} corrected — adjustment history me add hua.")
                        st.rerun()
                    except Exception as e:
                        st.session_state.flash = ("err", str(e))
                        st.rerun()
            elif t["type"] == "reversal":
                c3.caption("adjustment")
            else:
                c3.caption("corrected")

    st.download_button("Download CSV", core.export_csv(),
                       file_name="dukaan_ledger.csv", mime="text/csv")

# ─────────────────────────────────────────────────────────────
elif nav == "Customers":
    if st.session_state.sel_customer:
        name = st.session_state.sel_customer
        bal = core.balance_of(name)
        if st.button("← All customers", key="back_cust"):
            st.session_state.sel_customer = None
            st.rerun()
        page_head(name, f"Outstanding: {inr(bal)}", add_btn=False)
        hist = core.customer_history(name)
        stat_cards([
            ("Outstanding", inr(bal),
             "baaki" if bal > 0 else ("clear" if bal == 0 else "advance diya"),
             "warn" if bal > 0 else "pos"),
            ("Credit given", inr(sum(h["amount"] for h in hist if h["type"] == "credit")), "", "warn"),
            ("Payments received", inr(sum(h["amount"] for h in hist if h["type"] == "payment")), "", "pos"),
            ("Entries", str(len(hist)), "", ""),
        ])
        st.markdown('<div class="sec-label">History</div>', unsafe_allow_html=True)
        for h in hist:
            sign = "+" if h["dir"] > 0 else ("−" if h["dir"] < 0 else "")
            amt_cls = "due" if h["dir"] > 0 else ("in" if h["dir"] < 0 else "")
            st.markdown(
                f'<div class="trow"><div><div class="who">{type_badge(h["type"])}</div>'
                f'<div class="desc">{h["ts"][:16].replace("T", " ")}'
                f'{" · " + h["note"] if h.get("note") else ""}</div></div>'
                f'<div><div class="amt {amt_cls}">{sign}{inr(h["amount"])}</div>'
                f'<div class="when">#{h["id"]}</div></div></div>',
                unsafe_allow_html=True,
            )
    else:
        page_head("Customers", "Naam, balance aur aakhri entry")
        q = st.text_input("Search", placeholder="Naam dhundhein…", key="cust_q")
        custs = core.customers()
        if q:
            k = q.casefold()
            custs = [c for c in custs if k in c["name"].casefold()]
        if not custs:
            empty_state("Koi customer nahi", "Voice entry se pehla udhaar dein.")
        for c in custs:
            due = c["balance"] > 0
            bal_cls = "due" if due else ("in" if c["balance"] == 0 else "")
            tag = "baaki" if due else ("clear" if c["balance"] == 0 else "advance")
            with st.container(border=True):
                r1, r2, r3 = st.columns([3, 1.2, 1])
                r1.markdown(
                    f'<div class="trow flat"><div>'
                    f'<div class="who">{c["name"]}</div>'
                    f'<div class="desc">{tag} · aakhri {c["last"][:10]} · {c["count"]} entries</div>'
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                r2.markdown(
                    f'<div style="text-align:right;padding-top:0.4rem;font-weight:700;'
                    f'color:{"#B45309" if due else "#176B45"}">{inr(c["balance"])}</div>',
                    unsafe_allow_html=True,
                )
                if r3.button("Kholo", key=f"oc_{c['name']}", use_container_width=True):
                    st.session_state.sel_customer = c["name"]
                    st.rerun()

# ─────────────────────────────────────────────────────────────
elif nav == "Reports":
    page_head("Reports", "Aaj aur is mahine ka hisaab", add_btn=False)
    today = date.today()
    s_today = core.summary(today)
    tx = core.load_tx()
    mpre = today.strftime("%Y-%m")
    mrows = [t for t in tx if t["ts"].startswith(mpre)]
    m_sales = sum(t["amount"] for t in mrows if t["type"] == "sale")
    m_credit = sum(t["amount"] for t in mrows if t["type"] == "credit")
    m_recv = sum(t["amount"] for t in mrows if t["type"] == "payment")

    st.markdown('<div class="sec-label">Aaj</div>', unsafe_allow_html=True)
    stat_cards([
        ("Sales", inr(s_today["sales"]), "", "pos"),
        ("Received", inr(s_today["received"]), "", ""),
        ("Credit given", inr(s_today["credit"]), "", "warn"),
        ("Pending dues", inr(s_today["outstanding"]), "sab customers", "warn"),
    ])
    st.markdown(f'<div class="sec-label">{today.strftime("%B %Y")}</div>',
                unsafe_allow_html=True)
    stat_cards([
        ("Sales", inr(m_sales), f"{len(mrows)} entries", "pos"),
        ("Received", inr(m_recv), "", ""),
        ("Credit", inr(m_credit), "", "warn"),
        ("Transactions", str(len(mrows)), "is mahine", ""),
    ])

    if not mrows:
        empty_state("Is mahine koi entry nahi", "Voice entry se shuru karein.")

    with st.expander("Daily closing summary (din ke ant me)"):
        st.markdown(
            f"- **Sales (maal becha):** {inr(s_today['sales'])}\n"
            f"- **Money received (cash/UPI):** {inr(s_today['received'])}\n"
            f"- **Credit given (udhaar):** {inr(s_today['credit'])}\n"
            f"- **Purchases (supplier ko):** {inr(s_today['purchases'])}\n"
            f"- **Outstanding dues (customers per baaki):** {inr(s_today['outstanding'])}\n\n"
            "Cash movement aur credit movement alag hain — outstanding dues "
            "cash in hand nahi hain."
        )

# ─────────────────────────────────────────────────────────────
else:  # Settings
    page_head("Settings", "Dukaan aur language", add_btn=False)
    with st.form("settings_form"):
        shop = st.text_input("Shop name", value=settings["shop_name"])
        owner = st.text_input("Owner / greeting name", value=settings["owner"])
        lang = st.selectbox(
            "Interface language", ["Hinglish", "Hindi", "English"],
            index=["Hinglish", "Hindi", "English"].index(settings["language"]),
        )
        vlang = st.selectbox("Voice input language", ["hi-IN", "en-IN"],
                             index=0 if settings["voice_lang"] == "hi-IN" else 1)
        saved = st.form_submit_button("Save settings", type="primary")
    if saved:
        settings.update({"shop_name": shop, "owner": owner,
                         "language": lang, "voice_lang": vlang})
        core.save_settings(settings)
        st.session_state.voice_lang = vlang
        st.success("Saved.")

    st.markdown('<div class="sec-label">Data</div>', unsafe_allow_html=True)
    st.download_button("Export all transactions (CSV)", core.export_csv(),
                       file_name="dukaan_export.csv", mime="text/csv")
    st.caption(f"Data file: {core.TX_FILE} — local JSON, aapke computer par.")

    st.markdown('<div class="sec-label">About</div>', unsafe_allow_html=True)
    st.markdown(
        "**Dukaan AI — किराना साथी**  \n"
        "Voice-first digital munim for local shopkeepers.\n\n"
        "- **Framework:** Hermes Agent (Nous Research)  \n"
        "- **Model:** Gemma 4 · `gemma-4-26b-a4b-it` via Gemini API  \n"
        "- **Skill:** kirana-saathi (Hinglish parsing, GST rules)  \n"
        "- **License:** MIT"
    )
