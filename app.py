"""
app.py — ContentBot Agent  |  streamlit run app.py
100% free: OpenRouter free models + manual Perplexity prompts + image prompts
FIXED: Render functions defined before use, st.stop() replaced, better flow
"""
import streamlit as st

st.set_page_config(
    page_title="ContentBot Agent 🚀",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

import datetime, json
from config import (
    get_today_cycle, get_state, advance_day, CONTENT_CYCLE,
    REVIEW_FILE, ENGAGEMENT_FILE, INSIGHTS_FILE, APPROVED_FILE, STATE_FILE,
    OPENROUTER_KEY, IG_TOKEN, IG_ACCOUNT_ID, CREATOR_HANDLE,
    load_json, save_json, append_json_list,
)

# ── Start scheduler silently ──────────────────────────────────────────────────
try:
    from utils.scheduler import start_scheduler
    start_scheduler()
except Exception:
    pass

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background:#0f0f13;}
[data-testid="stSidebar"]{background:#13131a;border-right:1px solid #1e1e2e;}
[data-testid="stSidebar"] *{color:#e2e8f0 !important;}
div[data-testid="metric-container"]{background:#1e1e2e;border:1px solid #2e2e3e;border-radius:12px;padding:14px !important;}
h1,h2,h3{color:#a5b4fc !important;}
.stButton>button{background:linear-gradient(135deg,#4f46e5,#7c3aed)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;}
[data-baseweb="tab-list"]{background:#13131a!important;border-radius:10px;}
[data-baseweb="tab"]{color:#94a3b8!important;}
[aria-selected="true"]{color:#a5b4fc!important;}
input,textarea{background:#1e1e2e!important;color:#e2e8f0!important;border:1px solid #2e2e3e!important;}
[data-testid="stExpander"]{background:#1e1e2e!important;border:1px solid #2e2e3e!important;border-radius:12px!important;}
[data-baseweb="select"]>div{background:#1e1e2e!important;border-color:#2e2e3e!important;}
code{background:#1e1e2e!important;color:#a5b4fc!important;}
.stTextArea textarea{font-family:monospace;font-size:13px;}
</style>""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────────────
theme         = get_today_cycle()
state         = get_state()
review_queue  = load_json(REVIEW_FILE, [])
engagement    = load_json(ENGAGEMENT_FILE, [])
insights      = load_json(INSIGHTS_FILE, {})
approved      = load_json(APPROVED_FILE, [])
pending       = [r for r in review_queue if r.get("status") == "pending_review"]

# ═══════════════════════════════════════════════════════════════════════════════
# RENDER HELPERS — DEFINED BEFORE ANY TAB USES THEM
# ═══════════════════════════════════════════════════════════════════════════════

def _render_content(g: dict, key_prefix: str = ""):
    """Route to correct renderer based on content type.
    key_prefix: unique prefix to avoid duplicate Streamlit keys when rendering same content in multiple places (e.g. Review tab + Dashboard)."""
    ctype = g.get("content_type", "")
    if ctype == "reel":
        _render_reel(g, key_prefix)
    elif ctype == "carousel":
        _render_carousel(g, key_prefix)


def _render_reel(g: dict, key_prefix: str = ""):
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("#### 🪝 Script")

        def hook_box(label, text, color):
            st.markdown(f"""
            <div style='background:{color}15;border:1px solid {color}40;border-radius:10px;padding:12px;margin-bottom:8px'>
              <div style='color:{color};font-size:11px;font-weight:700;margin-bottom:4px'>{label}</div>
              <div style='color:#e2e8f0;font-size:14px'>{text}</div>
            </div>""", unsafe_allow_html=True)

        hook_box("🪝 HOOK 1",        g.get("hook1",""),        "#f59e0b")
        hook_box("🪝 HOOK 2",        g.get("hook2",""),        "#f59e0b")
        hook_box("🎥 VISUAL HOOK",   g.get("visual_hook",""),  "#0ea5e9")

        st.markdown("**💎 Value Points**")
        for i, pt in enumerate(g.get("value_points", []), 1):
            st.markdown(f"**{i}.** {pt}")

        st.markdown(f"""
        <div style='background:#ec489915;border:1px solid #ec489940;border-radius:10px;padding:12px;margin-top:8px'>
          <div style='color:#ec4899;font-size:11px;font-weight:700'>📣 CTA</div>
          <div style='color:#e2e8f0'>{g.get("cta","")}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("#### 📱 Post Details")
        st.markdown(f"**📝 Caption:** {g.get('caption_english','')}")
        st.markdown(f"**🎵 Audio:** {g.get('audio_mood','')}")
        st.markdown(f"**💡 Audio tip:** {g.get('trending_audio_tip','')}")
        st.markdown(f"**⏰ Post time:** `{g.get('post_time','')}`")
        st.markdown(f"**⏱ Duration:** {g.get('estimated_duration','')}")
        st.markdown(f"**🖼 Thumbnail:** `{g.get('thumbnail_text','')}`")

        if g.get("hashtags"):
            tags = " ".join(
                f"<span style='background:#1e1e2e;border:1px solid #2e2e3e;border-radius:5px;padding:2px 7px;font-size:11px;color:#6366f1'>{h}</span>"
                for h in g["hashtags"]
            )
            st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:5px;margin-top:6px'>{tags}</div>", unsafe_allow_html=True)

        if g.get("viral_tip"):
            st.markdown(f"""
            <div style='background:#4f46e515;border:1px solid #4f46e540;border-radius:10px;padding:12px;margin-top:10px'>
              <div style='color:#6366f1;font-size:11px;font-weight:700'>🚀 Viral Tip</div>
              <div style='color:#a5b4fc;font-size:13px'>{g["viral_tip"]}</div>
            </div>""", unsafe_allow_html=True)


def _render_carousel(g: dict, key_prefix: str = ""):
    slides = g.get("slides", [])
    if slides:
        st.markdown("#### 🖼 Slides")
        slide_tabs = st.tabs([f"S{s.get('slide_no',i+1)}" for i, s in enumerate(slides)])
        type_colors = {"title_hook": "#6366f1", "value": "#10b981", "cta": "#ec4899"}
        for i, (slide, stab) in enumerate(zip(slides, slide_tabs)):
            with stab:
                stype = slide.get("type","value")
                color = type_colors.get(stype, "#94a3b8")

                # Slide header card
                st.markdown(f"""
                <div style='background:#1e1e2e;border:1px solid {color}40;border-radius:12px;padding:18px;margin-bottom:12px'>
                  <div style='color:{color};font-size:10px;font-weight:700;margin-bottom:6px'>SLIDE {slide.get("slide_no",i+1)} · {stype.upper().replace("_"," ")}</div>
                  <div style='color:#e2e8f0;font-size:17px;font-weight:700;margin-bottom:8px'>{slide.get("headline","")}</div>
                """, unsafe_allow_html=True)

                if slide.get("subtext"):
                    st.markdown(f"<div style='color:#94a3b8;font-style:italic;margin-bottom:10px'>{slide['subtext']}</div>", unsafe_allow_html=True)

                if slide.get("bullets"):
                    for b in slide["bullets"]:
                        st.markdown(f"<div style='color:#e2e8f0;margin:4px 0'>• {b}</div>", unsafe_allow_html=True)

                if slide.get("cta_text"):
                    st.markdown(f"<div style='color:#a5b4fc;font-weight:600;margin:8px 0'>{slide['cta_text']}</div>", unsafe_allow_html=True)
                if slide.get("save_nudge"):
                    st.markdown(f"<div style='color:#fbbf24;font-style:italic;margin:4px 0'>{slide['save_nudge']}</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # ── Rich visual details (v2) ──
                if slide.get("key_message") or slide.get("developer_takeaway"):
                    with st.expander("📋 Content Details", expanded=False):
                        if slide.get("key_message"):
                            st.markdown(f"**💡 Key Message:** {slide['key_message']}")
                        if slide.get("developer_takeaway"):
                            st.markdown(f"**🎯 Developer Takeaway:** {slide['developer_takeaway']}")
                        if slide.get("facts"):
                            st.markdown("**📊 Facts:**")
                            for f in slide["facts"]:
                                st.markdown(f"• {f}")

                if slide.get("visual_story") or slide.get("scene_description"):
                    with st.expander("🎬 Visual Story & Scene", expanded=False):
                        if slide.get("visual_story"):
                            st.markdown(f"**🎬 Visual Story:** {slide['visual_story']}")
                        if slide.get("scene_description"):
                            st.markdown(f"**🏞️ Scene Description:** {slide['scene_description']}")

                if slide.get("objects") or slide.get("icons"):
                    with st.expander("🎨 Objects & Icons", expanded=False):
                        if slide.get("objects"):
                            st.markdown("**📦 Objects:**")
                            for obj in slide["objects"]:
                                st.markdown(f"• {obj}")
                        if slide.get("icons"):
                            st.markdown("**🔣 Icons:**")
                            for icon in slide["icons"]:
                                st.markdown(f"• {icon}")

                if slide.get("layout") or slide.get("background") or slide.get("lighting"):
                    with st.expander("🖌 Design Specs", expanded=False):
                        cols = st.columns(2)
                        with cols[0]:
                            if slide.get("layout"): st.markdown(f"**📐 Layout:** {slide['layout']}")
                            if slide.get("background"): st.markdown(f"**🎨 Background:** {slide['background']}")
                            if slide.get("lighting"): st.markdown(f"**💡 Lighting:** {slide['lighting']}")
                            if slide.get("camera"): st.markdown(f"**📷 Camera:** {slide['camera']}")
                        with cols[1]:
                            if slide.get("palette"):
                                st.markdown("**🎨 Palette:**")
                                for p in slide["palette"]:
                                    st.markdown(f"<span style='display:inline-block;width:20px;height:20px;background:{p};border-radius:4px;margin-right:6px;border:1px solid #444'></span>`{p}`", unsafe_allow_html=True)
                            if slide.get("design_notes"):
                                st.markdown(f"**📝 Design Notes:** {slide['design_notes']}")

                # ── Ready-to-use image prompt ──
                if slide.get("image_prompt"):
                    with st.expander("🤖 Ready Image Prompt", expanded=True):
                        st.code(slide["image_prompt"], language=None)
                        if st.button("📋 Copy", key=f"copy_img_{key_prefix}_{slide.get('slide_no',i)}_{i}"):
                            st.toast("Prompt copied! Paste into your image generator.", icon="📋")

                # Legacy fallback
                elif slide.get("visual_direction"):
                    st.caption(f"🎨 Design: {slide['visual_direction']}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**📝 Caption:** {g.get('caption_english','')}")
        st.markdown(f"**⏰ Post time:** `{g.get('post_time','')}`")
        pal = g.get("design_palette", {})
        if pal:
            st.markdown(f"**🎨 Palette:** `{pal.get('primary_hex','')}` / `{pal.get('accent_hex','')}` · {pal.get('font_style','')}")
        if g.get("save_hook"):
            st.markdown(f"**💾 Save hook:** *{g['save_hook']}*")
    with c2:
        if g.get("hashtags"):
            tags = " ".join(
                f"<span style='background:#1e1e2e;border:1px solid #2e2e3e;border-radius:5px;padding:2px 7px;font-size:11px;color:#6366f1'>{h}</span>"
                for h in g["hashtags"]
            )
            st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:5px'>{tags}</div>", unsafe_allow_html=True)
        if g.get("viral_tip"):
            st.markdown(f"""
            <div style='background:#4f46e515;border:1px solid #4f46e540;border-radius:10px;padding:12px;margin-top:10px'>
              <div style='color:#6366f1;font-size:11px;font-weight:700'>🚀 Viral Tip</div>
              <div style='color:#a5b4fc;font-size:13px'>{g["viral_tip"]}</div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🚀 ContentBot Agent")
    st.caption("Free · OpenRouter · Tamil Tech Creator")
    st.divider()

    st.markdown(f"""
    <div style='background:{theme["color"]}22;border:1px solid {theme["color"]}55;
    border-radius:10px;padding:12px;'>
      <div style='font-size:26px'>{theme["icon"]}</div>
      <div style='color:{theme["color"]};font-weight:700;font-size:15px'>Day {state.get("current_day",1)}: {theme["theme"]}</div>
      <div style='color:#64748b;font-size:11px;margin-top:2px'>#{theme["tag"]}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown("**Status**")
    st.markdown(f"{'✅' if OPENROUTER_KEY else '❌ Add key in .env'} OpenRouter (free)")
    st.markdown(f"{'✅' if IG_TOKEN else '⚠️ Optional'} Instagram API")

    st.divider()
    c1, c2 = st.columns(2)
    with c1: st.metric("Review", len(pending))
    with c2: st.metric("Approved", len(approved))
    st.metric("Best Time", insights.get("best_time", "7:00 PM"))

    st.divider()
    if st.button("⏭ Next Day", use_container_width=True):
        advanced = advance_day()
        if advanced:
            st.rerun()
        else:
            st.toast("Already advanced today!", icon="⚠️")

    st.caption("Auto-advances at midnight IST\nAuto-generates at 6 AM IST")

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 Dashboard",
    "🔬 Research Prompts",
    "✨ Generate",
    "🔍 Review",
    "🖼 Image Prompts",
    "📈 Engagement",
    "📅 Schedule",
    "⚙️ Setup",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.header("📊 Dashboard")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Today", f"{theme['icon']} {theme['theme']}")
    c2.metric("Pending Review", len(pending))
    c3.metric("Posts Logged", len(engagement))
    c4.metric("Approved", len(approved))

    st.divider()

    # Cycle strip
    st.subheader("🗓 7-Day Cycle")
    cols = st.columns(7)
    today_idx = (state.get("current_day",1) - 1) % 7
    for i, c in enumerate(CONTENT_CYCLE):
        with cols[i]:
            is_today = (i == today_idx)
            border = f"border:2px solid {c['color']};" if is_today else "border:1px solid #2e2e3e;"
            today_tag = "<div style='font-size:9px;color:#fff;background:#4f46e5;border-radius:4px;padding:2px 4px;margin-top:3px'>TODAY</div>" if is_today else ""
            st.markdown(f"""
            <div style='background:{c["color"] + "22" if is_today else "#1e1e2e"};{border}
            border-radius:10px;padding:8px;text-align:center;'>
              <div style='font-size:20px'>{c["icon"]}</div>
              <div style='font-size:9px;color:#94a3b8'>Day {c["day"]}</div>
              <div style='font-size:10px;color:{c["color"]};font-weight:600;line-height:1.2'>{c["theme"]}</div>
              {today_tag}
            </div>""", unsafe_allow_html=True)

    st.divider()

    # Growth tips
    if insights.get("growth_tip"):
        st.subheader("🤖 AI Growth Strategy")
        a, b = st.columns(2)
        with a:
            st.success(f"✅ Keep: {insights.get('keep_doing','–')}")
            st.info(f"💡 This week: {insights.get('growth_tip','–')}")
        with b:
            st.error(f"❌ Stop: {insights.get('stop_doing','–')}")
            st.warning(f"🎯 Goal: {insights.get('weekly_goal','–')}")
    else:
        st.info("📈 Log engagement data in the **Engagement** tab to unlock AI strategy updates.")

    # Pending items preview
    if pending:
        st.divider()
        st.subheader("🔔 Awaiting Your Review")
        for item in pending[:2]:
            ct = item.get("content_type","").upper()
            tp = item.get("topic", item.get("theme",""))
            model = item.get("model_used","")
            with st.expander(f"{'🎬' if ct=='REEL' else '🖼'} {ct} · {tp} · model: {model}"):
                if ct == "REEL":
                    st.markdown(f"**Hook 1:** {item.get('hook1','')}")
                    st.markdown(f"**Hook 2:** {item.get('hook2','')}")
                else:
                    s = item.get("slides", [{}])
                    st.markdown(f"**Slide 1:** {s[0].get('headline','') if s else ''}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESEARCH PROMPTS (Perplexity manual)
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.header("🔬 Research Prompts")
    st.markdown(
        "Since you have **Perplexity Pro**, copy the prompt below → paste in Perplexity → "
        "copy the result back here. The agent will use it to generate better, current content."
    )

    # Theme selector
    theme_options = [f"Day {c['day']}: {c['icon']} {c['theme']}" for c in CONTENT_CYCLE]
    sel = st.selectbox("Pick theme to research:", ["Today: " + f"{theme['icon']} {theme['theme']}"] + theme_options)
    if sel.startswith("Today"):
        research_theme = theme
    else:
        day_n = int(sel.split(":")[0].replace("Day ",""))
        research_theme = CONTENT_CYCLE[day_n - 1]

    st.divider()

    # The Perplexity prompt
    prompt_text = research_theme["perplexity_prompt"]
    st.subheader(f"📋 Perplexity Prompt for {research_theme['icon']} {research_theme['theme']}")

    st.markdown("""
    <div style='background:#1e3a5f;border:1px solid #0ea5e9;border-radius:10px;padding:4px 14px;margin-bottom:8px'>
      <span style='color:#0ea5e9;font-size:12px'>💡 How to use: Copy prompt → Open perplexity.ai → Paste → Copy result → Paste in the box below</span>
    </div>""", unsafe_allow_html=True)

    st.code(prompt_text, language=None)
    if st.button("📋 Copy Prompt", key="copy_research"):
        st.toast("Prompt shown above — select all text and copy!", icon="📋")

    st.divider()
    st.subheader("📥 Paste Perplexity Result Here")
    research_paste = st.text_area(
        "Paste Perplexity's response:",
        value=st.session_state.get("research_result", ""),
        height=250,
        placeholder="Paste the full Perplexity response here...",
        key="research_input"
    )

    col_r1, col_r2 = st.columns([1,2])
    with col_r1:
        if st.button("✅ Save Research", use_container_width=True):
            if research_paste.strip():
                st.session_state["research_result"] = research_paste
                st.session_state["research_theme_tag"] = research_theme["tag"]
                st.success("Saved! Now go to **Generate** tab.")
            else:
                st.warning("Paste the Perplexity result first.")
    with col_r2:
        if st.button("⚡ Skip — Generate without research", use_container_width=True):
            st.session_state["research_result"] = ""
            st.info("Will use OpenRouter model's own knowledge. Go to **Generate** tab.")

    # Show saved research
    if st.session_state.get("research_result"):
        st.divider()
        st.markdown("**Saved research (ready for generation):**")
        st.markdown(
            f"<div style='background:#1e1e2e;border-radius:10px;padding:14px;color:#cbd5e1;font-size:13px;max-height:200px;overflow-y:auto'>"
            f"{st.session_state['research_result'][:800]}{'...' if len(st.session_state['research_result'])>800 else ''}"
            f"</div>", unsafe_allow_html=True
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GENERATE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.header("✨ Generate Content")

    # Check OpenRouter key
    if not OPENROUTER_KEY:
        st.error("❌ OPENROUTER_API_KEY not set. Add it to your `.env` file then restart.")
        st.markdown("Get free key → [openrouter.ai](https://openrouter.ai) → Sign up → Dashboard → Keys → Create (no credit card needed)")
        st.markdown("""
        ```bash
        # Create .env file in project root:
        OPENROUTER_API_KEY=sk-or-v1-your-key-here
        ```
        """)
        # Don't use st.stop() — just disable the generate button
        can_generate = False
    else:
        can_generate = True

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        content_type = st.selectbox("Content Type",
            ["🎬 Reel Script (Tanglish, 60–90 sec)", "🖼 Carousel Post (English, 7 slides)"],
            disabled=not can_generate)
    with col_g2:
        custom_topic = st.text_input("Custom Topic (blank = today's theme)",
            placeholder=f"e.g. Top 5 VS Code Extensions",
            disabled=not can_generate)

    # Theme
    theme_options = [f"Day {c['day']}: {c['icon']} {c['theme']}" for c in CONTENT_CYCLE]
    sel_theme = st.selectbox("Theme", ["📍 Today's: " + f"{theme['icon']} {theme['theme']}"] + theme_options, disabled=not can_generate)
    if "📍 Today's" in sel_theme:
        gen_theme = theme
    else:
        d = int(sel_theme.split(":")[0].replace("Day ",""))
        gen_theme = CONTENT_CYCLE[d - 1]

    # Research
    research_text = st.session_state.get("research_result", "")
    if research_text:
        st.success(f"✅ Research loaded ({len(research_text)} chars). Will be used in generation.")
    else:
        st.info("ℹ️ No research loaded. Get better results by pasting Perplexity output in Research tab first.")

    st.divider()
    gen_btn = st.button("⚡ Generate Now", use_container_width=True, disabled=not can_generate)

    if gen_btn and can_generate:
        from utils.ai_engine import generate_reel_script, generate_carousel
        is_reel = "Reel" in content_type

        status_box = st.empty()
        status_box.info(f"⏳ Generating {'Tanglish reel script' if is_reel else 'English carousel'}... (using free OpenRouter model)")

        try:
            if is_reel:
                result, model_used = generate_reel_script(
                    gen_theme, research_text, custom_topic, engagement, insights)
            else:
                result, model_used = generate_carousel(
                    gen_theme, research_text, custom_topic, engagement, insights)

            result["status"]         = "pending_review"
            result["generated_at"]   = str(datetime.datetime.now())
            result["id"]             = f"{'reel' if is_reel else 'carousel'}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            result["auto_generated"] = False
            result["model_used"]     = model_used
            append_json_list(REVIEW_FILE, result)
            st.session_state["last_generated"] = result
            status_box.success(f"✅ Generated using `{model_used}` — added to Review Queue!")

        except Exception as e:
            status_box.error(f"❌ Failed: {e}")

    # Preview last generated
    g = st.session_state.get("last_generated")
    if g:
        st.divider()
        st.subheader(f"📋 Preview: {g.get('content_type','').upper()} · {g.get('topic', g.get('theme',''))}")
        model_tag = g.get("model_used","")
        st.caption(f"Generated by: `{model_tag}`")
        _render_content(g, key_prefix="gen_preview")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.header("🔍 Review Queue")
    st.caption("Check every piece before posting. Approve → ready to post. Reject → discard.")

    review_queue = load_json(REVIEW_FILE, [])
    status_filter = st.selectbox("Filter", ["pending_review", "approved", "rejected", "all"], key="review_filter")
    filtered = review_queue if status_filter == "all" else [r for r in review_queue if r.get("status") == status_filter]

    if not filtered:
        st.info(f"No content with status: **{status_filter}**")
    else:
        for idx, item in enumerate(filtered):
            ct     = item.get("content_type","")
            topic  = item.get("topic", item.get("theme",""))
            status = item.get("status","pending_review")
            iid    = item.get("id", str(idx))
            model  = item.get("model_used","")
            gen_at = item.get("generated_at","")[:16]

            sc = {"pending_review":"#f59e0b","approved":"#10b981","rejected":"#ef4444"}.get(status,"#94a3b8")
            label = "🎬 Reel" if ct=="reel" else "🖼 Carousel"
            auto  = "🤖 Auto" if item.get("auto_generated") else "✍️ Manual"

            with st.expander(f"{label} · {topic} · {gen_at} · {auto}"):
                st.markdown(
                    f"<span style='background:{sc}22;color:{sc};border:1px solid {sc}44;"
                    f"border-radius:12px;padding:3px 12px;font-size:12px'>{status}</span>"
                    f"  <span style='color:#64748b;font-size:12px'>model: {model}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown("")
                _render_content(item, key_prefix=f"review_{iid}")

                if status == "pending_review":
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅ Approve", key=f"ap_{iid}"):
                            for r in review_queue:
                                if r.get("id") == iid:
                                    r["status"] = "approved"
                                    r["reviewed_at"] = str(datetime.datetime.now())
                                    append_json_list(APPROVED_FILE, r)
                            save_json(REVIEW_FILE, review_queue)
                            st.rerun()
                    with b2:
                        if st.button("❌ Reject", key=f"rj_{iid}"):
                            for r in review_queue:
                                if r.get("id") == iid:
                                    r["status"] = "rejected"
                            save_json(REVIEW_FILE, review_queue)
                            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — IMAGE PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.header("🖼 Image Prompts")
    st.markdown(
        "Generate one unified, copy-paste-ready prompt for **Google Flow** (Imagen 3), "
        "**Ideogram**, **Canva AI**, or **ChatGPT DALL-E**. Paste the entire prompt into any AI image tool."
    )

    # Pick content to generate image for
    all_content = load_json(REVIEW_FILE, []) + load_json(APPROVED_FILE, [])
    if not all_content:
        st.info("Generate some content first, then come here to get image prompts.")
    else:
        # Build options with a clear, readable label for each piece of content
        options = {}
        for c in all_content[:15]:
            ctype   = c.get('content_type','').upper()
            topic   = c.get('topic', c.get('theme',''))
            gen_at  = c.get('generated_at','')[:10]
            # Try to get a title / headline for carousels, or thumbnail text for reels
            title = ""
            if ctype == 'CAROUSEL':
                slides = c.get('slides', [])
                if slides:
                    title = slides[0].get('headline', '')
            elif ctype == 'REEL':
                title = c.get('thumbnail_text', '')
            # Build the dropdown label: include the title if we found one
            label = f"{ctype} · {topic}"
            if title:
                label += f" · '{title}'"
            label += f" · {gen_at}"
            options[label] = c

        sel_content_label = st.selectbox("Pick content to create image for:", list(options.keys()))
        sel_content = options[sel_content_label]

        # Theme
        sel_theme_tag = sel_content.get("theme","")
        img_theme = next((c for c in CONTENT_CYCLE if c["theme"] == sel_theme_tag), theme)

        if st.button("🎨 Generate Image Prompt", use_container_width=True):
            from utils.ai_engine import generate_image_prompts
            with st.spinner("Generating unified image prompt..."):
                try:
                    img_data, model = generate_image_prompts(sel_content, img_theme)
                    st.session_state["img_prompts"] = img_data
                    st.success(f"✅ Done (model: `{model}`)")
                except Exception as e:
                    st.error(f"❌ {e}")

        img = st.session_state.get("img_prompts")
        if img:
            st.divider()

            # ── Recommended Tool Banner ──
            st.markdown(f"""
            <div style='background: #1e1e2e; border: 1px solid #6366f1; border-radius: 12px; padding: 16px; margin-bottom: 20px;'>
              <div style='color: #a5b4fc; font-weight: 700; font-size: 16px; margin-bottom: 8px;'>🎯 Recommended Tool Chain</div>
              <div style='color: #e2e8f0; font-size: 13px; line-height: 1.6;'>
                <b>1. ChatGPT/DALL-E (Primary)</b> — Best text rendering, can edit via chat. Free: 10 images/day.<br>
                <b>2. Google Flow/Gemini (Backup)</b> — Fastest (3-5 sec), 20 free/day. Best for backgrounds.<br>
                <b>3. Canva AI (Assembly)</b> — Import AI backgrounds, add perfect text overlays with Montserrat Bold.
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Unified Prompt Display ──
            st.subheader("📋 Unified Image Generation Prompt")
            st.caption("Copy this ENTIRE prompt and paste into ChatGPT, Google Flow, Ideogram, or DALL-E")

            unified = img.get("unified_prompt", "")

            # Display in a clean code block with full width
            st.code(unified, language=None, wrap_lines=True)

            col_copy, col_info = st.columns([1, 3])
            with col_copy:
                if st.button("📋 Copy Full Prompt", use_container_width=True, key="copy_unified"):
                    st.toast("Full prompt copied! Paste into your AI image generator.", icon="📋")
            with col_info:
                st.caption("💡 Tip: In ChatGPT, paste this then say 'Generate Slide 1' → 'Now Slide 2' etc. for context-aware generation.")

            st.divider()

            # ── Color Palette & Quick Info ──
            col_i1, col_i2, col_i3 = st.columns(3)
            with col_i1:
                st.markdown("**🎨 Color Palette**")
                colors = img.get("color_palette", [])
                for hex_c in colors:
                    st.markdown(
                        f"<div style='background:{hex_c};width:40px;height:40px;border-radius:8px;display:inline-block;margin:4px;border:1px solid #2e2e3e'></div> <code>{hex_c}</code>",
                        unsafe_allow_html=True
                    )
            with col_i2:
                st.markdown("**📝 Text Overlay**")
                txt = img.get("text_overlay","")
                st.markdown(
                    f"<div style='background:#1e1e2e;border-radius:8px;padding:12px;font-size:16px;font-weight:700;color:#e2e8f0;word-break:break-word;'>{txt}</div>",
                    unsafe_allow_html=True
                )
            with col_i3:
                st.markdown("**💡 Pro Tips**")
                st.markdown(f"<div style='font-size:12px;color:#94a3b8;line-height:1.5;'>{img.get('thumbnail_tip','')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:11px;color:#6366f1;margin-top:8px;'>Recommended: {img.get('recommended_tool','')}</div>", unsafe_allow_html=True)

            # ── Per-Slide Breakdown (collapsible) ──
            slide_prompts = img.get("slide_prompts", [])
            if slide_prompts:
                st.divider()
                with st.expander("📑 View Per-Slide Details (for reference)", expanded=False):
                    st.caption("Individual slide content breakdown — use as reference when generating")
                    for i, sp in enumerate(slide_prompts, 1):
                        st.markdown(f"**Slide {i}**")
                        st.code(sp, language=None, wrap_lines=True)
                        st.markdown("---")

# TAB 5 — ENGAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.header("📈 Engagement Tracker")
    st.caption("Log post performance after 24h. AI analyses patterns and updates your strategy automatically.")

    # IG auto-fetch
    if IG_TOKEN and IG_ACCOUNT_ID:
        if st.button("📲 Auto-fetch from Instagram API"):
            from utils.ai_engine import fetch_ig_insights
            with st.spinner("Fetching..."):
                ig = fetch_ig_insights(IG_TOKEN, IG_ACCOUNT_ID)
            if ig.get("error"):
                st.error(ig["error"])
            else:
                a = ig.get("account",{})
                st.success(f"@{a.get('username','')} · {a.get('followers_count',0)} followers · {a.get('media_count',0)} posts")
    else:
        st.info("💡 Add Instagram API credentials in `.env` to auto-fetch metrics. (Optional — manual logging works fine)")

    st.divider()
    st.subheader("📝 Log Post Performance")

    with st.form("eng_form", clear_on_submit=True):
        fc1, fc2 = st.columns(2)
        with fc1:
            log_theme   = st.selectbox("Theme", [f"Day {c['day']}: {c['icon']} {c['theme']}" for c in CONTENT_CYCLE])
            log_type    = st.selectbox("Type", ["Reel", "Carousel", "Story"])
            log_views   = st.number_input("👁 Views",    min_value=0, value=0)
            log_likes   = st.number_input("❤️ Likes",   min_value=0, value=0)
        with fc2:
            log_comments= st.number_input("💬 Comments", min_value=0, value=0)
            log_shares  = st.number_input("↗️ Shares",   min_value=0, value=0)
            log_saves   = st.number_input("💾 Saves",    min_value=0, value=0)
            log_date    = st.date_input("Date", value=datetime.date.today())
        log_topic = st.text_input("Topic/Title (optional)")
        submitted = st.form_submit_button("📊 Log & Analyse", use_container_width=True)

    if submitted:
        theme_name = log_theme.split(": ",1)[1].split(" ",1)[1]
        entry = {
            "date": str(log_date), "theme": theme_name, "type": log_type,
            "topic": log_topic, "views": log_views, "likes": log_likes,
            "comments": log_comments, "shares": log_shares, "saves": log_saves,
            "engagement_score": log_likes + log_comments*3 + log_shares*5 + log_saves*4,
        }
        append_json_list(ENGAGEMENT_FILE, entry)

        with st.spinner("AI analysing your data..."):
            from utils.ai_engine import analyse_engagement
            all_logs = load_json(ENGAGEMENT_FILE, [])
            new_ins, model = analyse_engagement(all_logs, load_json(INSIGHTS_FILE,{}))
            save_json(INSIGHTS_FILE, new_ins)

        st.success(f"✅ Logged & strategy updated (model: `{model}`)!")
        st.balloons()
        st.rerun()

    # History
    eng_log = load_json(ENGAGEMENT_FILE, [])
    if eng_log:
        st.divider()
        st.subheader("📊 History")
        import pandas as pd
        df = pd.DataFrame(eng_log[:20])
        cols = [c for c in ["date","theme","type","views","likes","comments","shares","saves","engagement_score"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)

    # Insights
    ins = load_json(INSIGHTS_FILE, {})
    if ins and not ins.get("error"):
        st.divider()
        st.subheader("🤖 AI Strategy")
        i1, i2, i3 = st.columns(3)
        with i1:
            st.metric("Best Time", ins.get("best_time","–"))
            st.metric("Avg Views", ins.get("avg_views","–"))
            st.metric("Eng Rate",  ins.get("engagement_rate","–"))
        with i2:
            tops = ins.get("top_themes",[])
            st.markdown(f"**🔥 Top themes:** {', '.join(tops) if tops else '–'}")
            st.markdown(f"**📅 Best days:** {', '.join(ins.get('best_days',[])) or '–'}")
            st.markdown(f"**📊 Content mix:** {ins.get('content_mix','–')}")
        with i3:
            st.success(f"**Growth:** {ins.get('growth_tip','–')}")
            st.error(f"**Stop:** {ins.get('stop_doing','–')}")
            st.info(f"**Mix:** {ins.get('content_mix','–')}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.header("📅 Schedule & Blueprint")

    ins = load_json(INSIGHTS_FILE, {})
    best_time = ins.get("best_time","7:00 PM")
    st.markdown(f"**Optimal post time (AI-updated):** `{best_time}` IST")
    st.divider()

    for c in CONTENT_CYCLE:
        is_today = (c["day"] == state.get("current_day",1))
        today_badge = " 🟢 **TODAY**" if is_today else ""
        with st.expander(f"{c['icon']} Day {c['day']} · {c['theme']}{today_badge}"):
            st.markdown(f"""
            <div style='border-left:3px solid {c["color"]};padding-left:14px'>
              <b style='color:{c["color"]}'>Post angle:</b> {c["post_angle"]}<br>
              <b style='color:{c["color"]}'>Reel hook style:</b> {c["reel_hook"]}<br>
              <b style='color:{c["color"]}'>Image style:</b> {c["image_style"]}<br>
              <b style='color:{c["color"]}'>Best post time:</b> {best_time} IST
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("📈 0 → 1K Blueprint")
    for title, tip in [
        ("Week 1 — Consistency", "Post every day. Reel + Carousel. Focus entirely on your hook (first line). Reply to every comment within 1 hour of posting."),
        ("Week 2 — Find the winner", "Check which theme got highest saves. Double down on that. Start polls/questions in Stories to push IG algorithm."),
        ("Week 3 — Amplify", "Boost your best reel ₹100–₹200 (Reels Boost, not Feed Boost). Target: India, 18–30, interests = technology/programming."),
        ("Week 4 — Authority + viral", "Post one big Myth vs Fact carousel — highest save rate in tech. Go Live once (even 10 min). Use Collab post with another creator."),
    ]:
        with st.expander(title):
            st.markdown(tip)

    st.divider()
    st.subheader("⚙️ Automation Status")
    try:
        from utils.scheduler import get_next_runs, is_running
        if is_running():
            st.success("✅ Scheduler running")
            for j in get_next_runs():
                st.markdown(f"- `{j['id']}` → next: `{j['next_run']}`")
        else:
            st.warning("Scheduler not running. Restart the app.")
    except Exception as e:
        st.caption(f"Scheduler unavailable: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — SETUP
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.header("⚙️ Setup Guide")

    st.subheader("1️⃣ Get Your Free OpenRouter API Key")
    st.markdown("""
1. Go to **[openrouter.ai](https://openrouter.ai)** → Sign up (no credit card)
2. Dashboard → **Keys** → **Create Key**
3. Copy the key → paste in `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
CREATOR_HANDLE=your_instagram_handle
```
4. Restart: `streamlit run app.py`

**Free limits:** 200 requests/day, 20/min. More than enough for daily content.
""")

    st.subheader("2️⃣ Using Perplexity Pro for Research")
    st.markdown("""
You already have Perplexity Pro — no API needed.

**Workflow:**
1. Go to **Research Prompts** tab → pick today's theme
2. Copy the auto-generated prompt
3. Paste in **[perplexity.ai](https://perplexity.ai)** → get result
4. Paste result back in Research tab → Save
5. Go to **Generate** tab → your content will use real, current info
""")

    st.subheader("3️⃣ Image Generation (All Free)")
    st.markdown("""
After generating content → go to **Image Prompts** tab for ready-to-paste prompts.

| Tool | Best for | Link |
|------|----------|------|
| **Google Flow / ImageFX** | Photorealistic thumbnails | [labs.google/flow](https://labs.google/flow) |
| **Ideogram** | Text on image (best for carousels) | [ideogram.ai](https://ideogram.ai) |
| **Canva AI** | Quick branded designs | [canva.com](https://canva.com) |
| **ChatGPT DALL-E** | Creative/artistic thumbnails | ChatGPT Free |
""")

    st.subheader("4️⃣ Instagram API (Optional)")
    st.markdown("""
Optional — lets the app auto-fetch your post metrics instead of manual logging.

1. Go to [developers.facebook.com](https://developers.facebook.com) → Create App → Business
2. Add **Instagram Graph API** product
3. Connect your Instagram Professional account
4. Get long-lived access token + Business Account ID
5. Add to `.env`:
```
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_id
```
""")

    st.divider()
    st.subheader("🗑 Data Management")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Clear Review Queue"):
            save_json(REVIEW_FILE, [])
            st.success("Cleared.")
    with c2:
        if st.button("Clear Engagement"):
            save_json(ENGAGEMENT_FILE, [])
            save_json(INSIGHTS_FILE, {})
            st.success("Cleared.")
    with c3:
        if st.button("Clear Approved"):
            save_json(APPROVED_FILE, [])
            st.success("Cleared.")

    st.divider()
    st.subheader("📅 Day Control")
    d1, d2 = st.columns(2)
    with d1:
        cur = get_state().get("current_day",1)
        st.metric("Current Day", f"{cur} — {CONTENT_CYCLE[(cur-1)%7]['theme']}")
    with d2:
        manual = st.number_input("Jump to day", 1, 7, cur)
        if st.button("Set Day"):
            s = load_json(STATE_FILE, {"current_day":1})
            s["current_day"] = manual
            save_json(STATE_FILE, s)
            st.success(f"Set to Day {manual}")
            st.rerun()