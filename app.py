import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from tavily import TavilyClient
from agents import (
    AgentExecutionError,
    burnout_researcher_agent,
    fallback_habit_analysis,
    fallback_judge_result,
    fallback_recovery_plan,
    fallback_research_brief,
    habit_analyzer_agent,
    judge_agent,
    plan_writer_agent,
)

load_dotenv()

st.set_page_config(
    page_title="Sanctuary | Burnout Recovery Planner",
    page_icon="🌿",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --primary: #376847;
    --primary-container: #6B9E78;
    --primary-fixed: #B9EFC4;
    --secondary: #645E52;
    --secondary-container: #E8DFD0;
    --tertiary: #066A5F;
    --background: #FBFAF6;
    --surface-low: #F5F3F0;
    --surface-high: #EAE8E5;
    --surface-lowest: #FFFFFF;
    --on-surface: #1A2E1F;
    --on-surface-variant: #2E4A35;
    --outline-variant: #C1C9BF;
}

.stApp {
    background: var(--background) !important;
    font-family: 'Manrope', sans-serif !important;
    color: var(--on-surface) !important;
}

[data-testid="stSidebar"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }
.main .block-container {
    max-width: 100% !important;
    padding: 0 !important;
}

/* NAV */
.sanctuary-nav {
    position: fixed;
    top: 0;
    width: 100%;
    z-index: 999;
    background: rgba(249, 247, 244, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(193,201,191,0.15);
}

.sanctuary-brand {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.03em;
}

.sanctuary-nav-links {
    display: flex;
    gap: 2rem;
    align-items: center;
    font-size: 0.9rem;
    font-weight: 500;
}

.nav-active {
    color: var(--primary);
    font-weight: 700;
    border-bottom: 2px solid var(--primary);
    padding-bottom: 2px;
}

.nav-muted { color: var(--secondary); }

/* HERO */
.sanctuary-hero {
    padding: 7rem 2rem 5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(55,104,71,0.18) 0%, transparent 70%),
        radial-gradient(ellipse 50% 40% at 20% 30%, rgba(107,158,120,0.15) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 80% 20%, rgba(185,239,196,0.2) 0%, transparent 60%),
        linear-gradient(180deg, rgba(185,239,196,0.25) 0%, rgba(251,249,246,1) 55%);
    border-bottom: 1px solid rgba(107,158,120,0.12);
}

.hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: clamp(2.5rem, 6vw, 5rem);
    font-weight: 800;
    color: var(--on-surface);
    letter-spacing: -0.03em;
    line-height: 1.05;
    margin-bottom: 1.2rem;
}

.hero-subtitle {
    font-size: 1.15rem;
    color: var(--on-surface-variant);
    max-width: 38rem;
    margin: 0 auto 1.5rem;
    line-height: 1.7;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(55,104,71,0.08);
    border: 1px solid rgba(107,158,120,0.35);
    border-radius: 999px;
    padding: 0.65rem 1.2rem;
    font-size: 0.88rem;
    color: var(--primary);
    font-weight: 600;
    backdrop-filter: blur(8px);
}

/* INPUT SECTION */
.input-section {
    max-width: 1100px;
    margin: 0 auto;
    padding: 3rem 2rem;
}

.section-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    text-align: center;
    color: var(--on-surface);
    margin-bottom: 0.5rem;
}

.section-sub {
    text-align: center;
    color: var(--on-surface-variant);
    font-size: 0.95rem;
    margin-bottom: 2.5rem;
    line-height: 1.6;
}

.input-card {
    background: var(--surface-lowest);
    border-radius: 20px;
    padding: 1.6rem;
    box-shadow: 0 20px 40px rgba(27,28,26,0.05);
    margin-bottom: 1.2rem;
}

.input-card-label {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: var(--on-surface);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.input-note {
    font-size: 0.8rem;
    color: var(--on-surface-variant);
    margin-top: 0.6rem;
}

/* Streamlit textarea */
.stTextArea textarea {
    background: var(--surface-low) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 1rem !important;
    font-family: 'Manrope', sans-serif !important;
    font-size: 0.95rem !important;
    color: var(--on-surface) !important;
    min-height: 130px !important;
    resize: vertical !important;
    box-shadow: none !important;
}

.stTextArea textarea::placeholder {
    color: #1A2E1F !important;
    opacity: 0.7 !important;
}

.stTextArea textarea:focus {
    box-shadow: 0 0 0 2px rgba(107,158,120,0.3) !important;
    outline: none !important;
}

.stTextArea label {
    display: none !important;
}

/* CTA Button */
.stButton > button {
    width: 100% !important;
    min-height: 3.5rem !important;
    border-radius: 999px !important;
    border: none !important;
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-container) 100%) !important;
    color: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    box-shadow: 0 16px 32px rgba(55,104,71,0.2) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 20px 40px rgba(55,104,71,0.25) !important;
}

/* PROGRESS */
.progress-shell {
    max-width: 800px;
    margin: 0 auto 3rem;
    background: var(--surface-low);
    border-radius: 24px;
    padding: 2rem;
}

.progress-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 1rem;
}

.progress-label-text {
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--primary);
    margin-bottom: 0.3rem;
}

.progress-title-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--on-surface);
}

.progress-pct {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: var(--on-surface);
}

.progress-track {
    width: 100%;
    height: 10px;
    background: rgba(27,28,26,0.06);
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 1.2rem;
}

.progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--primary), var(--primary-container));
    transition: width 0.4s ease;
}

.progress-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
}

.progress-item {
    font-size: 0.88rem;
    color: var(--on-surface-variant);
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.progress-item.done { color: var(--primary); font-weight: 600; }

.log-box {
    background: rgba(255,255,255,0.7);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-top: 1rem;
    font-size: 0.88rem;
    color: var(--on-surface-variant);
    line-height: 1.8;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent !important;
    border-bottom: none !important;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 999px !important;
    height: 2.8rem !important;
    padding: 0 1.2rem !important;
    background: var(--surface-low) !important;
    border: none !important;
    color: var(--on-surface) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
}

.stTabs [aria-selected="true"] {
    background: var(--surface-lowest) !important;
    color: var(--primary) !important;
    box-shadow: 0 8px 20px rgba(27,28,26,0.07) !important;
}

.stTabs [data-baseweb="tab-panel"] {
    background: var(--surface-lowest) !important;
    border-radius: 20px !important;
    padding: 1.5rem !important;
    box-shadow: 0 20px 40px rgba(27,28,26,0.05) !important;
}

/* SCORE CARD */
.score-card {
    background: var(--surface-lowest);
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 24px 48px rgba(27,28,26,0.07);
    position: sticky;
    top: 5rem;
}

.score-kicker {
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--on-surface-variant);
    text-align: center;
    margin-bottom: 1rem;
}

.score-ring-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    margin-bottom: 0.75rem;
    height: 132px;
}

.score-ring-number {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: #1A2E1F;
    line-height: 1;
}

.score-match-label {
    text-align: center;
    font-weight: 700;
    color: var(--tertiary);
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

.metric-row { margin-bottom: 1rem; }

.metric-top {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    color: var(--on-surface);
    margin-bottom: 0.35rem;
}

.mini-bar {
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: var(--surface-high);
    overflow: hidden;
}

.mini-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: var(--primary-container);
}

.score-note {
    font-size: 0.88rem;
    color: var(--on-surface-variant);
    line-height: 1.6;
    margin-top: 0.5rem;
}

.score-divider {
    border: none;
    border-top: 1px solid rgba(193,201,191,0.15);
    margin: 1.25rem 0;
}

.blueprint-icon {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    background: rgba(107,158,120,0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
}

.blueprint-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--on-surface);
}

/* FOOTER */
.sanctuary-footer {
    background: var(--surface-high);
    padding: 3rem 2rem;
    text-align: center;
    margin-top: 4rem;
}

.footer-copy {
    color: var(--secondary);
    font-size: 0.82rem;
    line-height: 1.6;
    max-width: 36rem;
    margin: 0 auto 1rem;
    opacity: 0.8;
}

.footer-links {
    display: flex;
    justify-content: center;
    gap: 2rem;
    font-size: 0.82rem;
    color: var(--secondary);
}

.footer-links a {
    color: var(--primary);
    text-decoration: underline;
    opacity: 0.8;
}
</style>
""", unsafe_allow_html=True)

# ── NAV ───────────────────────────────────────────────────────────────────────
st.markdown("""
<nav class="sanctuary-nav">
    <div class="sanctuary-brand">Sanctuary</div>
    <div class="sanctuary-nav-links">
        <span class="nav-active">Planner</span>
        <span class="nav-muted">Resources</span>
        <span class="nav-muted">Community</span>
    </div>
</nav>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<section class="sanctuary-hero">
    <div style="
        position:absolute;top:4rem;left:10%;
        width:320px;height:320px;
        background:radial-gradient(circle, rgba(107,158,120,0.18) 0%, transparent 70%);
        border-radius:50%;pointer-events:none;">
    </div>
    <div style="
        position:absolute;top:2rem;right:8%;
        width:240px;height:240px;
        background:radial-gradient(circle, rgba(185,239,196,0.22) 0%, transparent 70%);
        border-radius:50%;pointer-events:none;">
    </div>
    <div style="position:relative;z-index:1;">
        <div style="
            display:inline-flex;align-items:center;gap:0.5rem;
            background:rgba(55,104,71,0.09);
            border:1px solid rgba(107,158,120,0.3);
            border-radius:999px;padding:0.4rem 1rem;
            font-size:0.8rem;font-weight:700;color:#376847;
            letter-spacing:0.08em;text-transform:uppercase;
            margin-bottom:1.2rem;">
            🌱 AI-Powered Recovery
        </div>
        <h1 class="hero-title">🌿 Burnout Recovery Planner</h1>
        <p class="hero-subtitle">
            Tell us about your situation. Our AI builds your personalized 21-day recovery plan.
        </p>
        <div class="hero-pill">
            ⏱ In the next 60 seconds, we'll create a realistic plan you can actually follow.
        </div>
    </div>
</section>
""", unsafe_allow_html=True)

# ── INPUT SECTION ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="input-section">
    <h2 class="section-title">Tell Us About Your Situation</h2>
    <p class="section-sub">
        The more real your description is, the better the planner can shape a recovery path
        that feels gentle, specific, and actually doable.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div class="input-card">
        <div class="input-card-label">💼 Work Situation</div>
    </div>
    """, unsafe_allow_html=True)
    work_situation = st.text_area(
        "work",
        placeholder="Describe your current role, hours, and workload... e.g. Engineering student with 10 hrs of classes and deadlines every week",
        height=140,
        label_visibility="collapsed"
    )
    st.markdown('<div class="input-note">💡 Mention if you are remote, in-office, or a student.</div>', unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="input-card">
        <div class="input-card-label">⚡ Stress Triggers</div>
    </div>
    """, unsafe_allow_html=True)
    stress_triggers = st.text_area(
        "stress",
        placeholder="What specifically is draining your energy? e.g. Constant deadlines, fear of failing, comparison with peers, poor sleep",
        height=140,
        label_visibility="collapsed"
    )
    st.markdown('<div class="input-note">💡 Examples: Meetings, lack of boundaries, or exam pressure.</div>', unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="input-card">
        <div class="input-card-label">🌙 Lifestyle</div>
    </div>
    """, unsafe_allow_html=True)
    lifestyle = st.text_area(
        "lifestyle",
        placeholder="Sleep patterns, exercise, and diet... e.g. Sedentary, 4-5 hrs sleep, skipping meals, excessive screen time",
        height=140,
        label_visibility="collapsed"
    )
    st.markdown('<div class="input-note">💡 How are you supporting your physical self today?</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    generate_btn = st.button("✨ Build My Recovery Plan", type="primary")

# ── PIPELINE ──────────────────────────────────────────────────────────────────
if generate_btn:
    if not work_situation or not stress_triggers or not lifestyle:
        st.warning("Please fill in all three fields before generating your plan.")
        st.stop()

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")

    if not tavily_key:
        st.error("TAVILY_API_KEY missing in .env file.")
        st.stop()

    user_profile = f"""Work Situation: {work_situation}
Stress Triggers: {stress_triggers}
Lifestyle: {lifestyle}"""

    client = genai.Client(api_key=gemini_key, vertexai=False) if gemini_key else None
    tavily_client = TavilyClient(api_key=tavily_key)

    logs = []
    fallback_messages = []
    progress_value = 10
    progress_placeholder = st.empty()

    def render_progress():
        steps = [
            ("🔍 Researching techniques", progress_value >= 35),
            ("⚡ Analyzing habits",        progress_value >= 60),
            ("📋 Writing your plan",       progress_value >= 82),
            ("⭐ Evaluating quality",      progress_value >= 100),
        ]
        items_html = "".join(
            f'<div class="progress-item {"done" if done else ""}">'
            f'{"✓" if done else "○"} {label}</div>'
            for label, done in steps
        )
        log_html = (
            f'<div class="log-box">{"<br>".join(logs[-6:])}</div>'
            if logs else ""
        )
        progress_placeholder.markdown(f"""
        <div class="progress-shell">
            <div class="progress-header">
                <div>
                    <div class="progress-label-text">Engine Processing</div>
                    <div class="progress-title-text">Assembling your sanctuary...</div>
                </div>
                <div class="progress-pct">{progress_value}%</div>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{progress_value}%"></div>
            </div>
            <div class="progress-grid">{items_html}</div>
            {log_html}
        </div>
        """, unsafe_allow_html=True)

    def log_step(msg):
        logs.append(f"✓ {msg}")
        render_progress()

    def record_fallback(message):
        if message not in fallback_messages:
            fallback_messages.append(message)

    render_progress()

    # Agent 1
    with st.spinner(""):
        if client is None:
            log_step("Researcher: Gemini unavailable — using Tavily fallback")
            research_brief = fallback_research_brief(tavily_client, user_profile)
            record_fallback("Researcher ran in fallback mode.")
        else:
            try:
                research_brief = burnout_researcher_agent(client, tavily_client, user_profile, log_step=log_step)
            except AgentExecutionError as e:
                log_step("Researcher: fallback mode")
                research_brief = fallback_research_brief(tavily_client, user_profile)
                record_fallback(e.user_message)
    progress_value = 35
    render_progress()

    # Agent 2
    with st.spinner(""):
        if client is None:
            log_step("Habit Analyzer: using built-in analysis")
            habit_analysis = fallback_habit_analysis(research_brief, user_profile)
            record_fallback("Habit Analyzer ran in fallback mode.")
        else:
            try:
                habit_analysis = habit_analyzer_agent(client, research_brief, user_profile, log_step=log_step)
            except AgentExecutionError as e:
                log_step("Habit Analyzer: fallback mode")
                habit_analysis = fallback_habit_analysis(research_brief, user_profile)
                record_fallback(e.user_message)
    progress_value = 60
    render_progress()

    # Agent 3
    with st.spinner(""):
        if client is None:
            log_step("Plan Writer: using built-in planner")
            recovery_plan = fallback_recovery_plan(research_brief, habit_analysis, user_profile)
            record_fallback("Plan Writer ran in fallback mode.")
        else:
            try:
                recovery_plan = plan_writer_agent(client, research_brief, habit_analysis, user_profile, log_step=log_step)
            except AgentExecutionError as e:
                log_step("Plan Writer: fallback mode")
                recovery_plan = fallback_recovery_plan(research_brief, habit_analysis, user_profile)
                record_fallback(e.user_message)
    progress_value = 82
    render_progress()

    # Agent 4
    with st.spinner(""):
        if client is None:
            log_step("Judge: using estimated rubric")
            judge_result = fallback_judge_result()
            record_fallback("Judge ran in fallback mode.")
        else:
            try:
                judge_result = judge_agent(client, user_profile, research_brief, recovery_plan, log_step=log_step)
            except AgentExecutionError as e:
                log_step("Judge: fallback mode")
                judge_result = fallback_judge_result()
                record_fallback(e.user_message)
    progress_value = 100
    render_progress()
    progress_placeholder.empty()

    # ── OUTPUT ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="max-width:1200px;margin:2rem auto;padding:0 2rem">
        <div style="display:flex;align-items:center;gap:0.85rem;margin-bottom:1.5rem">
            <div class="blueprint-icon">✅</div>
            <div class="blueprint-title">Your Recovery Blueprint</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    output_col, score_col = st.columns([1.9, 0.95], gap="large")

    with output_col:
        tabs = st.tabs(["🔍 Research Brief", "⚡ Habit Analysis", "📋 21-Day Plan", "⭐ Quality Review"])

        with tabs[0]:
            st.markdown(research_brief)

        with tabs[1]:
            st.markdown(habit_analysis)

        with tabs[2]:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#376847,#4a7f59);color:white;
                        border-radius:18px;padding:1.3rem;margin-bottom:1rem">
                <h3 style="color:white;font-family:'Plus Jakarta Sans',sans-serif;
                           font-size:1.2rem;margin-bottom:0.25rem">
                    The 21-Day Recovery Path
                </h3>
                <p style="color:rgba(255,255,255,0.8);font-size:0.88rem">
                    Phase 1: Foundation & Boundary Setting
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(recovery_plan)

        with tabs[3]:
            st.markdown(judge_result.get("summary", ""))
            st.markdown("---")
            labels = {
                "scientific_grounding": "Scientific Grounding",
                "personalization":      "Personalization",
                "practicality":         "Practicality",
                "progression":          "Progression",
                "compassionate_tone":   "Compassionate Tone",
            }
            for key, label in labels.items():
                data  = judge_result.get("scores", {}).get(key, {})
                score = float(data.get("score", 0))
                st.markdown(f"**{label}** — {score}/5")
                st.progress(min(max(score / 5, 0.0), 1.0))
                st.caption(data.get("reasoning", ""))

    with score_col:
        overall  = float(judge_result.get("overall_score", 0))
        pct      = min(int(round((overall / 5) * 100)), 100)
        match_label = (
            "Exceptional Match" if pct >= 85 else
            "Strong Match"      if pct >= 70 else
            "Emerging Match"
        )
        scores   = judge_result.get("scores", {})
        realism  = int((float(scores.get("practicality",         {}).get("score", 0)) / 5) * 100)
        science  = int((float(scores.get("scientific_grounding", {}).get("score", 0)) / 5) * 100)
        sustain  = int((float(scores.get("progression",          {}).get("score", 0)) / 5) * 100)
        offset_val = round(351.8 - (pct / 100) * 351.8, 1)
        top_strength    = judge_result.get("top_strength", "")
        top_improvement = judge_result.get("top_improvement", "")

        st.markdown(f"""
<div class="score-card">
    <div class="score-kicker">Plan Integrity Score</div>
    <div class="score-ring-wrapper">
        <svg width="132" height="132" viewBox="0 0 132 132"
             xmlns="http://www.w3.org/2000/svg"
             style="transform:rotate(-90deg)">
            <circle cx="66" cy="66" r="56" stroke="#EAE8E5"
                    stroke-width="8" fill="transparent"/>
            <circle cx="66" cy="66" r="56" stroke="#066A5F"
                    stroke-width="8" fill="transparent"
                    stroke-dasharray="351.8"
                    stroke-dashoffset="{offset_val}"
                    stroke-linecap="round"/>
        </svg>
        <div class="score-ring-number">{pct}</div>
    </div>
    <div class="score-match-label">{match_label}</div>
    <div class="metric-row">
        <div class="metric-top"><span>Realism</span><span>{realism}%</span></div>
        <div class="mini-bar">
            <div class="mini-bar-fill" style="width:{realism}%"></div>
        </div>
    </div>
    <div class="metric-row">
        <div class="metric-top"><span>Scientific Rigor</span><span>{science}%</span></div>
        <div class="mini-bar">
            <div class="mini-bar-fill" style="width:{science}%"></div>
        </div>
    </div>
    <div class="metric-row">
        <div class="metric-top"><span>Sustainability</span><span>{sustain}%</span></div>
        <div class="mini-bar">
            <div class="mini-bar-fill" style="width:{sustain}%"></div>
        </div>
    </div>
    <hr class="score-divider"/>
    <div class="score-note"><strong>Strength:</strong> {top_strength}</div>
    <div class="score-note" style="margin-top:0.75rem">
        <strong>Improvement:</strong> {top_improvement}
    </div>
</div>
""", unsafe_allow_html=True)



    st.success("🌿 Your personalized burnout recovery plan is ready!")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<footer class="sanctuary-footer">
    <p class="footer-copy">
        © 2024 Sanctuary Recovery. This planner is for informational purposes
        and does not replace professional medical advice.
    </p>
    <div class="footer-links">
        <a href="#">Privacy Policy</a>
        <span>Terms of Service</span>
        <span>Support</span>
    </div>
</footer>
""", unsafe_allow_html=True)