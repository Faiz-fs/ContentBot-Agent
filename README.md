# 🚀 ContentBot Agent — Free Tamil Tech Creator AI

**100% free. No paid API required.**
- ✅ OpenRouter free models (Llama 4, DeepSeek V3, etc.)
- ✅ Perplexity Pro via manual copy-paste
- ✅ Image prompts for Google Flow, Ideogram, Canva, DALL-E

---

## ⚡ Setup (5 minutes)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Create .env
cp .env.example .env
# Open .env → add your OpenRouter key

# 3. Run
streamlit run app.py
```

Open: `http://localhost:8501`

---

## 🔑 Only 1 Key Needed

**OpenRouter** (free, no credit card):
1. Go to https://openrouter.ai → Sign up
2. Dashboard → Keys → Create Key
3. Paste in `.env` as `OPENROUTER_API_KEY=...`

Free tier: 200 requests/day, 20/min. More than enough.

---

## 📋 Daily Workflow

```
Morning
  1. Open app → Research Prompts tab
  2. Copy today's Perplexity prompt
  3. Paste in perplexity.ai → copy result
  4. Paste result back → Save

  5. Go to Generate tab → Generate Now
     → Reel Script (Tanglish)
     → Carousel Post (English)

  6. Go to Review tab → check → Approve

  7. Go to Image Prompts → generate for each piece
     → paste in Google Flow / Ideogram / Canva

  8. Post at recommended time

Evening (after 24h)
  9. Go to Engagement tab → log views/likes/saves
     → AI auto-updates your best time & strategy
```

**Automated (happens without you):**
- 6:00 AM IST → Auto-generates reel + carousel drafts
- 12:00 AM IST → Day advances to next theme

---

## 🗓 7-Day Cycle

| Day | Theme | Language |
|-----|-------|----------|
| 1 | 📰 Tech News | Post: English, Reel: Tanglish |
| 2 | 🤖 AI & ML | Post: English, Reel: Tanglish |
| 3 | ☁️ Cloud & DevOps | Post: English, Reel: Tanglish |
| 4 | ⚙️ Backend Dev | Post: English, Reel: Tanglish |
| 5 | 🎨 Frontend Dev | Post: English, Reel: Tanglish |
| 6 | 🔒 Security | Post: English, Reel: Tanglish |
| 7 | 💡 Myths & Facts | Post: English, Reel: Tanglish |

---

## 🖼 Image Generation (All Free)

The app generates ready-to-paste prompts for:

| Tool | Best for |
|------|----------|
| Google Flow / ImageFX | Photorealistic thumbnails |
| Ideogram.ai | Text-on-image carousels |
| Canva AI | Quick branded slides |
| ChatGPT DALL-E | Creative thumbnails |

---

## 📁 Files

```
content_agent/
├── app.py              # Main Streamlit app
├── config.py           # 7-day cycle, settings, helpers
├── requirements.txt
├── .env.example
├── utils/
│   ├── ai_engine.py    # OpenRouter calls (reel, carousel, images, engagement)
│   └── scheduler.py    # Auto daily generation
└── data/               # Auto-created
    ├── state.json       # Current day
    ├── review_queue.json
    ├── approved.json
    ├── engagement.json
    ├── insights.json
    └── scheduler.log
```

---

## 🆓 Free AI Models Used

Priority order (auto-fallback):
1. `meta-llama/llama-4-maverick:free` — Best overall
2. `deepseek/deepseek-chat-v3-0324:free` — Strong reasoning
3. `meta-llama/llama-4-scout:free` — Fast
4. `openrouter/free` — OpenRouter auto-pick fallback
