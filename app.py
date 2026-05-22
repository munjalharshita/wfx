import streamlit as st
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
)
from deep_translator import GoogleTranslator
from urllib.parse import urlparse, parse_qs
import re, time

# ══════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════
GROQ_API_KEY       = st.secrets["GROQ_API_KEY"]
client             = Groq(api_key=GROQ_API_KEY)
MODEL_NAME         = "llama-3.3-70b-versatile"
MAX_TRANSCRIPT_CHARS = 80_000
TRANSLATE_CHUNK    = 3_500     # safe for GoogleTranslator free tier

# ══════════════════════════════════════════════
# LANGUAGE TABLE  — all codes verified for deep_translator
# ══════════════════════════════════════════════
OUTPUT_LANGUAGES = {
    "English":               "en",
    "Hindi (हिंदी)":         "hi",
    "Bengali (বাংলা)":       "bn",
    "Tamil (தமிழ்)":         "ta",
    "Telugu (తెలుగు)":       "te",
    "Marathi (मराठी)":       "mr",
    "Gujarati (ગુજરાતી)":    "gu",
    "Kannada (ಕನ್ನಡ)":       "kn",
    "Malayalam (മലയാളം)":    "ml",
    "Punjabi (ਪੰਜਾਬੀ)":      "pa",
    "Urdu (اردو)":            "ur",
    "Spanish (Español)":     "es",
    "French (Français)":     "fr",
    "German (Deutsch)":      "de",
    "Japanese (日本語)":      "ja",
    "Chinese (中文)":         "zh-cn",   # must be lowercase
    "Arabic (العربية)":       "ar",
    "Portuguese":            "pt",
    "Russian (Русский)":      "ru",
    "Korean (한국어)":        "ko",
}

# ══════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="YouTube Summarizer AI",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap');

html, .stApp { background:#0a0a0a; color:#fff; }

.big-title {
    font-family:'Bebas Neue',sans-serif; font-size:3.8rem; letter-spacing:4px;
    background:linear-gradient(90deg,#FF0000,#ff6b6b,#ffaa00,#FF0000);
    background-size:300%; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    text-align:center; animation:shimmer 4s infinite linear; margin-bottom:0;
}
@keyframes shimmer{0%{background-position:0%}100%{background-position:300%}}
.subtitle{text-align:center;color:#888;font-family:'Inter',sans-serif;
          font-size:1rem;margin-top:.3rem;margin-bottom:2rem;}

/* cards */
.card{background:#161616;border-radius:14px;padding:1.4rem 1.8rem;
      margin-bottom:1rem;font-family:'Inter',sans-serif;
      border-left:4px solid #FF0000;box-shadow:0 4px 24px rgba(255,0,0,.07);}
.card-blue  {border-left-color:#3b82f6!important;box-shadow:0 4px 24px rgba(59,130,246,.07)!important;}
.card-green {border-left-color:#22c55e!important;box-shadow:0 4px 24px rgba(34,197,94,.07)!important;}
.card-amber {border-left-color:#f59e0b!important;box-shadow:0 4px 24px rgba(245,158,11,.07)!important;}
.card-purple{border-left-color:#a855f7!important;box-shadow:0 4px 24px rgba(168,85,247,.07)!important;}
.card h3{font-family:'Bebas Neue',sans-serif;font-size:1.4rem;letter-spacing:1.5px;
         margin-bottom:.8rem;color:#FF0000;}
.card-blue   h3{color:#3b82f6!important;}
.card-green  h3{color:#22c55e!important;}
.card-amber  h3{color:#f59e0b!important;}
.card-purple h3{color:#a855f7!important;}
.card p{color:#ccc;line-height:1.8;margin:0;font-size:.95rem;}

/* quiz */
.quiz-q{background:#1c1c1c;border-radius:10px;padding:1rem 1.2rem;
        margin-bottom:.8rem;border:1px solid #2a2a2a;font-family:'Inter',sans-serif;}
.quiz-q p{color:#e0e0e0;margin:0 0 .5rem;font-weight:600;}
.quiz-opt{color:#aaa;font-size:.9rem;padding:.2rem 0;}
.correct{color:#22c55e!important;font-weight:700;}

/* meta pills */
.meta-pill{display:inline-block;background:#1c1c1c;border:1px solid #2a2a2a;
           border-radius:20px;padding:.3rem .9rem;font-size:.78rem;color:#bbb;
           margin:.25rem .15rem;font-family:'Inter',sans-serif;}
.prog-track{background:#222;border-radius:6px;height:5px;width:100%;margin:.4rem 0;}
.prog-fill {background:linear-gradient(90deg,#FF0000,#ff6b6b);border-radius:6px;height:5px;}

/* sidebar */
section[data-testid="stSidebar"]{background:#111!important;border-right:1px solid #1e1e1e!important;}
section[data-testid="stSidebar"] label{color:#ccc!important;font-family:'Inter',sans-serif;}

/* buttons */
.stButton>button{
    background:linear-gradient(135deg,#FF0000,#cc0000)!important;
    color:#fff!important;border:none!important;border-radius:28px!important;
    padding:.65rem 2rem!important;font-weight:700!important;font-size:1rem!important;
    font-family:'Inter',sans-serif!important;box-shadow:0 4px 20px rgba(255,0,0,.3)!important;
    transition:all .2s!important;width:100%;}
.stButton>button:hover{transform:translateY(-2px)!important;
    box-shadow:0 8px 28px rgba(255,0,0,.45)!important;}
.stDownloadButton>button{background:#1c1c1c!important;color:#fff!important;
    border:1px solid #333!important;border-radius:28px!important;
    font-family:'Inter',sans-serif!important;transition:all .2s!important;}
.stDownloadButton>button:hover{border-color:#FF0000!important;}
.stTextInput>div>div>input{background:#161616!important;color:#fff!important;
    border:2px solid #2a2a2a!important;border-radius:10px!important;
    font-family:'Inter',sans-serif!important;font-size:.95rem!important;padding:.65rem 1rem!important;}
.stTextInput>div>div>input:focus{border-color:#FF0000!important;
    box-shadow:0 0 0 3px rgba(255,0,0,.12)!important;}
.stTabs [data-baseweb="tab-list"]{background:#161616;border-radius:10px;padding:4px;}
.stTabs [aria-selected="true"]{background:#FF0000!important;border-radius:7px;color:#fff!important;}

/* loader */
.loader-wrap{text-align:center;padding:2.5rem;background:#161616;border-radius:16px;
             margin:1rem 0;border:1px solid #2a2a2a;}
.bounce{display:inline-block;font-size:5rem;animation:bounce 1s infinite;}
@keyframes bounce{0%,100%{transform:translateY(0) rotate(-5deg)}50%{transform:translateY(-18px) rotate(5deg)}}
.spin{display:inline-block;font-size:1.6rem;animation:spin 2s linear infinite;}
@keyframes spin{100%{transform:rotate(360deg)}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown('<h1 class="big-title">▶ YouTube Summarizer AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Paste any YouTube link · choose your language · get an instant AI summary ✨</p>',
    unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SIDEBAR  — read ALL settings first
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Options")

    st.markdown("**🌍 Output Language**")
    output_lang_name = st.selectbox(
        "lang", list(OUTPUT_LANGUAGES.keys()), index=0, label_visibility="collapsed")
    output_lang_code = OUTPUT_LANGUAGES[output_lang_name]

    st.markdown("---")
    st.markdown("**📏 Summary Length**")
    summary_length = st.radio(
        "len", ["Concise", "Standard", "Detailed"], index=1, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**📋 Extra Features**")
    gen_chapters  = st.checkbox("📑 Chapter Breakdown", value=True)
    gen_quiz      = st.checkbox("🧠 Quiz / Q&A",        value=True)
    gen_sentiment = st.checkbox("😊 Sentiment Analysis",value=True)
    gen_tweet     = st.checkbox("🐦 Tweet Thread",       value=False)

    st.markdown("---")
    st.markdown("### 🛡️ Edge Cases Handled")
    for b in ["✅ No transcript","✅ Private/removed","✅ Long videos",
              "✅ Non-English","✅ Shorts","✅ Bad URLs","✅ Rate limits"]:
        st.markdown(
            f'<span style="display:inline-block;background:#1e1e1e;border:1px solid #2e2e2e;'
            f'border-radius:20px;padding:.2rem .7rem;font-size:.72rem;color:#aaa;margin:.2rem .1rem;">'
            f'{b}</span>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
STATE_KEYS = [
    "short_summary","detailed_summary","key_points","takeaways",
    "quiz","chapters","sentiment","tweet_thread",
    "transcript_en","transcript_orig","orig_lang","video_id",
    "error","warnings","word_count","char_count",
    # translated versions (all tabs)
    "tr_short","tr_detailed","tr_kp","tr_ta",
    "tr_quiz","tr_chapters","tr_sentiment","tr_tweet",
]
for k in STATE_KEYS:
    if k not in st.session_state:
        st.session_state[k] = None

# ══════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════

def extract_video_id(url: str):
    if not url:
        return None, "No URL provided."
    url = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url, None
    try:
        p    = urlparse(url)
        host = p.netloc.lower()
        if not host:
            return None, "URL is missing a domain. Include https://"
        if "youtu.be" in host:
            vid = p.path.lstrip("/").split("/")[0]
        elif "youtube.com" in host:
            if p.path == "/watch":
                vid = parse_qs(p.query).get("v", [None])[0]
            elif any(p.path.startswith(x) for x in ("/shorts/","/embed/","/live/")):
                seg = p.path.lstrip("/").split("/", 1)
                vid = re.split(r"[/?]", seg[1])[0] if len(seg) > 1 else None
            else:
                return None, "Unrecognized youtube.com URL format."
        else:
            return None, "Not a YouTube URL."
        if vid and re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
            return vid, None
        return None, "Could not extract a valid 11-character video ID."
    except Exception as e:
        return None, f"URL parse error: {e}"


def fetch_transcript(video_id: str):
    """Returns (text, lang_code, [warning strings])."""
    warnings = []
    api   = YouTubeTranscriptApi()
    tlist = api.list(video_id)
    avail = list(tlist)
    if not avail:
        raise NoTranscriptFound(video_id, [])

    chosen = None
    for t in avail:                          # 1. manual EN
        if t.language_code.startswith("en") and not t.is_generated:
            chosen = t; break
    if not chosen:
        for t in avail:                      # 2. auto EN
            if t.language_code.startswith("en"):
                chosen = t
                warnings.append("⚠️ Only auto-generated English captions found — may contain errors.")
                break
    if not chosen:
        for t in avail:                      # 3. any manual
            if not t.is_generated:
                chosen = t
                warnings.append(f"ℹ️ No English transcript. Using manual {t.language} ({t.language_code}).")
                break
    if not chosen:                           # 4. first available
        chosen = avail[0]
        warnings.append(f"ℹ️ Using auto-generated {chosen.language} ({chosen.language_code}) transcript.")

    text = " ".join(s.text for s in chosen.fetch())
    return text, chosen.language_code, warnings


def translate_text(text: str, target: str) -> str:
    """Chunked translation with per-chunk retry. Never returns empty."""
    if not text or not text.strip() or target == "en":
        return text
    words   = text.split()
    chunks  = []
    buf, buf_len = [], 0
    for w in words:
        buf.append(w); buf_len += len(w) + 1
        if buf_len >= TRANSLATE_CHUNK:
            chunks.append(" ".join(buf)); buf, buf_len = [], 0
    if buf:
        chunks.append(" ".join(buf))

    out = []
    for chunk in chunks:
        result = chunk                        # fallback = original
        for attempt in range(3):
            try:
                t = GoogleTranslator(source="auto", target=target).translate(chunk)
                if t and t.strip():
                    result = t; break
            except Exception:
                time.sleep(0.7 * (attempt + 1))
        out.append(result)
    return " ".join(out)


# ── Robust parser: tries 3 strategies in order ──────────────────────────────
def parse_sections(raw: str) -> dict:
    """
    Extract SHORT_SUMMARY, DETAILED_SUMMARY, KEY_POINTS, TAKEAWAYS from LLM output.
    Tries three strategies so it never silently fails.
    """
    raw = raw.strip()

    # ── Strategy 1: our custom ===TAG=== delimiters ──────────────────────────
    TAGS = ["SHORT_SUMMARY", "DETAILED_SUMMARY", "KEY_POINTS", "TAKEAWAYS"]
    found = {}
    for i, tag in enumerate(TAGS):
        next_tags = TAGS[i+1:] + ["$$$SENTINEL$$$"]
        # build pattern that matches from ===TAG=== until any next ===TAG=== or end
        next_pattern = "|".join(re.escape(f"==={t}===") for t in next_tags[:-1])
        if next_pattern:
            pattern = rf"==={re.escape(tag)}===\s*(.*?)(?={next_pattern}|\Z)"
        else:
            pattern = rf"==={re.escape(tag)}===\s*(.*)\Z"
        m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        if m:
            found[tag] = m.group(1).strip()

    if len(found) >= 3:   # accept if ≥3 sections found
        return {
            "short_summary":    found.get("SHORT_SUMMARY",    ""),
            "detailed_summary": found.get("DETAILED_SUMMARY", ""),
            "key_points":       found.get("KEY_POINTS",       ""),
            "takeaways":        found.get("TAKEAWAYS",        ""),
        }

    # ── Strategy 2: common LLM fallback patterns ────────────────────────────
    # Handles: "**SHORT SUMMARY**\n...", "SHORT SUMMARY:\n...", "## Short Summary" etc.
    ALIASES = {
        "short_summary":    [r"short[_ ]summary", r"overview", r"brief summary"],
        "detailed_summary": [r"detailed[_ ]summary", r"detailed overview", r"full summary", r"summary"],
        "key_points":       [r"key[_ ]points?", r"main points?", r"highlights?"],
        "takeaways":        [r"(?:actionable\s+)?takeaways?", r"key takeaways?", r"action items?"],
    }
    lines = raw.split("\n")
    section_map: dict[str, int] = {}     # field -> line index of its header
    for field, patterns in ALIASES.items():
        for li, line in enumerate(lines):
            clean = re.sub(r"[#*_`=:\-]", " ", line).strip().lower()
            if any(re.search(p, clean) for p in patterns):
                if field not in section_map:
                    section_map[field] = li
    # sort by line number so we know where each section ends
    order = sorted(section_map.items(), key=lambda x: x[1])
    result2 = {}
    for idx, (field, start_li) in enumerate(order):
        end_li = order[idx+1][1] if idx+1 < len(order) else len(lines)
        content_lines = [
            l for l in lines[start_li+1:end_li]
            if l.strip() and not re.match(r"^[#*`=\-]{1,6}\s*$", l.strip())
        ]
        result2[field] = " ".join(content_lines).strip()

    if len(result2) >= 2 and any(result2.values()):
        return {
            "short_summary":    result2.get("short_summary",    ""),
            "detailed_summary": result2.get("detailed_summary", ""),
            "key_points":       result2.get("key_points",       ""),
            "takeaways":        result2.get("takeaways",        ""),
        }

    # ── Strategy 3: best-effort split into 4 equal chunks ───────────────────
    # (last resort — at least show something)
    chunks = [p.strip() for p in re.split(r"\n{2,}", raw) if p.strip()]
    def pick(i):
        return chunks[i] if i < len(chunks) else ""
    return {
        "short_summary":    pick(0),
        "detailed_summary": pick(1),
        "key_points":       pick(2),
        "takeaways":        pick(3),
    }


LENGTH_GUIDE = {
    "Concise":  "SHORT_SUMMARY in 1-2 sentences. DETAILED_SUMMARY in 2-3 sentences. KEY_POINTS with 3 bullet points. TAKEAWAYS with 2 bullet points.",
    "Standard": "SHORT_SUMMARY in 2-3 sentences. DETAILED_SUMMARY in 1 solid paragraph. KEY_POINTS with 5 bullet points. TAKEAWAYS with 3 bullet points.",
    "Detailed": "SHORT_SUMMARY in 3-4 sentences. DETAILED_SUMMARY in 2-3 paragraphs. KEY_POINTS with 7-8 bullet points. TAKEAWAYS with 5 bullet points.",
}

def summarize_with_groq(text: str, length: str = "Standard") -> dict:
    if len(text) > MAX_TRANSCRIPT_CHARS:
        text = text[:MAX_TRANSCRIPT_CHARS] + "\n\n[Transcript truncated]"

    guide = LENGTH_GUIDE.get(length, LENGTH_GUIDE["Standard"])

    # Two-message approach: system sets strict format, user gives transcript
    system_msg = f"""You are a YouTube video summarizer. You MUST respond using EXACTLY these four section headers — no markdown, no extra text before the first header, no code blocks:

===SHORT_SUMMARY===
(your text here)

===DETAILED_SUMMARY===
(your text here)

===KEY_POINTS===
- point
- point

===TAKEAWAYS===
- takeaway
- takeaway

Length guide: {guide}"""

    user_msg = f"Summarize this YouTube video transcript:\n\n{text}"

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=2000,
        temperature=0.2,
    )
    raw = resp.choices[0].message.content.strip()

    # strip any accidental markdown code fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```$",       "", raw, flags=re.MULTILINE)

    parsed = parse_sections(raw)

    # Guarantee non-empty values with sensible fallbacks
    return {
        "short_summary":    parsed["short_summary"]    or "Short summary could not be extracted.",
        "detailed_summary": parsed["detailed_summary"] or "Detailed summary could not be extracted.",
        "key_points":       parsed["key_points"]       or "- Key points could not be extracted.",
        "takeaways":        parsed["takeaways"]        or "- Takeaways could not be extracted.",
    }


def generate_quiz(text: str) -> str:
    text = text[:12_000]
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":"Generate exactly 5 multiple-choice questions with this format:\nQ1: question\nA) option\nB) option\nC) option\nD) option\nANSWER: X\n\nRepeat for Q2-Q5."},
            {"role":"user",  "content":f"Transcript:\n{text}"},
        ],
        max_tokens=900, temperature=0.4)
    return resp.choices[0].message.content


def generate_chapters(text: str) -> str:
    text = text[:15_000]
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":"Break this video into logical chapters (max 8). Format:\nCHAPTER 1: Title\n1-2 sentence description.\n\nCHAPTER 2: Title\n..."},
            {"role":"user",  "content":f"Transcript:\n{text}"},
        ],
        max_tokens=700, temperature=0.3)
    return resp.choices[0].message.content


def generate_sentiment(text: str) -> str:
    text = text[:10_000]
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":"Analyze tone. Respond EXACTLY:\nOVERALL_TONE: X\nENERGY_LEVEL: X\nFORMALITY: X\nEMOTION_TAGS: x, y, z\nAUDIENCE: sentence\nINSIGHT: sentence"},
            {"role":"user",  "content":f"Transcript:\n{text}"},
        ],
        max_tokens=400, temperature=0.3)
    return resp.choices[0].message.content


def generate_tweet(text: str) -> str:
    text = text[:10_000]
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":"Write a 6-8 tweet thread. Each tweet ≤280 chars with emojis. Number them 1/, 2/, … Start with a hook. End with CTA."},
            {"role":"user",  "content":f"Transcript:\n{text}"},
        ],
        max_tokens=700, temperature=0.6)
    return resp.choices[0].message.content


def translate_all(lang_code: str):
    """Translate every stored content field into lang_code and save to session state."""
    if lang_code == "en":
        # just copy originals
        st.session_state.tr_short    = st.session_state.short_summary
        st.session_state.tr_detailed = st.session_state.detailed_summary
        st.session_state.tr_kp       = st.session_state.key_points
        st.session_state.tr_ta       = st.session_state.takeaways
        st.session_state.tr_quiz     = st.session_state.quiz
        st.session_state.tr_chapters = st.session_state.chapters
        st.session_state.tr_sentiment= st.session_state.sentiment
        st.session_state.tr_tweet    = st.session_state.tweet_thread
        return

    def t(val):
        return translate_text(val, lang_code) if val else val

    st.session_state.tr_short    = t(st.session_state.short_summary)
    st.session_state.tr_detailed = t(st.session_state.detailed_summary)
    st.session_state.tr_kp       = t(st.session_state.key_points)
    st.session_state.tr_ta       = t(st.session_state.takeaways)
    st.session_state.tr_quiz     = t(st.session_state.quiz)
    st.session_state.tr_chapters = t(st.session_state.chapters)
    st.session_state.tr_sentiment= t(st.session_state.sentiment)
    st.session_state.tr_tweet    = t(st.session_state.tweet_thread)


# ══════════════════════════════════════════════
# RENDER HELPERS
# ══════════════════════════════════════════════

def quiz_html(raw: str) -> str:
    if not raw: return ""
    questions = re.split(r"\n(?=Q\d+[:.)])", raw.strip())
    html = ""
    for q in questions:
        lines = [l.strip() for l in q.strip().split("\n") if l.strip()]
        if not lines: continue
        q_text  = lines[0]
        options = [l for l in lines if re.match(r"^[A-Da-d][.)]\s", l)]
        ans_raw = next((l for l in lines if re.match(r"^ANSWER\s*:", l, re.I)), "")
        ans     = re.sub(r"(?i)^answer\s*:\s*", "", ans_raw).strip().upper()[:1]
        opts_h  = ""
        for opt in options:
            letter  = opt[0].upper()
            correct = (letter == ans)
            icon    = " ✅" if correct else ""
            cls     = "correct" if correct else ""
            opts_h += f'<div class="quiz-opt {cls}">{opt}{icon}</div>'
        html += f'<div class="quiz-q"><p>{q_text}</p>{opts_h}</div>'
    return html or f"<p style='color:#aaa;font-family:Inter,sans-serif;'>{raw}</p>"


def chapters_html(raw: str) -> str:
    if not raw: return ""
    blocks  = re.split(r"\n(?=CHAPTER\s+\d+[:.)])", raw.strip(), flags=re.I)
    colors  = ["#FF0000","#3b82f6","#22c55e","#f59e0b","#a855f7","#06b6d4","#ec4899","#84cc16"]
    html    = ""
    for i, blk in enumerate(b for b in blocks if b.strip()):
        parts = blk.strip().split("\n", 1)
        title = parts[0].strip()
        desc  = parts[1].strip() if len(parts) > 1 else ""
        c     = colors[i % len(colors)]
        html += f"""<div style="display:flex;gap:1rem;margin-bottom:.9rem;align-items:flex-start;">
  <div style="background:{c};color:#fff;border-radius:50%;width:30px;height:30px;
       flex-shrink:0;display:flex;align-items:center;justify-content:center;
       font-family:'Bebas Neue',sans-serif;font-size:1rem;">{i+1}</div>
  <div>
    <div style="color:{c};font-family:'Bebas Neue',sans-serif;font-size:1.1rem;letter-spacing:1px;">{title}</div>
    <div style="color:#bbb;font-family:'Inter',sans-serif;font-size:.88rem;line-height:1.6;">{desc}</div>
  </div>
</div>"""
    return html


def sentiment_html(raw: str) -> str:
    if not raw: return ""
    fields = [
        ("OVERALL_TONE","😊 Overall Tone","#22c55e"),
        ("ENERGY_LEVEL","⚡ Energy Level","#f59e0b"),
        ("FORMALITY",   "🎩 Formality",   "#3b82f6"),
        ("EMOTION_TAGS","🎭 Emotions",    "#a855f7"),
        ("AUDIENCE",    "👥 Audience",    "#FF0000"),
        ("INSIGHT",     "💡 Insight",     "#64748b"),
    ]
    html = '<div style="display:flex;flex-wrap:wrap;gap:.7rem;">'
    for key, label, color in fields:
        m = re.search(rf"(?i){re.escape(key)}\s*:\s*(.+)", raw)
        if m:
            val = m.group(1).strip()
            html += f"""<div style="background:#1c1c1c;border:1px solid #2a2a2a;border-radius:10px;
  padding:.7rem 1rem;flex:1;min-width:200px;">
  <div style="font-size:.72rem;color:{color};font-weight:700;letter-spacing:1px;
       font-family:'Inter',sans-serif;margin-bottom:.3rem;">{label}</div>
  <div style="color:#ddd;font-family:'Inter',sans-serif;font-size:.9rem;">{val}</div>
</div>"""
    html += "</div>"
    return html


def show_steps(active: int):
    STEPS = ["Fetch","→ EN","Summarize","Extras","Translate"]
    parts = []
    for i, s in enumerate(STEPS):
        if   i <  active: col, icon = "#22c55e", "✅"
        elif i == active: col, icon = "#FF0000", "🔴"
        else:             col, icon = "#444",    "⬜"
        parts.append(
            f'<span style="color:{col};font-family:Inter,sans-serif;font-size:.82rem;'
            f'font-weight:{"700" if i==active else "400"};">{icon} {s}</span>')
    _steps_slot.markdown(
        '<div style="display:flex;gap:1.6rem;justify-content:center;margin:.5rem 0;">'
        + "  ".join(parts) + "</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# INPUT ROW
# ══════════════════════════════════════════════
c1, c2 = st.columns([6, 1])
with c1:
    url = st.text_input("url", label_visibility="collapsed",
        placeholder="Paste YouTube link (watch / shorts / youtu.be / embed)…")
with c2:
    go = st.button("✨ Go")

# ══════════════════════════════════════════════
# PROCESSING
# ══════════════════════════════════════════════
if go:
    for k in STATE_KEYS:
        st.session_state[k] = None
    st.session_state.warnings = []

    vid, url_err = extract_video_id(url)
    if not vid:
        st.session_state.error = f"❌ {url_err}"
    else:
        _loader     = st.empty()
        _steps_slot = st.empty()

        _loader.markdown("""
<div class="loader-wrap">
  <div class="bounce">🤖</div>
  <h3 style="color:#FF0000;font-family:'Bebas Neue',sans-serif;font-size:2.2rem;letter-spacing:3px;">
    AI is reading the video for you…</h3>
  <div class="spin">⚙️</div>
  <p style="color:#777;font-size:.9rem;">May take a moment for long videos ☕</p>
</div>""", unsafe_allow_html=True)

        try:
            # ── 1. Fetch ──────────────────────────────────
            show_steps(0)
            raw_text, lang, fetch_warns = fetch_transcript(vid)
            st.session_state.orig_lang       = lang
            st.session_state.transcript_orig = raw_text
            st.session_state.warnings        = fetch_warns
            st.session_state.word_count      = len(raw_text.split())
            st.session_state.char_count      = len(raw_text)

            if not raw_text.strip():
                raise ValueError("Transcript is completely empty — nothing to summarize.")
            if st.session_state.word_count < 20:
                st.session_state.warnings.append(
                    "⚠️ Very short transcript (< 20 words). Likely a short-form video; summary may be limited.")
            if st.session_state.char_count > MAX_TRANSCRIPT_CHARS:
                st.session_state.warnings.append(
                    f"⚠️ Long video: only first {MAX_TRANSCRIPT_CHARS:,} of "
                    f"{st.session_state.char_count:,} chars processed.")

            # ── 2. Translate transcript → English ─────────
            show_steps(1)
            if not lang.startswith("en"):
                transcript_en = translate_text(raw_text, "en")
                st.session_state.warnings.append(
                    f"ℹ️ Transcript ({lang}) translated to English for AI analysis.")
            else:
                transcript_en = raw_text
            st.session_state.transcript_en = transcript_en

            # ── 3. Summarize ──────────────────────────────
            show_steps(2)
            result = summarize_with_groq(transcript_en, summary_length)
            st.session_state.short_summary    = result["short_summary"]
            st.session_state.detailed_summary = result["detailed_summary"]
            st.session_state.key_points       = result["key_points"]
            st.session_state.takeaways        = result["takeaways"]
            st.session_state.video_id         = vid

            # ── 4. Extra features ─────────────────────────
            show_steps(3)
            if gen_quiz:
                try: st.session_state.quiz      = generate_quiz(transcript_en)
                except Exception as e: st.session_state.quiz = f"Quiz generation failed: {e}"
            if gen_chapters:
                try: st.session_state.chapters  = generate_chapters(transcript_en)
                except Exception as e: st.session_state.chapters = f"Chapter generation failed: {e}"
            if gen_sentiment:
                try: st.session_state.sentiment = generate_sentiment(transcript_en)
                except Exception as e: st.session_state.sentiment = f"Sentiment analysis failed: {e}"
            if gen_tweet:
                try: st.session_state.tweet_thread = generate_tweet(transcript_en)
                except Exception as e: st.session_state.tweet_thread = f"Tweet thread generation failed: {e}"

            # ── 5. Translate ALL output ───────────────────
            show_steps(4)
            translate_all(output_lang_code)

            show_steps(5)

        except TranscriptsDisabled:
            st.session_state.error = "🚫 Transcripts/captions are disabled for this video."
        except NoTranscriptFound:
            st.session_state.error = "🚫 No transcript or captions found for this video."
        except VideoUnavailable:
            st.session_state.error = "🚫 Video unavailable — private, age-restricted, or removed."
        except ValueError as e:
            st.session_state.error = f"⚠️ {e}"
        except Exception as e:
            msg = str(e).lower()
            if "rate_limit" in msg or "rate limit" in msg:
                st.session_state.error = "⏳ Groq rate limit hit. Wait ~30 s and retry."
            elif "api_key" in msg or "authentication" in msg or "x-api-key" in msg:
                st.session_state.error = "🔑 Invalid/missing GROQ_API_KEY — check secrets.toml."
            elif "quota" in msg:
                st.session_state.error = "📊 Groq quota exceeded. Check console.groq.com."
            else:
                st.session_state.error = f"⚠️ Unexpected error: {e}"
        finally:
            _loader.empty()
            _steps_slot.empty()

# ══════════════════════════════════════════════
# ERROR DISPLAY
# ══════════════════════════════════════════════
if st.session_state.error:
    st.error(st.session_state.error)
    e = st.session_state.error
    if "disabled" in e or "No transcript" in e:
        st.info("💡 Try a video that shows 'CC' (closed captions) in the YouTube player.")
    elif "unavailable" in e.lower() or "private" in e.lower():
        st.info("💡 Only public, non-age-restricted videos can be summarized.")
    elif "rate limit" in e.lower():
        st.info("💡 Free Groq tier: 14,400 req/day. Wait a moment and retry.")
    elif "api_key" in e.lower():
        st.info("💡 Get a free key at [console.groq.com](https://console.groq.com/keys).")

if st.session_state.warnings:
    for w in st.session_state.warnings:
        st.warning(w)

# ══════════════════════════════════════════════
# OUTPUT
# ══════════════════════════════════════════════
if st.session_state.short_summary:

    lang_badge = (
        f" <span style='color:#888;font-size:.76rem;font-weight:400;'>({output_lang_name})</span>"
        if output_lang_code != "en" else ""
    )

    # ── Thumbnail + stats ─────────────────────
    tc, mc = st.columns([2, 3])
    with tc:
        st.image(f"https://img.youtube.com/vi/{st.session_state.video_id}/hqdefault.jpg",
                 use_container_width=True)
    with mc:
        st.markdown("### 📊 Stats")
        wc  = st.session_state.word_count or 0
        cc  = st.session_state.char_count or 0
        fp  = min(100, int(cc / MAX_TRANSCRIPT_CHARS * 100))
        st.markdown(f"""
<span class="meta-pill">📝 {wc:,} words</span>
<span class="meta-pill">🔤 {cc:,} chars</span>
<span class="meta-pill">🌐 Source: {st.session_state.orig_lang or "?"}</span>
<span class="meta-pill">📤 Output: {output_lang_name}</span>
<span class="meta-pill">📏 {summary_length}</span>
<br><br>
<div style="font-size:.74rem;color:#777;font-family:Inter,sans-serif;">Model context used</div>
<div class="prog-track"><div class="prog-fill" style="width:{fp}%"></div></div>
<div style="font-size:.71rem;color:#555;font-family:Inter,sans-serif;">{fp}%</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # ── TABS ──────────────────────────────────
    tabs = st.tabs(["📋 Summary","📑 Chapters","🧠 Quiz","😊 Sentiment","🐦 Tweet Thread","📜 Transcript"])

    # ────────────────── Summary ───────────────
    with tabs[0]:
        short    = st.session_state.tr_short    or st.session_state.short_summary
        detailed = st.session_state.tr_detailed or st.session_state.detailed_summary
        kp       = st.session_state.tr_kp       or st.session_state.key_points
        ta       = st.session_state.tr_ta       or st.session_state.takeaways

        st.markdown(f"""
<div class="card">
  <h3>⚡ SHORT SUMMARY{lang_badge}</h3>
  <p>{short}</p>
</div>""", unsafe_allow_html=True)

        st.markdown(f"""
<div class="card card-blue">
  <h3>📖 DETAILED SUMMARY{lang_badge}</h3>
  <p>{detailed}</p>
</div>""", unsafe_allow_html=True)

        ka, kb = st.columns(2)
        with ka:
            st.markdown(f"""
<div class="card card-green">
  <h3>🎯 KEY POINTS{lang_badge}</h3>
  <p>{kp.replace(chr(10),'<br>')}</p>
</div>""", unsafe_allow_html=True)
        with kb:
            st.markdown(f"""
<div class="card card-amber">
  <h3>💡 TAKEAWAYS{lang_badge}</h3>
  <p>{ta.replace(chr(10),'<br>')}</p>
</div>""", unsafe_allow_html=True)

        st.markdown("### ⬇️ Downloads")
        full_txt = (
            f"YOUTUBE VIDEO SUMMARY  |  Language: {output_lang_name}  |  Length: {summary_length}\n"
            f"{'='*60}\n\nSHORT SUMMARY:\n{short}\n\n"
            f"DETAILED SUMMARY:\n{detailed}\n\nKEY POINTS:\n{kp}\n\nTAKEAWAYS:\n{ta}\n"
        )
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("📄 Summary (.txt)", full_txt, file_name="summary.txt")
        with d2:
            st.download_button("📜 Transcript (EN)", st.session_state.transcript_en or "",
                               file_name="transcript_en.txt")
        with d3:
            if st.session_state.orig_lang and not st.session_state.orig_lang.startswith("en"):
                st.download_button(
                    f"🌍 Transcript ({st.session_state.orig_lang})",
                    st.session_state.transcript_orig or "",
                    file_name=f"transcript_{st.session_state.orig_lang}.txt")

    # ────────────────── Chapters ──────────────
    with tabs[1]:
        if not gen_chapters:
            st.info("Enable **Chapter Breakdown** in the sidebar ←")
        else:
            raw_ch = st.session_state.tr_chapters or st.session_state.chapters
            if raw_ch:
                st.markdown(f"""
<div class="card card-purple">
  <h3>📑 CHAPTER BREAKDOWN{lang_badge}</h3>
  {chapters_html(raw_ch)}
</div>""", unsafe_allow_html=True)
            else:
                st.info("Chapters not generated.")

    # ────────────────── Quiz ──────────────────
    with tabs[2]:
        if not gen_quiz:
            st.info("Enable **Quiz / Q&A** in the sidebar ←")
        else:
            raw_qz = st.session_state.tr_quiz or st.session_state.quiz
            if raw_qz:
                st.markdown("### 🧠 Comprehension Quiz")
                st.caption("Correct answers highlighted in green ✅")
                st.markdown(quiz_html(raw_qz), unsafe_allow_html=True)
            else:
                st.info("Quiz not generated.")

    # ────────────────── Sentiment ─────────────
    with tabs[3]:
        if not gen_sentiment:
            st.info("Enable **Sentiment Analysis** in the sidebar ←")
        else:
            raw_se = st.session_state.tr_sentiment or st.session_state.sentiment
            if raw_se:
                st.markdown("### 😊 Tone & Sentiment Analysis")
                st.markdown(sentiment_html(raw_se), unsafe_allow_html=True)
            else:
                st.info("Sentiment not generated.")

    # ────────────────── Tweet Thread ──────────
    with tabs[4]:
        if not gen_tweet:
            st.info("Enable **Tweet Thread** in the sidebar ←")
        else:
            raw_tw = st.session_state.tr_tweet or st.session_state.tweet_thread
            if raw_tw:
                st.markdown(f"""
<div class="card card-blue">
  <h3>🐦 TWEET THREAD{lang_badge}</h3>
  <p>{raw_tw.replace(chr(10),'<br>')}</p>
</div>""", unsafe_allow_html=True)
                st.download_button("📋 Download Thread", raw_tw, file_name="tweet_thread.txt")
            else:
                st.info("Tweet thread not generated.")

    # ────────────────── Transcript ────────────
    with tabs[5]:
        with st.expander("📜 English Transcript", expanded=False):
            st.write(st.session_state.transcript_en)
        if st.session_state.orig_lang and not st.session_state.orig_lang.startswith("en"):
            with st.expander(f"🌍 Original ({st.session_state.orig_lang}) Transcript", expanded=False):
                st.write(st.session_state.transcript_orig)

    st.divider()
    if st.button("🔄 Summarize Another Video"):
        for k in STATE_KEYS:
            st.session_state[k] = None
        st.rerun()

