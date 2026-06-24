import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from core.orchestrator import run_pipeline
from chat.qa_agent import answer_question

load_dotenv()

st.set_page_config(
    page_title="Docsmith",
    page_icon="⚒️",
    layout="wide"
)

st.markdown("""
<style>

/* ── Sticky top bar ── */
.sticky-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: #0e1117;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding: 12px 0 10px 0;
    text-align: center;
}
.sticky-nav .brand {
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 2px;
}
.sticky-nav .sub {
    font-size: 11px;
    color: rgba(255,255,255,0.35);
    margin-bottom: 10px;
}
.mode-bar {
    position: fixed;
    top: 58px;
    left: 0;
    right: 0;
    z-index: 9998;
    background: #0e1117;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* ── Push all page content below the sticky nav ── */
.main-body {
    margin-top: 170px;
}

/* ── Hero boxes ── */
.hero-box {
    background: rgba(108,99,255,0.08);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
}
.advisor-box {
    background: rgba(29,158,117,0.08);
    border: 1px solid rgba(29,158,117,0.2);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
}
.hero-title {
    font-size: 17px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 14px;
}
.hero-steps {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}
.hero-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    flex: 1;
    min-width: 150px;
}
.step-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #6C63FF;
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
}
.step-num-green {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #1D9E75;
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
}
.step-text {
    font-size: 13px;
    color: rgba(255,255,255,0.7);
    line-height: 1.5;
}
.step-text b {
    color: #fff;
    display: block;
    margin-bottom: 3px;
    font-size: 13px;
}

/* ── Hide Streamlit default header ── */
header[data-testid="stHeader"] {
    height: 0 !important;
    visibility: hidden !important;
}
section[data-testid="stSidebar"] { display: none; }

/* ── Remove default top padding ── */
.block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem;
}

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════
# ADVISOR FUNCTION — defined first
# ════════════════════════════════════════
def _get_advisor_answer(question: str, history: list) -> str:
    system_prompt = """You are an expert API advisor for developers.
You have deep knowledge of all major APIs, SDKs, and developer tools.

You help developers with:
- Choosing the right API for their use case
- Comparing APIs on pricing, features, rate limits, ease of use
- Best practices for API authentication and security
- REST vs SDK integration recommendations
- Error handling strategies and retry logic
- Rate limiting and pagination patterns
- Webhook setup and event-driven architectures
- Popular APIs: Stripe, Razorpay, Twilio, SendGrid, GitHub, OpenAI,
  Google Maps, Firebase, AWS, Cloudinary, and many more

Be concise, practical, and always give a clear recommendation when asked.
Use bullet points or short comparison tables where it helps clarity.
Never give vague answers — always pick a winner when asked to compare."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": question})

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4,
        max_tokens=1024
    )
    return response.choices[0].message.content.strip()


# ── Session state ──
if "mode" not in st.session_state:
    st.session_state.mode = "helper"
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "index_data" not in st.session_state:
    st.session_state.index_data = None
if "advisor_history" not in st.session_state:
    st.session_state.advisor_history = []


# ── Sticky navbar HTML ──
st.markdown("""
<div class="sticky-nav">
    <div class="brand">⚒️ Docsmith</div>
    <div class="sub">Smart DevTool for API Integration</div>
</div>
""", unsafe_allow_html=True)

# ── Streamlit toggle buttons (rendered below sticky nav) ──
# These are inside the scrollable body but visually look like navbar tabs
st.markdown('<div class="main-body">', unsafe_allow_html=True)

# Center the buttons
nc1, nc2, nc3 = st.columns([3, 2, 3])
with nc2:
    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            "📄 API Doc Helper",
            use_container_width=True,
            type="primary" if st.session_state.mode == "helper" else "secondary"
        ):
            st.session_state.mode = "helper"
            st.rerun()
    with b2:
        if st.button(
            "💡 API Advisor",
            use_container_width=True,
            type="primary" if st.session_state.mode == "advisor" else "secondary"
        ):
            st.session_state.mode = "advisor"
            st.rerun()

st.markdown("<hr style='margin:14px 0 20px 0'>", unsafe_allow_html=True)


# ════════════════════════════════════════
# MODE 1 — API DOCUMENTATION HELPER
# ════════════════════════════════════════
if st.session_state.mode == "helper":

    st.markdown("""
    <div class="hero-box">
        <div class="hero-title">📄 API Documentation Helper</div>
        <div class="hero-steps">
            <div class="hero-step">
                <div class="step-num">1</div>
                <div class="step-text">
                    <b>Paste any API doc URL</b>
                    Enter the public documentation link of any REST API —
                    Stripe, GitHub, Razorpay, Twilio, and more
                </div>
            </div>
            <div class="hero-step">
                <div class="step-num">2</div>
                <div class="step-text">
                    <b>Click Analyze</b>
                    Docsmith scrapes the docs, extracts all endpoints,
                    auth methods, and generates a ready-to-use wrapper class
                </div>
            </div>
            <div class="hero-step">
                <div class="step-num">3</div>
                <div class="step-text">
                    <b>Ask anything in chat</b>
                    Chat with the documentation — authentication,
                    endpoints, error handling, webhooks, and more
                </div>
            </div>
            <div class="hero-step">
                <div class="step-num">4</div>
                <div class="step-text">
                    <b>Download your code</b>
                    Get a production-ready wrapper class in Python,
                    JavaScript, TypeScript, or Java
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        doc_url = st.text_input(
            "Documentation URL",
            placeholder="https://docs.stripe.com/api"
        )
    with col2:
        language = st.selectbox(
            "Language",
            ["Python", "JavaScript", "TypeScript", "Java"]
        )

    api_name = st.text_input(
        "API Name (optional)",
        placeholder="e.g. Stripe, GitHub, Razorpay"
    )

    analyze_btn = st.button(
        "🔍 Analyze Documentation",
        type="primary",
        use_container_width=True
    )

    st.divider()

    if analyze_btn:
        if not doc_url:
            st.error("Please provide a Documentation URL.")
        else:
            with st.spinner("Analyzing documentation... this takes 30–60 seconds."):
                try:
                    result = run_pipeline(
                        url=doc_url,
                        use_case="extract all endpoints authentication methods base URL and SDK information",
                        language=language,
                        api_name=api_name or "API",
                        max_pages=15
                    )
                    st.session_state.pipeline_result = result
                    st.session_state.index_data = result["index_data"]
                    st.session_state.chat_history = []
                    st.success(
                        f"✅ Done! Scraped {result['scraped']['pages_scraped']} pages. "
                        f"Found {len(result['parsed'].get('endpoints', []))} endpoints. "
                        f"Ask anything in the chat!"
                    )
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

    if st.session_state.pipeline_result:
        result = st.session_state.pipeline_result
        parsed = result["parsed"]
        intent = result["intent"]

        left, right = st.columns([1, 1])

        with left:
            st.markdown("### 💬 Chat with Docs")

            auth_col, sdk_col = st.columns(2)
            with auth_col:
                st.info(f"🔐 **Auth:** {parsed.get('auth_method', 'Unknown')}")
            with sdk_col:
                if parsed.get("sdk_available"):
                    st.success(f"📦 **SDK:** {parsed.get('sdk_name')}")
                else:
                    st.warning("📦 **SDK:** Use REST")

            with st.expander(
                f"📋 All endpoints found ({len(parsed.get('endpoints', []))})"
            ):
                for ep in parsed.get("endpoints", []):
                    st.markdown(
                        f"- `{ep.get('method','?')} {ep.get('path','?')}` "
                        f"— {ep.get('description', '')}"
                    )

            st.markdown("---")

            chat_container = st.container(height=500)
            with chat_container:
                if not st.session_state.chat_history:
                    st.markdown(
                        "<p style='color:rgba(255,255,255,0.3);font-size:13px;"
                        "text-align:center;margin-top:180px'>"
                        "⚒️ Docs analyzed — ask anything below</p>",
                        unsafe_allow_html=True
                    )
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            s1, s2, s3 = st.columns(3)
            with s1:
                if st.button("⚡ Generate wrapper", use_container_width=True):
                    q = f"Give me a complete {language} wrapper class for this API"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.spinner("Thinking..."):
                        ans = answer_question(q, st.session_state.index_data, [])
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    st.rerun()
            with s2:
                if st.button("🔐 Auth setup", use_container_width=True):
                    q = "How do I set up authentication for this API?"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.spinner("Thinking..."):
                        ans = answer_question(q, st.session_state.index_data, [])
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    st.rerun()
            with s3:
                if st.button("⚠️ Error handling", use_container_width=True):
                    q = "How should I handle errors from this API?"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.spinner("Thinking..."):
                        ans = answer_question(q, st.session_state.index_data, [])
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    st.rerun()

            question = st.chat_input("Ask anything about the API documentation...")
            if question:
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Thinking..."):
                    answer = answer_question(
                        question=question,
                        index_data=st.session_state.index_data,
                        chat_history=st.session_state.chat_history[:-1]
                    )
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()

        with right:
            st.markdown("### ⚙️ Generated Code")
            tab1, tab2 = st.tabs(["SDK / Wrapper Class", "Integration Summary"])

            with tab1:
                lang_map = {
                    "Python": "python",
                    "JavaScript": "javascript",
                    "TypeScript": "typescript",
                    "Java": "java"
                }
                ext = (
                    "py" if language == "Python" else
                    "js" if language == "JavaScript" else
                    "ts" if language == "TypeScript" else "java"
                )
                file_name = (
                    f"{(api_name or 'api').lower().replace(' ', '_')}_client.{ext}"
                )
                code_container = st.container(height=600)
                with code_container:
                    st.code(
                        result["code"],
                        language=lang_map.get(language, "python")
                    )
                st.download_button(
                    label=f"⬇️ Download {file_name}",
                    data=result["code"],
                    file_name=file_name,
                    mime="text/plain"
                )

            with tab2:
                st.markdown(f"**Base URL:** `{parsed.get('base_url', 'N/A')}`")
                st.markdown(f"**Auth Method:** {parsed.get('auth_method', 'N/A')}")
                st.markdown(f"**Auth Header:** `{parsed.get('auth_header', 'N/A')}`")
                st.markdown(
                    f"**Integration Path:** {intent.get('integration_path', 'REST')}"
                )
                if parsed.get("sdk_available"):
                    st.markdown(f"**SDK:** `{parsed.get('sdk_name')}`")
                    st.code(parsed.get("sdk_install", ""), language="bash")
                st.markdown("**Integration Notes:**")
                st.markdown(intent.get("explanation", ""))

    else:
        st.markdown(
            "<p style='color:rgba(255,255,255,0.4);font-size:14px;"
            "text-align:center;margin-top:10px'>"
            "👆 Paste a documentation URL above and click "
            "<b style='color:#fff'>Analyze Documentation</b> to get started.</p>",
            unsafe_allow_html=True
        )


# ════════════════════════════════════════
# MODE 2 — API ADVISOR
# ════════════════════════════════════════
else:

    st.markdown("""
    <div class="advisor-box">
        <div class="hero-title">💡 API Advisor</div>
        <div class="hero-steps">
            <div class="hero-step">
                <div class="step-num-green">1</div>
                <div class="step-text">
                    <b>Ask any API question</b>
                    Which payment API should I use? What is the best
                    SMS provider? How does OAuth work?
                </div>
            </div>
            <div class="hero-step">
                <div class="step-num-green">2</div>
                <div class="step-text">
                    <b>Get expert recommendations</b>
                    Docsmith compares APIs on pricing, features, rate limits,
                    and ease of use — then picks a winner
                </div>
            </div>
            <div class="hero-step">
                <div class="step-num-green">3</div>
                <div class="step-text">
                    <b>Learn best practices</b>
                    Auth strategies, error handling, rate limiting,
                    webhooks, pagination, and more
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💬 Chat")

    advisor_container = st.container(height=520)
    with advisor_container:
        if not st.session_state.advisor_history:
            st.markdown(
                "<p style='color:rgba(255,255,255,0.3);font-size:13px;"
                "text-align:center;margin-top:200px'>"
                "💡 Ask me anything about APIs — which to use, "
                "how they compare, integration tips, pricing, and more</p>",
                unsafe_allow_html=True
            )
        for msg in st.session_state.advisor_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if (
            st.session_state.advisor_history
            and st.session_state.advisor_history[-1]["role"] == "user"
        ):
            last_q = st.session_state.advisor_history[-1]["content"]
            with st.spinner("Thinking..."):
                advisor_answer = _get_advisor_answer(
                    last_q,
                    st.session_state.advisor_history[:-1]
                )
            st.session_state.advisor_history.append({
                "role": "assistant",
                "content": advisor_answer
            })
            st.rerun()

    advisor_q = st.chat_input("Ask anything about APIs...")
    if advisor_q:
        st.session_state.advisor_history.append({
            "role": "user",
            "content": advisor_q
        })
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)