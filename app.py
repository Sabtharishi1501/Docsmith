import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from core.orchestrator import run_pipeline
import time

load_dotenv()

st.set_page_config(
    page_title="Docsmith",
    page_icon="⚒️",
    layout="wide"
)

st.markdown("""
<style>

/* ── Kill Streamlit default header completely ── */
#MainMenu { visibility: hidden; }
header { visibility: hidden !important; height: 0 !important; }
footer { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── Remove all default padding ── */
html,
body,
[data-testid="stAppViewContainer"],
.main {
    width: 100vw;
    height: 100vh;
    overflow: hidden !important;
}

.block-container {
    max-width: 100% !important;
    width: 100%;
    height: 100vh;
    padding: 10px 20px !important;
    overflow: hidden !important;
}

/* ── Sticky navbar ── */
.sticky-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    background: #0e1117;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    text-align: center;
    padding: 10px 0 8px 0;
}

/* ── Spacer to push content below fixed nav ── */
.spacer { height: 90px; }

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
.top-navbar {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background: #0b1020;
    z-index: 9999;
    padding: 20px 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

.top-navbar-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.brand-title {
    font-size: 42px;
    font-weight: 700;
    color: white;
    margin-bottom: 5px;
}

.brand-subtitle {
    font-size: 18px;
    color: rgba(255,255,255,0.6);
    margin-bottom: 20px;
}

.nav-buttons {
    display: flex;
    gap: 20px;
}

.page-spacer {
    height: 180px;
}

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
}

/* ── Scroll to top JS anchor ── */
#top-anchor { display: block; height: 0; }
            
/* Active button = Green */
.stButton button[kind="primary"] {
    background-color: #1D9E75 !important;
    border-color: #1D9E75 !important;
    color: white !important;
}

/* Hover effect */
.stButton button[kind="primary"]:hover {
    background-color: #16825f !important;
    border-color: #16825f !important;
}

/* Secondary button */
.stButton button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: white !important;
}
            section.main {
    overflow: hidden !important;
}

[data-testid="stAppViewContainer"] {
    overflow: hidden !important;
}

[data-testid="stVerticalBlock"] {
    overflow: hidden;
}
[data-testid="stVerticalBlock"] > div:has([data-testid="stChatMessage"]) {
    height: 700px;
    overflow-y: auto;
}
.chat-window{

    height:50vh;

    overflow-y:auto;

    border:1px solid rgba(255,255,255,.08);

    border-radius:14px;

    padding:20px;

    background:#070d18;

    scroll-behavior:smooth;

}

.user-msg{

    display:flex;

    justify-content:flex-end;

    align-items:flex-start;

    gap:10px;

    margin-bottom:20px;

}

.assistant-msg{

    display:flex;

    align-items:flex-start;

    gap:10px;

    margin-bottom:20px;

}

.user-avatar,
.assistant-avatar{

    width:36px;

    height:36px;

    border-radius:50%;

    display:flex;

    align-items:center;

    justify-content:center;

    font-size:18px;

    flex-shrink:0;

}

.user-avatar{

    background:#ef4444;

}

.assistant-avatar{

    background:#f59e0b;

}

.bubble-user{

    max-width:75%;

    background:#1f2937;

    padding:14px 18px;

    border-radius:14px;

    color:white;

    word-wrap:break-word;

}

.bubble-assistant{

    max-width:75%;

    padding:14px 18px;

    color:white;

    word-wrap:break-word;

    line-height:1.7;

}          
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════
# STREAMING FUNCTIONS
# ════════════════════════════════════════
def _stream_advisor(question: str, history: list):
    system_prompt = """You are an expert API advisor for developers.
You have deep knowledge of all major APIs, SDKs, and developer tools.
Help developers choose the right API, compare options, and learn best practices.
Be concise, practical, and always give a clear recommendation.
Use bullet points or tables where helpful. Always pick a winner when comparing."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": question})

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4,
        max_tokens=1024,
        stream=True
    )
    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


def _stream_doc(question: str, index_data: dict, history: list):
    from core.retriever import retrieve_context
    context = retrieve_context(
        query=question,
        index_data=index_data,
        top_k=3,
        max_chars=2500
    )
    with open("prompts/qa_prompt.txt", "r") as f:
        base_prompt = f.read()

    system = f"{base_prompt}\n\n--- DOCUMENTATION CONTEXT ---\n{context}\n--- END ---"
    messages = [{"role": "system", "content": system}]
    messages.extend(history[-4:])
    messages.append({"role": "user", "content": question})

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
        stream=True
    )
    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


# ── Session state ──
for key, default in {
    "mode": "helper",
    "pipeline_result": None,
    "chat_history": [],
    "index_data": None,
    "advisor_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ════════════════════════════════════════
# MODE TOGGLE BUTTONS
# ════════════════════════════════════════

center1, center2, center3 = st.columns([1, 3, 1])

with center2:

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:20px;">
            <h1 style="margin-bottom:0;">⚒️ Docsmith</h1>
            <p style="color:#9ca3af; font-size:20px;">
                Smart DevTool for API Integration
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    btn1, btn2 = st.columns(2)

    with btn1:
        if st.button(
            "📄 API Doc Helper",
            use_container_width=True,
            type="primary" if st.session_state.mode == "helper" else "secondary"
        ):
            st.session_state.mode = "helper"
            st.rerun()

    with btn2:
        if st.button(
            "💡 API Advisor",
            use_container_width=True,
            type="primary" if st.session_state.mode == "advisor" else "secondary"
        ):
            st.session_state.mode = "advisor"
            st.rerun()

st.divider()

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
                    endpoints, error handling, and more
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
                    from core.orchestrator import run_pipeline
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
                        f"Found {len(result['parsed'].get('endpoints', []))} endpoints."
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

            a1, a2 = st.columns(2)
            with a1:
                st.info(f"🔐 **Auth:** {parsed.get('auth_method', 'Unknown')}")
            with a2:
                if parsed.get("sdk_available"):
                    st.success(f"📦 **SDK:** {parsed.get('sdk_name')}")
                else:
                    st.warning("📦 **SDK:** Use REST")

            with st.expander(
                f"📋 All endpoints ({len(parsed.get('endpoints', []))})"
            ):
                for ep in parsed.get("endpoints", []):
                    st.markdown(
                        f"- `{ep.get('method','?')} {ep.get('path','?')}` "
                        f"— {ep.get('description', '')}"
                    )

            st.markdown("---")

            # Render all previous messages
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if not st.session_state.chat_history:
                st.markdown(
                    "<p style='color:rgba(255,255,255,0.3);font-size:13px;"
                    "text-align:center;padding:30px 0'>"
                    "⚒️ Docs analyzed — ask anything below</p>",
                    unsafe_allow_html=True
                )

            # Suggestion buttons
            s1, s2, s3 = st.columns(3)
            with s1:
                if st.button("⚡ Generate wrapper", use_container_width=True):
                    q = f"Give me a complete {language} wrapper class for this API"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.chat_message("user"):
                        st.markdown(q)
                    with st.chat_message("assistant"):
                        resp = st.write_stream(_stream_doc(
                            q, st.session_state.index_data,
                            st.session_state.chat_history[:-1]
                        ))
                    st.session_state.chat_history.append({"role": "assistant", "content": resp})

            with s2:
                if st.button("🔐 Auth setup", use_container_width=True):
                    q = "How do I set up authentication for this API?"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.chat_message("user"):
                        st.markdown(q)
                    with st.chat_message("assistant"):
                        resp = st.write_stream(_stream_doc(
                            q, st.session_state.index_data,
                            st.session_state.chat_history[:-1]
                        ))
                    st.session_state.chat_history.append({"role": "assistant", "content": resp})

            with s3:
                if st.button("⚠️ Error handling", use_container_width=True):
                    q = "How should I handle errors from this API?"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.chat_message("user"):
                        st.markdown(q)
                    with st.chat_message("assistant"):
                        resp = st.write_stream(_stream_doc(
                            q, st.session_state.index_data,
                            st.session_state.chat_history[:-1]
                        ))
                    st.session_state.chat_history.append({"role": "assistant", "content": resp})

            question = st.chat_input("Ask anything about the API documentation...")
            if question:
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant"):
                    resp = st.write_stream(_stream_doc(
                        question,
                        st.session_state.index_data,
                        st.session_state.chat_history[:-1]
                    ))
                st.session_state.chat_history.append({"role": "assistant", "content": resp})

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
                st.markdown(f"**Integration Path:** {intent.get('integration_path', 'REST')}")
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

    left, right = st.columns([1, 2])

    with left:
        advisor_html = """
        <div class="advisor-box">

            <div class="hero-title">💡 API Advisor</div>

            <div class="hero-step">
                <div class="step-num-green">1</div>
                <div class="step-text">
                    <b>Ask any API question</b><br>
                    Which payment API should I use?<br>
                    What is the best SMS provider?<br>
                    How does OAuth work?
                </div>
            </div>

            <br>

            <div class="hero-step">
                <div class="step-num-green">2</div>
                <div class="step-text">
                    <b>Get expert recommendations</b><br>
                    Docsmith compares APIs on pricing,
                    features, rate limits and ease of use
                    and picks a winner.
                </div>
            </div>

            <br>

            <div class="hero-step">
                <div class="step-num-green">3</div>
                <div class="step-text">
                    <b>Learn best practices</b><br>
                    Auth strategies, error handling,
                    rate limiting, webhooks,
                    pagination and more.
                </div>
            </div>

        </div>
        """

        st.html(advisor_html)
    # RIGHT PANEL
    with right:

    # ---------- Chat History ----------
        chat_html = ""

        if not st.session_state.advisor_history:

            chat_html = """
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                height:100%;
                color:#9ca3af;
                font-size:18px;
            ">
                Ask me anything about APIs, SDKs, pricing,
                authentication, rate limits and integrations.
            </div>
            """

        else:

            for msg in st.session_state.advisor_history:

                if msg["role"] == "user":

                    chat_html += f"""
                    <div class="user-msg">
                        <div class="user-avatar">😊</div>
                        <div class="bubble-user">
                            {msg["content"]}
                        </div>
                    </div>
                    """

                else:

                    chat_html += f"""
                    <div class="assistant-msg">
                        <div class="assistant-avatar">🤖</div>
                        <div class="bubble-assistant">
                            {msg["content"]}
                        </div>
                    </div>
                    """

        st.html(f"""
        <div id="chat-window" class="chat-window">
            {chat_html}
        </div>

        <script>

        function scrollBottom(){{
            const chat=document.getElementById("chat-window");
            if(chat){{
                chat.scrollTop=chat.scrollHeight;
            }}
        }}

        scrollBottom();

        new MutationObserver(scrollBottom)
        .observe(
            document.getElementById("chat-window"),
            {{
                childList:true,
                subtree:true
            }}
        );

        </script>
        """)

        advisor_q = st.chat_input("Ask anything about APIs...")

        if advisor_q:

            st.session_state.advisor_history.append(
                {
                    "role":"user",
                    "content":advisor_q
                }
            )

            resp = ""

            with st.spinner("Thinking..."):

                for token in _stream_advisor(
                    advisor_q,
                    st.session_state.advisor_history[:-1]
                ):
                    resp += token

            st.session_state.advisor_history.append(
                {
                    "role":"assistant",
                    "content":resp
                }
            )

            st.rerun()