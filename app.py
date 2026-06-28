import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from core.orchestrator import run_pipeline
import re

load_dotenv()

st.set_page_config(
    page_title="Docsmith",
    page_icon="⚒️",
    layout="wide"
)

st.markdown("""
<style>
#MainMenu { visibility: hidden !important; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

.block-container {
    padding-top: 0px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}

.hero-box {
    background: rgba(108,99,255,0.08);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
}
.advisor-box {
    background: rgba(29,158,117,0.08);
    border: 1px solid rgba(29,158,117,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
}
.hero-title {
    font-size: 15px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 10px;
}
.hero-steps { display: flex; gap: 12px; flex-wrap: wrap; }
.hero-step {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    flex: 1;
    min-width: 130px;
    margin-bottom: 8px;
}
.step-num {
    width: 20px; height: 20px; border-radius: 50%;
    background: #6C63FF; color: #fff; font-size: 11px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 2px;
}
.step-num-green {
    width: 20px; height: 20px; border-radius: 50%;
    background: #1D9E75; color: #fff; font-size: 11px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 2px;
}
.step-text { font-size: 12px; color: rgba(255,255,255,0.7); line-height: 1.4; }
.step-text b { color: #fff; display: block; margin-bottom: 2px; font-size: 12px; }

.note-box {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.25);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 14px;
    font-size: 13px;
    color: rgba(255,255,255,0.85);
    line-height: 1.7;
}
.note-box .note-title {
    font-weight: 600;
    color: #f59e0b;
    margin-bottom: 8px;
    font-size: 13px;
}
.note-box ol {
    margin: 0 0 0 18px;
    padding: 0;
}
.note-box li {
    margin-bottom: 4px;
}
.note-box code {
    background: rgba(255,255,255,0.1);
    padding: 1px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
}

.stButton button[kind="primary"] {
    background-color: #1D9E75 !important;
    border-color: #1D9E75 !important;
    color: white !important;
}
.stButton button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: white !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)


def render_md(text: str) -> str:
    import re

    code_blocks = {}
    counter = [0]

    def extract_code_block(match):
        lang = match.group(1).strip() if match.group(1) else "code"
        code = match.group(2)
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        placeholder = f"__CODEBLOCK_{counter[0]}__"
        code_blocks[placeholder] = f"""<div style="background:#0d1117;border:1px solid rgba(99,102,241,0.3);border-left:3px solid #6C63FF;border-radius:8px;margin:10px 0;overflow-x:auto"><div style="padding:4px 12px;background:rgba(108,99,255,0.15);border-bottom:1px solid rgba(99,102,241,0.2);font-size:11px;color:#AFA9EC;font-family:monospace">{lang}</div><pre style="margin:0;padding:12px 16px;font-family:'Courier New',Consolas,monospace;font-size:12px;line-height:1.7;color:#e2e8f0;white-space:pre-wrap;word-break:break-word"><code>{code.strip()}</code></pre></div>"""
        counter[0] += 1
        return placeholder

    text = re.sub(r'```(\w*)\n?([\s\S]*?)```', extract_code_block, text)

    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#fff;font-weight:600">\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(
        r'`([^`\n]+)`',
        r'<code style="background:rgba(108,99,255,0.2);color:#AFA9EC;padding:1px 6px;border-radius:4px;font-family:monospace;font-size:12px">\1</code>',
        text
    )

    lines = text.split('\n')
    result = []
    in_ul = False
    in_ol = False
    in_table = False

    for line in lines:
        s = line.strip()

        if not s:
            if in_ul: result.append('</ul>'); in_ul = False
            if in_ol: result.append('</ol>'); in_ol = False
            if in_table: result.append('</table>'); in_table = False
            continue

        if s.startswith('__CODEBLOCK_') and s.endswith('__'):
            if in_ul: result.append('</ul>'); in_ul = False
            if in_ol: result.append('</ol>'); in_ol = False
            if in_table: result.append('</table>'); in_table = False
            result.append(code_blocks.get(s, s))
            continue

        if s.startswith('* ') or s.startswith('- '):
            if in_ol: result.append('</ol>'); in_ol = False
            if not in_ul:
                result.append('<ul style="margin:6px 0 6px 18px;padding:0">')
                in_ul = True
            result.append(f'<li style="margin-bottom:4px">{s[2:]}</li>')

        elif re.match(r'^\d+\.\s', s):
            if in_ul: result.append('</ul>'); in_ul = False
            if not in_ol:
                result.append('<ol style="margin:6px 0 6px 18px;padding:0">')
                in_ol = True
            content = re.sub(r'^\d+\.\s', '', s)
            result.append(f'<li style="margin-bottom:4px">{content}</li>')

        elif s.startswith('| ') and '|' in s[1:]:
            if in_ul: result.append('</ul>'); in_ul = False
            if in_ol: result.append('</ol>'); in_ol = False
            cells = [c.strip() for c in s.split('|') if c.strip()]
            if all(set(c) <= set('-: ') for c in cells):
                continue
            if not in_table:
                result.append('<table style="border-collapse:collapse;width:100%;margin:8px 0;font-size:12px">')
                in_table = True
                tag = 'th'
            else:
                tag = 'td'
            bg = 'background:rgba(255,255,255,0.06);' if tag == 'th' else ''
            row = ''.join(
                f'<{tag} style="border:1px solid rgba(255,255,255,0.12);padding:5px 10px;{bg}">{c}</{tag}>'
                for c in cells
            )
            result.append(f'<tr>{row}</tr>')

        else:
            if in_ul: result.append('</ul>'); in_ul = False
            if in_ol: result.append('</ol>'); in_ol = False
            if in_table: result.append('</table>'); in_table = False
            result.append(f'<p style="margin:0 0 6px 0">{s}</p>')

    if in_ul: result.append('</ul>')
    if in_ol: result.append('</ol>')
    if in_table: result.append('</table>')

    return ''.join(result)


# ════════════════════════════════════════
# CHAT BOX RENDERER
# ════════════════════════════════════════
def render_chat_box(messages: list, box_id: str = "chat-box", height: int = 420):
    chat_inner = ""
    if not messages:
        chat_inner = """
        <div style="display:flex;align-items:center;justify-content:center;
        height:100%;color:rgba(255,255,255,0.25);font-size:13px;text-align:center;padding:20px">
            Ask me anything...
        </div>"""
    else:
        for msg in messages:
            if msg["role"] == "user":
                content = msg['content'].replace("<", "&lt;").replace(">", "&gt;")
                chat_inner += f"""
                <div style="display:flex;justify-content:flex-end;
                align-items:flex-start;gap:8px;margin-bottom:16px">
                    <div style="max-width:75%;background:#1f2937;padding:10px 14px;
                    border-radius:12px;color:white;font-size:13px;
                    line-height:1.6;word-wrap:break-word">
                        {content}
                    </div>
                    <div style="width:30px;height:30px;border-radius:50%;
                    background:#ef4444;display:flex;align-items:center;
                    justify-content:center;font-size:15px;flex-shrink:0">😊</div>
                </div>"""
            else:
                rendered = render_md(msg["content"])
                chat_inner += f"""
                <div style="display:flex;align-items:flex-start;
                gap:8px;margin-bottom:16px">
                    <div style="width:30px;height:30px;border-radius:50%;
                    background:#f59e0b;display:flex;align-items:center;
                    justify-content:center;font-size:15px;flex-shrink:0">🤖</div>
                    <div style="max-width:85%;color:rgba(255,255,255,0.9);
                    font-size:13px;line-height:1.8;word-wrap:break-word;min-width:0">
                        {rendered}
                    </div>
                </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #070d18;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}
#chat-box {{
    height: {height}px;
    overflow-y: auto;
    padding: 16px;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    background: #070d18;
}}
#chat-box::-webkit-scrollbar {{ width: 4px; }}
#chat-box::-webkit-scrollbar-thumb {{
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
}}
</style>
</head>
<body>
    <div id="chat-box">
        {chat_inner}
    </div>
    <script>
        var box = document.getElementById('chat-box');
        if (box) box.scrollTop = box.scrollHeight;
    </script>
</body>
</html>"""

    st.iframe(html, height=height + 4)


# ════════════════════════════════════════
# STREAMING FUNCTIONS
# ════════════════════════════════════════
def _stream_advisor(question: str, history: list):
    system_prompt = """You are an expert API advisor for developers.
Help developers choose the right API, compare options, learn best practices.
Be concise and practical. Always give a clear recommendation.
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


def _stream_doc(
    question: str,
    index_data: dict,
    history: list,
    parsed_data: dict = None
):
    from core.retriever import retrieve_context
    context = retrieve_context(
        query=question, index_data=index_data, top_k=3, max_chars=2500
    )
    with open("prompts/qa_prompt.txt", "r") as f:
        base = f.read()

    # Build endpoints section from parsed data
    endpoints_section = ""
    if parsed_data and parsed_data.get("endpoints"):
        base_url = parsed_data.get("base_url", "")
        auth_method = parsed_data.get("auth_method", "")
        auth_header = parsed_data.get("auth_header", "")
        ep_lines = []
        for ep in parsed_data["endpoints"]:
            method = ep.get("method", "?")
            path = ep.get("path", "?")
            desc = ep.get("description", "")
            params = ep.get("parameters", [])
            param_str = ", ".join(
                f"{p.get('name')}({p.get('type','')})"
                for p in params
            ) if params else "none"
            ep_lines.append(
                f"  - {method} {path} — {desc} | params: {param_str}"
            )
        endpoints_section = f"""
--- EXTRACTED API ENDPOINTS ---
Base URL: {base_url}
Auth Method: {auth_method}
Auth Header: {auth_header}
Endpoints:
{chr(10).join(ep_lines)}
--- END ENDPOINTS ---
"""

    system = f"""{base}

{endpoints_section}

--- DOCUMENTATION CONTEXT ---
{context}
--- END CONTEXT ---

IMPORTANT: You have the extracted endpoints listed above. Always use them to answer questions about available endpoints, methods, paths, and parameters. Never say endpoints are not available if they are listed above."""

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
for key, val in {
    "mode": "helper",
    "pipeline_result": None,
    "chat_history": [],
    "index_data": None,
    "advisor_history": [],
    "last_chat_len": 0,
    "last_advisor_len": 0,
    "saved_doc_url": "",        
    "saved_api_name": "", 
    "saved_language": "Python",
    "saved_use_case": "" ,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

mode = st.session_state.mode


# ════════════════════════════════════════
# HEADER
# ════════════════════════════════════════
st.markdown(
    "<h2 style='text-align:center;margin:16px 0 2px 0'>⚒️ Docsmith</h2>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center;color:rgba(255,255,255,0.4);font-size:12px;"
    "margin-bottom:12px'>Smart DevTool for API Integration</p>",
    unsafe_allow_html=True
)

hc1, hc2, hc3 = st.columns([3, 2, 3])
with hc2:
    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            "📄 API Doc Helper",
            use_container_width=True,
            type="primary" if mode == "helper" else "secondary",
            key="btn_helper"
        ):
            st.session_state.mode = "helper"
            st.rerun()
    with b2:
        if st.button(
            "💡 API Advisor",
            use_container_width=True,
            type="primary" if mode == "advisor" else "secondary",
            key="btn_advisor"
        ):
            st.session_state.mode = "advisor"
            st.rerun()

st.markdown("<hr style='margin:10px 0 16px 0'>", unsafe_allow_html=True)


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
                <div class="step-text"><b>Paste any API doc URL</b>
                Stripe, GitHub, Razorpay, Twilio and more</div>
            </div>
            <div class="hero-step">
                <div class="step-num">2</div>
                <div class="step-text"><b>Describe your use case</b>
                e.g. "I want to charge a customer after checkout"</div>
            </div>
            <div class="hero-step">
                <div class="step-num">3</div>
                <div class="step-text"><b>Ask anything in chat</b>
                Auth, endpoints, error handling and more</div>
            </div>
            <div class="hero-step">
                <div class="step-num">4</div>
                <div class="step-text"><b>Download your code</b>
                Wrapper class, tests and Postman collection</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    left_inputs, right_inputs = st.columns([1, 1])

    with left_inputs:
        doc_url = st.text_input(
            "Documentation URL",
            placeholder="e.g. https://docs.stripe.com/api",
            value=st.session_state.get("saved_doc_url", ""),
            key="doc_url_input"
        )
        api_name = st.text_input(
            "API Name (optional)",
            placeholder="e.g. Stripe, GitHub, Razorpay",
            value=st.session_state.get("saved_api_name", ""),
            key="api_name_input"
        )

    with right_inputs:
        language = st.selectbox(
            "Preferred Language",
            ["Python", "JavaScript", "TypeScript", "Java"],
            index=["Python", "JavaScript", "TypeScript", "Java"].index(
                st.session_state.get("saved_language", "Python")
            ),
            key="language_input"
        )
        use_case = st.text_area(
            "Use Case — describe what you want to build",
            value=st.session_state.get("saved_use_case", ""),
            height=100,
            key="use_case_input"
        )

    if st.button("🔍 Analyze Documentation", type="primary",
                 use_container_width=True):
        if not doc_url:
            st.error("Please provide a Documentation URL.")
        elif not use_case:
            st.error("Please describe your use case so Docsmith can filter the right endpoints.")
        else:
            # Save inputs to session state so they persist on tab switch
            st.session_state.saved_doc_url = doc_url
            st.session_state.saved_api_name = api_name
            st.session_state.saved_language = language
            st.session_state.saved_use_case = use_case

            with st.spinner("Analyzing... this takes 30–90 seconds."):
                try:
                    result = run_pipeline(
                        url=doc_url,
                        use_case=use_case,
                        language=language,
                        api_name=api_name or "API",
                        max_pages=15
                    )
                    st.session_state.pipeline_result = result
                    st.session_state.index_data = result["index_data"]
                    st.session_state.chat_history = []
                    st.success(
                        f"✅ Scraped {result['scraped']['pages_scraped']} pages. "
                        f"Found {len(result['parsed'].get('endpoints', []))} endpoints. "
                        f"Ask anything in the chat!"
                    )
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

    st.divider()

    if st.session_state.pipeline_result:
        result = st.session_state.pipeline_result
        parsed = result["parsed"]
        intent = result["intent"]

        left, right = st.columns([1, 1])

        # ── RIGHT panel — code tabs ──
        with right:
            st.markdown("### ⚙️ Generated Code")

            lang_map = {
                "Python": "python", "JavaScript": "javascript",
                "TypeScript": "typescript", "Java": "java"
            }
            ext = ("py" if language == "Python" else
                   "js" if language == "JavaScript" else
                   "ts" if language == "TypeScript" else "java")
            file_name = f"{(api_name or 'api').lower().replace(' ','_')}_client.{ext}"
            postman_file = f"{(api_name or 'api').lower().replace(' ','_')}_collection.json"

            tab1, tab2, tab3 = st.tabs([
                "SDK / Wrapper Class",
                "Integration Summary",
                "Postman Collection"
            ])

            with tab1:
                code_container = st.container(height=500)
                with code_container:
                    st.code(result["code"],
                            language=lang_map.get(language, "python"))
                st.download_button(
                    label=f"⬇️ Download {file_name}",
                    data=result["code"],
                    file_name=file_name,
                    mime="text/plain",
                    key="download_btn"
                )

            with tab2:
                st.markdown(f"**Base URL:** `{parsed.get('base_url','N/A')}`")
                st.markdown(f"**Auth Method:** {parsed.get('auth_method','N/A')}")
                st.markdown(f"**Auth Header:** `{parsed.get('auth_header','N/A')}`")
                st.markdown(f"**Integration Path:** {intent.get('integration_path','REST')}")
                if parsed.get("sdk_available"):
                    st.markdown(f"**SDK:** `{parsed.get('sdk_name')}`")
                    st.code(parsed.get("sdk_install", ""), language="bash")
                st.markdown("**Integration Notes:**")
                st.markdown(intent.get("explanation", ""))

            with tab3:
                st.markdown("""
                <div class="note-box">
                    <div class="note-title">📬 How to use the Postman Collection</div>
                    <ol>
                        <li>Download the collection file using the button below</li>
                        <li>Open <strong>Postman</strong> on your computer</li>
                        <li>Click <strong>Import</strong> → select the downloaded <code>.json</code> file</li>
                        <li>Go to the collection → click <strong>Variables</strong></li>
                        <li>Set <code>api_key</code> to your actual API key</li>
                        <li>Every endpoint is now ready — click <strong>Send</strong> on any request</li>
                    </ol>
                </div>
                """, unsafe_allow_html=True)

                if result.get("postman_json"):
                    postman_container = st.container(height=400)
                    with postman_container:
                        st.code(result["postman_json"], language="json")
                    st.download_button(
                        label="⬇️ Download Postman Collection",
                        data=result["postman_json"],
                        file_name=postman_file,
                        mime="application/json",
                        key="download_postman_btn"
                    )
                else:
                    st.info("Postman collection not available for this analysis.")

        # ── LEFT panel — chat ──
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

            # ── Scrollable endpoints box ──
            st.markdown(
                f"**📋 All endpoints ({len(parsed.get('endpoints', []))})**"
            )
            endpoint_container = st.container(height=200)
            with endpoint_container:
                for ep in parsed.get("endpoints", []):
                    st.markdown(
                        f"- `{ep.get('method','?')} {ep.get('path','?')}` "
                        f"— {ep.get('description', '')}"
                    )

            st.markdown("---")

            render_chat_box(st.session_state.chat_history, height=400)

            s1, s2, s3 = st.columns(3)
            with s1:
                if st.button("⚡ Generate wrapper", use_container_width=True,
                             key="gen_wrap"):
                    q = f"Give me a complete {language} wrapper class for this API"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    resp = ""
                    with st.spinner("Generating..."):
                        for token in _stream_doc(
                            q,
                            st.session_state.index_data,
                            st.session_state.chat_history[:-1],
                            parsed_data=parsed
                        ):
                            resp += token
                    st.session_state.chat_history.append({"role": "assistant", "content": resp})
                    st.rerun()
            with s2:
                if st.button("🔐 Auth setup", use_container_width=True,
                             key="auth_setup"):
                    q = "How do I set up authentication for this API?"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    resp = ""
                    with st.spinner("Thinking..."):
                        for token in _stream_doc(
                            q,
                            st.session_state.index_data,
                            st.session_state.chat_history[:-1],
                            parsed_data=parsed
                        ):
                            resp += token
                    st.session_state.chat_history.append({"role": "assistant", "content": resp})
                    st.rerun()
            with s3:
                if st.button("⚠️ Error handling", use_container_width=True,
                             key="err_handle"):
                    q = "How should I handle errors from this API?"
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    resp = ""
                    with st.spinner("Thinking..."):
                        for token in _stream_doc(
                            q,
                            st.session_state.index_data,
                            st.session_state.chat_history[:-1],
                            parsed_data=parsed
                        ):
                            resp += token
                    st.session_state.chat_history.append({"role": "assistant", "content": resp})
                    st.rerun()

            question = st.chat_input(
                "Ask anything about the API documentation...",
                key="doc_chat_input"
            )
            if question:
                st.session_state.chat_history.append({"role": "user", "content": question})
                resp = ""
                with st.spinner("Thinking..."):
                    for token in _stream_doc(
                        question,
                        st.session_state.index_data,
                        st.session_state.chat_history[:-1],
                        parsed_data=parsed
                    ):
                        resp += token
                st.session_state.chat_history.append({"role": "assistant", "content": resp})
                st.rerun()

    else:
        st.markdown(
            "<p style='color:rgba(255,255,255,0.4);font-size:14px;"
            "text-align:center;margin-top:10px'>"
            "👆 Fill in the URL and use case above, then click "
            "<b style='color:#fff'>Analyze Documentation</b> to get started.</p>",
            unsafe_allow_html=True
        )


# ════════════════════════════════════════
# MODE 2 — API ADVISOR
# ════════════════════════════════════════
else:

    left, right = st.columns([1, 2])

    with left:
        st.markdown("""
        <div class="advisor-box">
            <div class="hero-title">💡 API Advisor</div>
            <div class="hero-step" style="margin-bottom:10px">
                <div class="step-num-green">1</div>
                <div class="step-text"><b>Ask any API question</b>
                Which payment API? Best SMS provider? How does OAuth work?</div>
            </div>
            <div class="hero-step" style="margin-bottom:10px">
                <div class="step-num-green">2</div>
                <div class="step-text"><b>Get expert recommendations</b>
                Compare APIs on pricing, features, rate limits — picks a winner</div>
            </div>
            <div class="hero-step">
                <div class="step-num-green">3</div>
                <div class="step-text"><b>Learn best practices</b>
                Auth, error handling, rate limiting, webhooks and more</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("### 💬 Chat")

        render_chat_box(st.session_state.advisor_history, height=420)

        advisor_q = st.chat_input(
            "Ask anything about APIs...",
            key="advisor_chat_input"
        )
        if advisor_q:
            st.session_state.advisor_history.append({
                "role": "user",
                "content": advisor_q
            })
            resp = ""
            with st.spinner("Thinking..."):
                for token in _stream_advisor(
                    advisor_q,
                    st.session_state.advisor_history[:-1]
                ):
                    resp += token
            st.session_state.advisor_history.append({
                "role": "assistant",
                "content": resp
            })
            st.rerun()