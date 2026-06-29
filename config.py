"""
config.py — 7-day content cycle, file paths, JSON helpers
Updated: Latest 2026 free OpenRouter models, official SDK support
"""
import os, json, datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── File paths ───────────────────────────────────────────────────────────────
STATE_FILE      = DATA_DIR / "state.json"
ENGAGEMENT_FILE = DATA_DIR / "engagement.json"
REVIEW_FILE     = DATA_DIR / "review_queue.json"
APPROVED_FILE   = DATA_DIR / "approved.json"
INSIGHTS_FILE   = DATA_DIR / "insights.json"

# ── Keys ─────────────────────────────────────────────────────────────────────
OPENROUTER_KEY  = os.getenv("OPENROUTER_API_KEY", "")
IG_TOKEN        = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
IG_ACCOUNT_ID   = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
CREATOR_HANDLE  = os.getenv("CREATOR_HANDLE", "your_handle")

# ── Latest 2026 Free OpenRouter Models (priority order) ─────────────────────
# Updated with newest free models as of mid-2026
FREE_MODELS = [
    "openrouter/owl-alpha",                         # OpenRouter's own model — best for creative
    "nvidia/nemotron-3-ultra-550b-a55b:free",       # NVIDIA — massive context, great reasoning
    "poolside/laguna-m.1:free",                     # Poolside — excellent for code/tech content
    "openai/gpt-oss-120b:free",                     # OpenAI OSS — strong general purpose
    "cohere/north-mini-code:free",                  # Cohere — optimized for code/structured output
    "google/gemma-4-31b-it:free",                   # Google Gemma 4 — fast, reliable
    "meta-llama/llama-4-maverick:free",             # Meta — fallback, proven
    "deepseek/deepseek-chat-v3-0324:free",          # DeepSeek — reasoning powerhouse
]
PRIMARY_MODEL  = FREE_MODELS[0]
FALLBACK_MODEL = "openrouter/auto"  # Let OpenRouter pick best available free model

# ── 7-Day Content Cycle ──────────────────────────────────────────────────────
CONTENT_CYCLE = [
    {
        "day": 1, "theme": "Tech News", "icon": "📰", "color": "#6366f1",
        "tag": "tech-news",
        "perplexity_prompt": (
            "What are the top 3 most important tech news stories from the last 48 hours? "
            "Focus on: new product launches, big company announcements, AI releases, or major developer tools. "
            "For each story give: headline, what happened (2-3 sentences), why developers should care, "
            "and one specific tool name or number/stat. Format clearly."
        ),
        "post_angle": "Breaking news — what happened, why it matters for developers",
        "reel_hook": "shock stat or breaking news style",
        "image_style": "Dark background, bold breaking-news headline text, tech icons/logos, red accent glow",
    },
    {
        "day": 2, "theme": "AI & ML", "icon": "🤖", "color": "#8b5cf6",
        "tag": "ai-ml",
        "perplexity_prompt": (
            "What are the latest AI tools, models, or updates released in the last week that software developers should know about? "
            "Include: tool names, what they do, who made them, how developers can use them today, "
            "and any free vs paid info. Give specific examples and use cases."
        ),
        "post_angle": "Practical AI tools devs can use today — real workflows, real examples",
        "reel_hook": "'5 AI tools that will save you 10 hours this week' style",
        "image_style": "Purple/violet gradient, robot/brain icons, glowing neural network lines, futuristic fonts",
    },
    {
        "day": 3, "theme": "Cloud & DevOps", "icon": "☁️", "color": "#0ea5e9",
        "tag": "cloud-devops",
        "perplexity_prompt": (
            "What are the most useful AWS, GCP, or Azure tips, new features, or cost-saving tricks "
            "announced or trending this week? Include Docker, Kubernetes, CI/CD if relevant. "
            "Be specific: give actual commands, service names, and real numbers (cost savings, performance gains)."
        ),
        "post_angle": "Practical cloud tip that saves time or money — with real numbers",
        "reel_hook": "'Stop paying $X for Y, do this instead' or 'This one AWS setting...'",
        "image_style": "Sky blue gradient, cloud icons, AWS/GCP logos, clean minimal tech aesthetic",
    },
    {
        "day": 4, "theme": "Backend Dev", "icon": "⚙️", "color": "#10b981",
        "tag": "backend",
        "perplexity_prompt": (
            "What are the most useful backend development tips, common mistakes to avoid, or best practices "
            "trending among developers right now? Cover: Node.js, Python, FastAPI, databases, REST APIs, system design. "
            "Include specific code patterns, mistakes with fixes, or performance tips with real numbers."
        ),
        "post_angle": "Coding pattern or common mistake — show the wrong way then the right way",
        "reel_hook": "'This one mistake is killing your API performance' or 'Most devs write X wrong'",
        "image_style": "Dark green/emerald, code editor screenshot style, terminal aesthetic, matrix-like",
    },
    {
        "day": 5, "theme": "Frontend Dev", "icon": "🎨", "color": "#f59e0b",
        "tag": "frontend",
        "perplexity_prompt": (
            "What are the most useful React, CSS, or frontend development tips, tricks, or tools "
            "trending this week? Include: performance tricks, CSS one-liners, React hooks tips, "
            "UI/UX mistakes, new npm packages. Give specific code examples or before/after comparisons."
        ),
        "post_angle": "Visual tip — CSS trick, React pattern, show before/after",
        "reel_hook": "'90% of devs don\'t know this CSS trick' or before/after UI transformation",
        "image_style": "Warm amber/orange, browser mockup showing before/after, colorful UI components",
    },
    {
        "day": 6, "theme": "Security", "icon": "🔒", "color": "#ef4444",
        "tag": "security",
        "perplexity_prompt": (
            "What are the most important cybersecurity vulnerabilities, breaches, or security tips "
            "for developers from the last week? Include: specific CVEs if any, OWASP vulnerabilities, "
            "secure coding mistakes with fixes, real breach examples with company names and impact. "
            "Make it urgent and actionable for backend/full-stack developers."
        ),
        "post_angle": "Scare them first, then give the fix — real breach + how to prevent it",
        "reel_hook": "'Your app is vulnerable right now if...' or 'X company got hacked because...'",
        "image_style": "Red/dark red, lock icon, warning symbols, hacker aesthetic, urgent feel",
    },
    {
        "day": 7, "theme": "Myths & Facts", "icon": "💡", "color": "#ec4899",
        "tag": "myths-facts",
        "perplexity_prompt": (
            "List 5 common myths or misconceptions about programming, software development, or tech careers "
            "that are still widely believed in 2026. For each myth: state the myth clearly, "
            "explain why it\'s wrong with evidence/data, give the actual fact/truth. "
            "Focus on myths that will surprise even experienced developers."
        ),
        "post_angle": "Myth bust — make people feel smart, drive saves",
        "reel_hook": "'Everyone told you X, but the truth is...' — most popular format for saves",
        "image_style": "Pink/magenta, 'MYTH vs FACT' split design, bold contrast, truth-bomb aesthetic",
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_json(path: Path, default=None):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default if default is not None else {}

def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, default=str))

def append_json_list(path: Path, item: dict, limit: int = 200):
    lst = load_json(path, [])
    lst.insert(0, item)
    save_json(path, lst[:limit])

def get_today_cycle() -> dict:
    state = load_json(STATE_FILE, {"current_day": 1})
    idx = (state.get("current_day", 1) - 1) % 7
    return CONTENT_CYCLE[idx]

def get_state() -> dict:
    return load_json(STATE_FILE, {"current_day": 1})

def advance_day():
    state = load_json(STATE_FILE, {"current_day": 1})
    today = str(datetime.date.today())
    if state.get("last_advanced") == today:
        return False
    state["current_day"] = (state.get("current_day", 1) % 7) + 1
    state["last_advanced"] = today
    save_json(STATE_FILE, state)
    return True
