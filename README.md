# ▶ YouTube Summarizer AI


## ✨ Features

### Core
- Short summary, detailed summary, key points, actionable takeaways
- Adjustable summary length: Concise / Standard / Detailed
- Thumbnail display + transcript word/character count

### 🌍 Translation (NEW)
- **20 output languages** including Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu, Spanish, French, German, Japanese, Chinese, Arabic, Portuguese, Russian, Korean
- Full summary translated to your chosen language
- Chunked translation with retry — handles large transcripts safely

### 📑 Chapter Breakdown (NEW)
- AI-generated chapter structure showing how the video flows
- Color-coded chapter numbers

### 🧠 Quiz / Q&A (NEW)
- 5 multiple-choice comprehension questions
- Correct answers highlighted in green

### 😊 Sentiment Analysis (NEW)
- Overall tone, energy level, formality
- Emotion tags, intended audience, communication style insight

### 🐦 Tweet Thread (NEW)
- Converts video into a ready-to-post 6-8 tweet thread
- Downloadable as .txt

### ⬇️ Downloads
- Summary .txt in output language
- English transcript
- Original language transcript (if non-English)

---

## 🛡️ Edge Cases Handled

| Scenario | Handling |
|---|---|
| No transcript / captions disabled | Clear error + tips shown |
| Private / removed / age-restricted video | Clear error message |
| Invalid or malformed YouTube URL | URL parser catches and explains |
| Non-English video | Auto-detected, translated to EN before analysis |
| Very long video (>80k chars) | Transcript truncated with warning |
| Short-form / Shorts (<20 words) | Warning shown, summary still attempted |
| Empty transcript | Raises clear error |
| Groq rate limit hit | Detected from error message, user-friendly hint |
| Invalid API key | Detected and explained with link to get a key |
| Translation API failure | 3-retry logic per chunk, falls back to original on failure |
| Auto-generated vs manual captions | Prefers manual EN > auto EN > manual other > auto other |

---

## Notes
- Model: `llama-3.3-70b-versatile` on Groq (free tier: 14,400 req/day)
- Max transcript: 80,000 characters (~2hr video)
- Translation powered by `deep-translator` (Google Translate, no API key needed)