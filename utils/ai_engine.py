"""
utils/ai_engine.py  |  v3 — Content-specific image prompts with per-slide generation
Each slide gets its own AI call. Slide JSON contains full image_prompt ready to use.
"""
import json, re, time
import requests
from config import OPENROUTER_KEY, FREE_MODELS, FALLBACK_MODEL, CREATOR_HANDLE

# ── Try official SDK first, fallback to requests ─────────────────────────────
try:
    from openrouter import OpenRouter
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Core API caller ────────────────────────────────────────────────────────────

def _call_openrouter_sdk(messages: list, system: str = "", model: str = None, max_tokens: int = 1500) -> str:
    client = OpenRouter(api_key=OPENROUTER_KEY)
    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)
    response = client.chat.send(
        model=model or FREE_MODELS[0],
        messages=all_messages,
        max_tokens=max_tokens,
        temperature=0.8,
    )
    return response.choices[0].message.content, model or FREE_MODELS[0]


def _call_openrouter_requests(messages: list, system: str = "", model: str = None, max_tokens: int = 1500) -> str:
    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://contentbot-agent.local",
        "X-Title": "ContentBot Agent",
    }
    models_to_try = [model] if model else FREE_MODELS[:4]
    if not model:
        models_to_try.append(FALLBACK_MODEL)
    last_error = None
    for attempt, m in enumerate(models_to_try):
        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json={"model": m, "messages": all_messages, "max_tokens": max_tokens, "temperature": 0.8},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                last_error = data["error"].get("message", "Unknown error")
                time.sleep(2 ** attempt)
                continue
            content = data["choices"][0]["message"]["content"]
            used_model = data.get("model", m)
            return content, used_model
        except requests.exceptions.HTTPError as e:
            last_error = str(e)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
            continue
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue
    raise RuntimeError(f"All models failed. Last error: {last_error}")


def _call_openrouter(messages: list, system: str = "", model: str = None, max_tokens: int = 1500) -> str:
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in .env")
    if SDK_AVAILABLE:
        try:
            return _call_openrouter_sdk(messages, system, model, max_tokens)
        except Exception:
            pass
    return _call_openrouter_requests(messages, system, model, max_tokens)


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"```json\s*|```\s*", "", raw).strip()
    depth = 0
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    return json.loads(cleaned[start:i+1])
                except json.JSONDecodeError:
                    continue
    return json.loads(cleaned)


# ═══════════════════════════════════════════════════════════════════════════════
# v2 — RICH SLIDE SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

SLIDE_SCHEMA = {
    "slide_no": 1,
    "type": "title_hook | value | cta",
    "headline": "Bold headline text",
    "subtext": "Supporting line (optional)",
    "bullets": ["Point 1", "Point 2", "Point 3"],
    "key_message": "The single most important takeaway from this slide",
    "facts": ["Specific fact with number or source", "Another concrete fact"],
    "developer_takeaway": "What the developer should DO after reading this",
    "visual_story": "Narrative description of what the viewer sees — like a movie scene",
    "scene_description": "Detailed visual composition: foreground, midground, background",
    "objects": ["Object 1 with color and position", "Object 2 with color and position", "Object 3 with color and position"],
    "icons": ["emoji/icon name — position — purpose", "emoji/icon name — position — purpose"],
    "layout": "Split 40/60 | Two-column | Centered | Timeline | Hero | Card stack",
    "background": "Color hex + texture + gradient direction if any",
    "lighting": "Lighting style: rim light, glow, volumetric, flat, dramatic",
    "camera": "Camera angle: top-down, eye-level, Dutch angle, wide shot",
    "palette": ["#primary", "#accent", "#text", "#highlight"],
    "design_notes": "Typography details, spacing rules, hierarchy notes",
    "image_prompt": "READY-TO-PASTE prompt for AI image generators. 3-4 sentences. Extremely specific.",
}


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Generate Outline (1 AI call)
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_outline(theme: dict, research: str, topic: str) -> dict:
    """Generate the narrative arc and key points for all 7 slides."""
    system = """You are a senior Instagram content strategist for a Tamil tech creator.
Create a tight narrative outline for a 7-slide carousel.
Each slide must have a clear purpose in the story arc.
RETURN ONLY VALID JSON."""

    user = f"""Topic: "{topic}"
Theme: {theme['theme']}
Post angle: {theme['post_angle']}
Research: {research[:800]}

Return ONLY this JSON:
{{
  "hook_concept": "The single idea that makes someone stop scrolling",
  "story_arc": "One sentence describing the journey from slide 1 to 7",
  "slides": [
    {{"slide_no": 1, "type": "title_hook", "purpose": "Stop the scroll — make them NEED to swipe", "key_angle": "specific angle for this hook"}},
    {{"slide_no": 2, "type": "value", "purpose": "Establish the problem/news", "key_angle": ""}},
    {{"slide_no": 3, "type": "value", "purpose": "Deep dive into detail 1", "key_angle": ""}},
    {{"slide_no": 4, "type": "value", "purpose": "Deep dive into detail 2", "key_angle": ""}},
    {{"slide_no": 5, "type": "value", "purpose": "Indian developer angle / why YOU should care", "key_angle": ""}},
    {{"slide_no": 6, "type": "value", "purpose": "Big picture / what happens next", "key_angle": ""}},
    {{"slide_no": 7, "type": "cta", "purpose": "Follow + Save nudge", "key_angle": ""}}
  ],
  "caption_hook": "First line of caption that drives engagement",
  "save_hook": "Exact line that triggers save behavior"
}}"""

    raw, model = _call_openrouter([{"role": "user", "content": user}], system, max_tokens=1200)
    return _parse_json(raw)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Generate Individual Slide (7 AI calls, one per slide)
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_slide(
    slide_no: int,
    slide_type: str,
    purpose: str,
    key_angle: str,
    outline: dict,
    theme: dict,
    research: str,
    topic: str,
) -> dict:
    """Generate ONE rich slide with full visual specification."""

    theme_color = theme.get("color", "#6366f1")
    theme_icon = theme.get("icon", "💡")

    system = f"""You are an expert Instagram visual designer AND copywriter.
You create single carousel slides with EXTREMELY detailed visual specifications.

CRITICAL: Every field must be specific. No vague language.
- "objects": list physical things with colors and exact positions
- "icons": list exact emojis with WHERE they go and WHY
- "image_prompt": must be a complete, ready-to-paste AI image prompt (3-4 sentences)
- "visual_story": describe it like a movie scene the viewer watches
- "scene_description": foreground, midground, background layers

Theme color: {theme_color}
Theme icon: {theme_icon}

RETURN ONLY VALID JSON. No markdown."""

    # Slide-specific guidance
    if slide_no == 1:
        specific_guidance = """SLIDE 1 — TITLE HOOK:
This slide must STOP THE SCROLL. Think billboard, not paragraph.
- headline: MAX 6 words, bold, punchy
- visual_story: One iconic image that communicates the entire topic instantly
- image_prompt: Should work as a standalone thumbnail. High contrast. Bold text."""
    elif slide_no == 7:
        specific_guidance = """SLIDE 7 — CTA:
This slide must look DIFFERENT from the dark value slides. Bright, high energy.
- background: Use bright gradient or solid accent color (not dark navy)
- headline: Friendly, personal
- cta_text: Exact follow text
- save_nudge: Exact save text
- image_prompt: Bright, contrasting, celebratory feel"""
    else:
        specific_guidance = f"""SLIDE {slide_no} — VALUE:
Educational slide. Developer must learn something specific.
- bullets: 3 points, each with a concrete example, number, or tool name
- developer_takeaway: What should they DO with this info
- key_message: If they forget everything else, remember THIS"""

    user = f"""Create Slide {slide_no} for this carousel.

Topic: "{topic}"
Theme: {theme['theme']}
Post angle: {theme['post_angle']}
Slide purpose: {purpose}
Key angle: {key_angle}
Research context: {research[:600]}

{specific_guidance}

Return ONLY this exact JSON:
{{
  "slide_no": {slide_no},
  "type": "{slide_type}",
  "headline": "Bold headline — max 8 words for value, max 6 for hook",
  "subtext": "One supporting line (optional, empty string if not needed)",
  "bullets": ["Point 1 with specific detail", "Point 2 with number or tool", "Point 3 with actionable takeaway"],
  "key_message": "The single most important takeaway",
  "facts": ["Concrete fact 1 with number/source", "Concrete fact 2"],
  "developer_takeaway": "What the developer should do after reading this",
  "visual_story": "Describe like a movie scene: what the viewer sees, feels, understands in 3 seconds. 40-60 words.",
  "scene_description": "Foreground: [elements]. Midground: [elements]. Background: [elements]. 40-60 words.",
  "objects": [
    "Primary object — color — exact position (e.g. 'Glowing chip icon — {theme_color} — centered top third')",
    "Secondary object — color — position",
    "Tertiary object — color — position"
  ],
  "icons": [
    "🇰🇷 — top-left — represents country context",
    "🖥️ — next to bullet 1 — represents compute",
    "→ — before each bullet — visual separator"
  ],
  "layout": "Exact layout: Split 40/60, Two-column, Centered, Timeline, etc.",
  "background": "Exact background: Dark navy #1a1a2e solid, or gradient direction, or texture",
  "lighting": "Lighting style: Indigo rim glow from left, flat even lighting, dramatic spotlight, etc.",
  "camera": "Camera angle: Eye-level flat lay, slight top-down, straight-on, etc.",
  "palette": ["{theme_color}", "#1a1a2e", "#ffffff", "#10b981"],
  "design_notes": "Typography: font, weight, size hierarchy. Spacing: padding, margins. Special: glow effects, borders, shadows. 30-50 words.",
  "image_prompt": "READY-TO-PASTE AI image prompt. 3-4 sentences. Extremely specific about: colors, layout, objects, text elements, style, mood. Include hex codes. No generic descriptions."
}}"""

    raw, model = _call_openrouter([{"role": "user", "content": user}], system, max_tokens=1500)
    slide = _parse_json(raw)

    # Add CTA-specific fields for slide 7
    if slide_no == 7:
        slide["cta_text"] = f"Follow @{CREATOR_HANDLE} for daily dev tips! 💡"
        slide["save_nudge"] = "💾 Save this — you WILL need it later."

    return slide


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Assemble Carousel
# ═══════════════════════════════════════════════════════════════════════════════

def generate_carousel(
    theme: dict,
    research: str,
    custom_topic: str,
    engagement_history: list,
    insights: dict,
) -> tuple[dict, str]:
    """
    v2: Modular per-slide generation.
    1 call for outline + 7 calls for individual slides = 8 total AI calls.
    Returns rich slide objects with pre-built image_prompts.
    """
    topic = custom_topic.strip() or theme["theme"]
    best_time = insights.get("best_time", "7:00 PM")
    theme_color = theme.get("color", "#6366f1")

    research_block = research[:1200] if research and research.strip() else f"Use your knowledge about {topic}. Focus on practical tips for Indian developers."

    # Step 1: Generate outline
    outline = _generate_outline(theme, research_block, topic)

    # Step 2: Generate each slide individually
    slides = []
    for slide_plan in outline.get("slides", []):
        slide = _generate_slide(
            slide_no=slide_plan["slide_no"],
            slide_type=slide_plan["type"],
            purpose=slide_plan["purpose"],
            key_angle=slide_plan.get("key_angle", ""),
            outline=outline,
            theme=theme,
            research=research_block,
            topic=topic,
        )
        slides.append(slide)

    # Sort by slide_no just in case
    slides.sort(key=lambda s: s.get("slide_no", 99))

    # Assemble final carousel object
    carousel = {
        "topic": topic,
        "theme": theme["theme"],
        "slides": slides,
        "caption_english": outline.get("caption_hook", f"💡 {topic} — here's what you need to know. {outline.get('save_hook', '')}"),
        "hashtags": ["#programming","#developer","#coding","#webdev","#tech","#india","#softwareengineering","#devtips","#learnprogramming","#techcreator"],
        "post_time": best_time,
        "design_palette": {
            "primary_hex": "#1a1a2e",
            "accent_hex": theme_color,
            "font_style": "Bold Montserrat or Poppins"
        },
        "viral_tip": f"Use split-layout on slides 2-5 with flag emoji + topic icon — visual contrast drives 30%+ more slide completion on {theme['theme']} carousels.",
        "save_hook": outline.get("save_hook", f"Save this — {topic} is about to change 🚀"),
    }

    # Track which model was used (use first slide's generation as proxy)
    # In practice all slides use same model chain, but we could track per-slide
    carousel["content_type"] = "carousel"
    return carousel, "openrouter/owl-alpha (v2 modular)"


# ═══════════════════════════════════════════════════════════════════════════════
# REEL SCRIPT (unchanged from v1 — already working well)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_reel_script(
    theme: dict,
    research: str,
    custom_topic: str,
    engagement_history: list,
    insights: dict,
) -> tuple[dict, str]:
    """Returns (content_dict, model_used). Tanglish 60-90 sec reel."""
    topic = custom_topic.strip() or theme["theme"]
    best_time = insights.get("best_time", "7:00 PM")
    top_themes = insights.get("top_themes", [])
    research_block = research[:1000] if research and research.strip() else f"Use your knowledge about {topic}. Focus on what Indian developers need to know."

    system = """You are a viral Tamil tech content creator on Instagram.
You write 60-90 second Tanglish reel scripts (Tamil words in English + English tech terms).
Natural Tamil: bro, da, macha, paaru, sollu, vera level, super pa, enna da ithu, kadaisila, mukkiyamana vishayam, neenga, ungaluku.
Casual, conversational, like talking to a friend.
RETURN ONLY VALID JSON. No markdown."""

    user = f"""Write a 60-90 second Tanglish Instagram Reel script.

Topic: "{topic}"
Theme: {theme['theme']}
Hook style: {theme['reel_hook']}
Research: {research_block}
Top themes: {', '.join(top_themes) if top_themes else 'not tracked yet'}
Best time: {best_time}

Return ONLY this JSON:
{{
  "topic": "{topic}",
  "theme": "{theme['theme']}",
  "hook1": "First scroll-stopping line in Tanglish (1-2 lines max)",
  "hook2": "Second punch line — question or shocking stat in Tanglish",
  "visual_hook": "Describe what the editor shows on screen during first 3 seconds",
  "value_points": [
    "Point 1 in Tanglish — specific, with tool name or number",
    "Point 2 in Tanglish",
    "Point 3 in Tanglish",
    "Point 4 in Tanglish"
  ],
  "cta": "CTA in Tanglish — follow/save/comment nudge",
  "caption_english": "Instagram caption in English with emojis, under 150 chars",
  "hashtags": ["#tech","#programming","#coding","#developer","#india","#tamiltech","#softwareengineering","#devtips","#learntocode","#techcreator"],
  "audio_mood": "lo-fi beats / trap instrumental / motivational bgm — describe what fits",
  "trending_audio_tip": "How to find trending audio for this reel type",
  "post_time": "{best_time}",
  "estimated_duration": "70 sec",
  "thumbnail_text": "Bold cover text max 5 words",
  "viral_tip": "One specific thing that will boost reach for this exact reel"
}}"""

    raw, model = _call_openrouter([{"role": "user", "content": user}], system)
    data = _parse_json(raw)
    data["content_type"] = "reel"
    return data, model


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE PROMPTS — v3: Content-specific, tool-optimized, copy-paste ready
# ═══════════════════════════════════════════════════════════════════════════════

def generate_image_prompts(content: dict, theme: dict) -> tuple[dict, str]:
    """
    v4: Compact, token-efficient image prompts (5-10K chars for carousel).
    Only includes essential info per slide to avoid exhausting API tokens.
    """
    ctype = content.get("content_type", "")
    topic = content.get("topic", theme["theme"])
    slides = content.get("slides", [])
    theme_color = theme.get("color", "#6366f1")
    theme_icon = theme.get("icon", "💡")

    # ── Build compact per-slide blocks ──
    slide_blocks = []

    if ctype == "carousel" and slides:
        for s in slides:
            sn = s.get("slide_no", "?")
            stype = s.get("type", "value")
            headline = s.get("headline", "")
            bullets = s.get("bullets", [])
            key_msg = s.get("key_message", "")
            image_prompt = s.get("image_prompt", "")

            # Compact: headline + key bullets + pre-generated image_prompt only
            lines = [f"SLIDE {sn}: {headline}"]
            if stype == "title_hook":
                lines.append("Type: HOOK — stop scroll")
            elif stype == "cta":
                lines.append("Type: CTA — bright, follow nudge")
            else:
                lines.append("Type: VALUE — educate")
            if bullets:
                lines.append("Bullets: " + " | ".join(bullets))
            if key_msg:
                lines.append(f"Key: {key_msg}")
            if image_prompt:
                lines.append(f"Visual: {image_prompt}")
            slide_blocks.append("\n".join(lines))

    elif ctype == "reel":
        thumbnail_text = content.get("thumbnail_text", "")
        hook1 = content.get("hook1", "")
        hook2 = content.get("hook2", "")

        lines = ["THUMBNAIL: Reel Cover"]
        lines.append("Format: 9:16 vertical, 1080×1920")
        if thumbnail_text:
            lines.append(f"Text: {thumbnail_text}")
        if hook1:
            lines.append(f"Hook1: {hook1}")
        if hook2:
            lines.append(f"Hook2: {hook2}")
        lines.append("Visual: Animated character, expressive face, dark navy bg, "
                     f"{theme_color} accent glow, bold white headline 3-5 words max, "
                     "dramatic rim light. 3D cartoon style.")
        slide_blocks.append("\n".join(lines))

    # ── Compact unified prompt ──
    if ctype == "carousel":
        unified_prompt = f"""CAROUSEL IMAGE PROMPT — {topic}
Format: 7 slides, 1:1 square (1080×1080), dark tech editorial
Theme: {theme['theme']} | Color: {theme_color} | Font: Montserrat Bold + Poppins
Palette: #1a1a2e (bg), {theme_color} (accent), #ffffff (text), #10b981 (highlight), #fbbf24 (CTA)
Rules: 48px padding, bold white headlines 48-60pt, body 18-24pt light gray, accent glow behind icon, consistent style across all slides.

{"\n\n".join(slide_blocks)}

Paste into ChatGPT/DALL-E or Google Flow. Generate one slide at a time for consistency."""

    else:  # reel
        unified_prompt = f"""REEL THUMBNAIL PROMPT — {topic}
Format: 9:16 vertical (1080×1920), dark tech editorial
Theme: {theme['theme']} | Color: {theme_color}
Palette: #1a1a2e (bg), {theme_color} (accent), #ffffff (text), #f59e0b (urgency)
Rules: Headline max 5 words, 60-72pt bold white, character upper body expressive face, dramatic rim light, dark vignette, text in upper third.

{"\n".join(slide_blocks)}

Paste into ChatGPT/DALL-E. Ask for edits like "make character more shocked" if needed."""

    result = {
        "unified_prompt": unified_prompt,
        "google_flow_prompt": unified_prompt,
        "ideogram_prompt": unified_prompt,
        "dalle_prompt": unified_prompt,
        "canva_instructions": unified_prompt,
        "color_palette": [theme_color, "#1a1a2e", "#ffffff", "#10b981", "#fbbf24"],
        "thumbnail_tip": f"Use {theme_color} accent on dark navy with bold headline to stop scroll",
        "text_overlay": (slides[0].get("headline", topic) if slides and ctype == "carousel" else content.get("thumbnail_text", topic))[:30],
        "slide_prompts": slide_blocks if ctype == "carousel" else [],
        "recommended_tool": "ChatGPT/DALL-E (best text) → Google Flow (fast backup) → Canva (text assembly)",
    }

    return result, "v4-compact"


def analyse_engagement(log: list, current_insights: dict) -> tuple[dict, str]:
    if not log:
        return current_insights, "no-data"

    system = """You are an Instagram growth analyst for a Tamil tech creator targeting Indian developers.
Analyse data, give specific actionable advice. Keep it blunt and practical.
RETURN ONLY VALID JSON. No markdown."""

    recent = log[:14]
    user = f"""Analyse Instagram engagement data and return updated strategy.

Data ({len(recent)} posts):
{json.dumps(recent, indent=2)}

Current follower count: under 500. Target: 1000-2000 in 30 days.

Return ONLY this JSON:
{{
  "best_time": "HH:MM AM/PM IST",
  "best_days": ["Monday", "Wednesday"],
  "top_themes": ["Theme1", "Theme2"],
  "worst_themes": ["Theme"],
  "avg_views": 0,
  "avg_likes": 0,
  "engagement_rate": "X%",
  "growth_tip": "Single most impactful action this week — be very specific",
  "stop_doing": "What is hurting reach — be specific",
  "keep_doing": "What is working",
  "caption_tip": "Caption style that will get more comments",
  "hashtag_tip": "Hashtag strategy tweak",
  "content_mix": "Recommended reel vs carousel split e.g. 70% reels 30% carousels",
  "weekly_goal": "Specific measurable target for next 7 days"
}}"""

    raw, model = _call_openrouter([{"role": "user", "content": user}], system, max_tokens=700)
    data = _parse_json(raw)
    return data, model


# ═══════════════════════════════════════════════════════════════════════════════
# INSTAGRAM API (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_ig_insights(token: str, account_id: str) -> dict:
    if not token or not account_id:
        return {"error": "Instagram credentials not set"}
    base = f"https://graph.instagram.com/v19.0/{account_id}"
    try:
        r = requests.get(
            base,
            params={"fields": "followers_count,media_count,username", "access_token": token},
            timeout=15,
        )
        r.raise_for_status()
        account = r.json()
        media_r = requests.get(
            f"{base}/media",
            params={
                "fields": "id,caption,media_type,timestamp,like_count,comments_count,permalink",
                "limit": 10,
                "access_token": token,
            },
            timeout=15,
        )
        media_r.raise_for_status()
        return {"account": account, "recent_media": media_r.json().get("data", []), "error": None}
    except Exception as e:
        return {"error": str(e), "account": {}, "recent_media": []}