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
# IMAGE PROMPTS — v5: Rich slide-specific prompts for AI image generators
# Each slide gets a detailed, copy-paste-ready prompt with exact layout,
# colors, icons, typography, and mood. Optimized for DALL-E, Midjourney,
# Ideogram, and Flux to produce consistent dark-tech editorial PNGs.
# ═══════════════════════════════════════════════════════════════════════════════

def _build_slide_prompt(s: dict, topic: str, theme_color: str) -> str:
    """Build a rich, detailed image prompt for a single carousel slide."""
    sn = s.get("slide_no", 1)
    stype = s.get("type", "value")
    headline = s.get("headline", topic)
    bullets = s.get("bullets", [])
    key_msg = s.get("key_message", "")
    subtext = s.get("subtext", "")
    visual_story = s.get("visual_story", "")
    scene = s.get("scene_description", "")
    objects = s.get("objects", [])
    icons = s.get("icons", [])
    layout = s.get("layout", "")
    background = s.get("background", "")
    lighting = s.get("lighting", "")
    palette = s.get("palette", [])
    design_notes = s.get("design_notes", "")

    # Base style that applies to every slide
    base_style = (
        "Dark tech editorial Instagram carousel slide, 1:1 square 1080x1080, "
        "clean modern UI design, no photorealistic clutter, flat graphic design with subtle depth, "
        "professional social media aesthetic, crisp vector-like elements, high contrast, "
        "no text overlay in the image itself — all text described as design elements only."
    )

    # Extract palette colors for the prompt
    bg_color = "#1a1a2e"
    accent = theme_color
    text_color = "#ffffff"
    highlight = "#10b981"
    cta_color = "#fbbf24"
    for p in palette:
        if p and p.startswith("#"):
            if "bg" in p.lower() or "background" in p.lower():
                pass  # keep default
            else:
                if p != theme_color and p != "#1a1a2e" and p != "#ffffff" and p != "#10b981":
                    cta_color = p

    # Build the prompt based on slide type
    if sn == 1 or stype == "title_hook":
        # HOOK SLIDE — dramatic, centered icon, bold headline, corner logos/badges
        prompt = (
            f"A dark navy background ({bg_color}) with a glowing chip/AI icon at the exact center, "
            f"radiating a soft {accent} light with subtle bloom glow. "
            f"Bold white headline text reading '{headline}' placed prominently in the upper-middle area, "
            f"in a modern sans-serif font (Montserrat Bold or similar), large and commanding. "
        )
        if subtext:
            prompt += f"A smaller supporting line in light gray below the headline reads '{subtext}'. "
        if bullets:
            prompt += f"Three clean bullet points in light indigo text arranged vertically below, each with a small {highlight} dot marker. "
        if objects:
            for obj in objects[:3]:
                prompt += f"{obj}. "
        if icons:
            for icon in icons[:2]:
                prompt += f"{icon}. "
        prompt += (
            f"Small credibility logos or badges placed in opposite bottom corners (e.g., news source and company logos). "
            f"The lighting is dramatic with a subtle {accent} glow emanating from the central icon. "
            f"The mood is urgent, cutting-edge, and attention-grabbing — perfect for a tech news hook slide. "
            f"Style: sleek SaaS product illustration, dark mode aesthetic, 8K detail, no text overlay on image."
        )

    elif sn == 7 or stype == "cta":
        # CTA SLIDE — bright, different from dark slides, follow/save nudge
        prompt = (
            f"A bright {accent} gradient background transitioning from vivid {accent} at center to a lighter periwinkle shade at edges, "
            f"with a faint hexagonal neural network mesh overlay in lighter tones at 15% opacity. "
            f"Bold white sans-serif headline '{headline}' centered in the top third, large and friendly. "
        )
        if bullets:
            prompt += f"Three bullet points with arrow icons in light indigo on the left side listing key highlights. "
        prompt += (
            f"A large rounded pill-shaped 'Follow' CTA button in white with {accent} text placed below the headline. "
            f"A glowing amber ({cta_color}) bookmark icon and 'Save this post!' nudge at the bottom. "
            f"Small floating chip and cloud icons in the corners as decorative elements. "
            f"Confetti dots in white and {accent} scattered in the top-right corner. "
            f"The mood is friendly, inviting, high-energy, and action-oriented — a celebratory call-to-action slide. "
            f"Style: modern flat illustration, optimistic magazine-cover aesthetic, clean graphic design, no photorealistic elements."
        )

    elif "split" in layout.lower() or "two-column" in layout.lower() or "two column" in layout.lower():
        # SPLIT / TWO-COLUMN LAYOUT — e.g., partnership slides, country stories
        prompt = (
            f"A dark navy background ({bg_color}) with a vertical {accent} divider line running down the center. "
            f"The left side features a large icon or flag emoji paired with a topic symbol (e.g., chip, GPU, country flag). "
            f"The right side contains a dark card panel with three clean bullet points in white text, "
            f"each with a small {highlight} dot or arrow marker. "
        )
        if headline:
            prompt += f"Bold white headline '{headline}' placed above the right card with an {accent} accent underline. "
        if subtext:
            prompt += f"A small {accent} label badge in the top-left corner reading '{subtext}'. "
        if objects:
            for obj in objects[:3]:
                prompt += f"{obj}. "
        prompt += (
            f"The mood is informative and authoritative, with a clean editorial design feel. "
            f"Style: sleek SaaS product illustration, dark mode UI, subtle card shadows, 8K detail."
        )

    elif "timeline" in layout.lower() or "roadmap" in layout.lower() or "milestone" in layout.lower():
        # TIMELINE SLIDE — strategic, forward-looking
        prompt = (
            f"A dark navy background ({bg_color}) with a horizontal timeline layout. "
            f"Three milestone nodes connected by bold {accent} arrows forming a left-to-right flow. "
            f"Each node is a rounded dark card with a small chip or relevant icon at the top, "
            f"a white headline label (e.g., 'Today', 'Soon', 'Later'), and a short description in light gray below. "
        )
        if bullets:
            for i, b in enumerate(bullets[:3]):
                prompt += f"Node {i+1} reads: '{b}'. "
        prompt += (
            f"The nodes are connected by glowing {accent} arrow lines with circular connector dots. "
            f"The mood is strategic, optimistic, and empowering — a clear narrative progression for developers. "
            f"Style: clean data visualization aesthetic, dark mode UI, subtle glow effects on connectors, modern infographic."
        )

    elif "india" in topic.lower() or "indian" in str(key_msg).lower() or "india" in str(headline).lower():
        # INDIA-SPECIFIC SLIDE — tricolor accent, globe/map, empowering
        prompt = (
            f"A dark navy background ({bg_color}) with an Indian tricolor accent bar "
            f"(saffron #FF9933, white #FFFFFF, green #138808) at the very top edge. "
            f"A large globe or map icon centered with connection lines radiating outward in {accent}. "
            f"Three bullet points displayed in a dark card panel below, each with relevant emojis (e.g., rupee, chip, rocket) "
            f"in {accent} or {highlight} color. "
        )
        if headline:
            prompt += f"Bold white headline '{headline}' placed above the globe. "
        prompt += (
            f"The mood is forward-looking, empowering, and patriotic — focused on global opportunity for Indian developers. "
            f"Style: sleek SaaS product illustration, dark mode aesthetic, subtle glow effects, modern editorial design."
        )

    else:
        # GENERIC VALUE SLIDE — icon top, bullets, clean card layout
        prompt = (
            f"A dark navy background ({bg_color}) with a large topic icon (e.g., GPU, cloud, chip, brain) "
            f"at the top center, glowing with subtle {accent} light. "
            f"Bold white headline '{headline}' placed prominently below the icon. "
        )
        if subtext:
            prompt += f"A supporting line in light gray below the headline: '{subtext}'. "
        if bullets:
            prompt += (
                f"Three clean bullet points listed vertically in a dark card panel, "
                f"each with a small {highlight} arrow or dot marker, text in white/light gray. "
            )
        if objects:
            for obj in objects[:3]:
                prompt += f"{obj}. "
        if "supply" in topic.lower() or "cost" in topic.lower() or "trend" in topic.lower():
            prompt += (
                f"A horizontal trend arrow graphic at the bottom showing progression "
                f"(e.g., 'More Supply -> Lower Costs') in white text with {highlight} arrow accents. "
            )
        prompt += (
            f"The mood is optimistic, forward-looking, and informative — clean data-visualization aesthetic. "
            f"Style: sleek SaaS product illustration, dark mode UI, subtle card shadows, modern infographic design."
        )

    # Append visual story and scene description if available
    if visual_story:
        prompt += f" Visual story: {visual_story}"
    if scene:
        prompt += f" Scene composition: {scene}"
    if lighting:
        prompt += f" Lighting: {lighting}"
    if design_notes:
        prompt += f" Design notes: {design_notes}"

    # Final quality/style tag
    prompt += (
        " High-quality render, consistent dark-tech editorial style across all slides, "
        "no photorealistic human figures, no text rendered as actual readable words in the image — "
        "text described as placeholder design elements only."
    )

    return prompt


def generate_image_prompts(content: dict, theme: dict) -> tuple[dict, str]:
    """
    v5: Rich, detailed slide-specific image prompts for AI image generators.
    Each slide gets a complete, copy-paste-ready prompt with exact layout,
    colors, icons, typography, and mood. Produces consistent dark-tech
    editorial PNGs matching the uploaded reference style.
    """
    ctype = content.get("content_type", "")
    topic = content.get("topic", theme["theme"])
    slides = content.get("slides", [])
    theme_color = theme.get("color", "#6366f1")
    theme_icon = theme.get("icon", "💡")

    # ── Build rich per-slide prompts ──
    slide_prompts = []
    individual_prompts = {}

    if ctype == "carousel" and slides:
        for s in slides:
            sn = s.get("slide_no", "?")
            stype = s.get("type", "value")
            headline = s.get("headline", "")
            bullets = s.get("bullets", [])
            key_msg = s.get("key_message", "")

            # Build the rich detailed prompt
            rich_prompt = _build_slide_prompt(s, topic, theme_color)

            # Also build a compact summary block for the unified prompt
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
            lines.append(f"Image Prompt: {rich_prompt}")

            slide_prompts.append("\n".join(lines))
            individual_prompts[f"slide_{sn}"] = rich_prompt

    elif ctype == "reel":
        thumbnail_text = content.get("thumbnail_text", "")
        hook1 = content.get("hook1", "")
        hook2 = content.get("hook2", "")

        rich_prompt = (
            f"A dark navy background (#1a1a2e) with a dramatic {theme_color} accent glow. "
            f"Bold white headline text '{thumbnail_text or topic}' in the upper third, "
            f"large sans-serif font (Montserrat Bold), 60-72pt. "
            f"An expressive 3D cartoon character upper body with shocked/curious face, "
            f"dramatic rim light from the left, dark vignette around edges. "
            f"Small {theme_color} particles or data nodes floating around. "
            f"Mood: urgent, attention-grabbing, scroll-stopping. "
            f"Style: 3D cartoon illustration, dark tech editorial, high contrast, no photorealism."
        )

        lines = ["THUMBNAIL: Reel Cover"]
        lines.append("Format: 9:16 vertical, 1080×1920")
        if thumbnail_text:
            lines.append(f"Text: {thumbnail_text}")
        if hook1:
            lines.append(f"Hook1: {hook1}")
        if hook2:
            lines.append(f"Hook2: {hook2}")
        lines.append(f"Image Prompt: {rich_prompt}")
        slide_prompts.append("\n".join(lines))
        individual_prompts["reel_thumbnail"] = rich_prompt

    # ── Unified master prompt ──
    if ctype == "carousel":
        unified_prompt = f"""CAROUSEL IMAGE PROMPT — {topic}
Format: 7 slides, 1:1 square (1080×1080), dark tech editorial
Theme: {theme['theme']} | Color: {theme_color} | Font: Montserrat Bold + Poppins
Palette: #1a1a2e (bg), {theme_color} (accent), #ffffff (text), #10b981 (highlight), #fbbf24 (CTA)
Rules: 48px padding, bold white headlines 48-60pt, body 18-24pt light gray, accent glow behind icon, consistent style across all slides.

Generate ONE slide at a time for consistency. Each prompt below is complete and copy-paste ready.

{"\n\n".join(slide_prompts)}

GENERATION TIPS:
- Use DALL-E 3 or Ideogram for best text-in-image results
- For Midjourney/Flux, add text in Canva after generation
- Generate slides 1-6 first (dark theme), then slide 7 (bright CTA) last
- Keep aspect ratio exactly 1:1 (1080x1080) for all slides
- Export as PNG with transparent text layers if possible"""

    else:  # reel
        unified_prompt = f"""REEL THUMBNAIL PROMPT — {topic}
Format: 9:16 vertical (1080×1920), dark tech editorial
Theme: {theme['theme']} | Color: {theme_color}
Palette: #1a1a2e (bg), {theme_color} (accent), #ffffff (text), #f59e0b (urgency)
Rules: Headline max 5 words, 60-72pt bold white, character upper body expressive face, dramatic rim light, dark vignette, text in upper third.

{slide_prompts[0] if slide_prompts else "No prompt generated."}

Paste into DALL-E/Midjourney. Ask for edits like "make character more shocked" if needed."""

    result = {
        "unified_prompt": unified_prompt,
        "google_flow_prompt": unified_prompt,
        "ideogram_prompt": unified_prompt,
        "dalle_prompt": unified_prompt,
        "canva_instructions": unified_prompt,
        "color_palette": [theme_color, "#1a1a2e", "#ffffff", "#10b981", "#fbbf24"],
        "thumbnail_tip": f"Use {theme_color} accent on dark navy with bold headline to stop scroll",
        "text_overlay": (slides[0].get("headline", topic) if slides and ctype == "carousel" else content.get("thumbnail_text", topic))[:30],
        "slide_prompts": slide_prompts,
        "individual_prompts": individual_prompts,
        "recommended_tool": "DALL-E 3 (best text + consistency) → Ideogram (fast text) → Midjourney/Flux (aesthetic) → Canva (text assembly + export PNG)",
    }

    return result, "v5-rich-slide-prompts"




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