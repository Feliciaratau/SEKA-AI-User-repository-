import streamlit as st
from seka_engine.engine import translate
import requests
import os

st.set_page_config(page_title="Seka.ai Portal | Knowledge Hub", page_icon="🌍", layout="centered")

st.markdown("""
    <style>
    .hero {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        font-size: 3rem;
        margin-bottom: 0.3rem;
        color: #006259;
    }
    .hero p {
        font-size: 1rem;
        color: #4d4d4d;
        margin-top: 0;
    }
    .prompt-card {
        border-radius: 20px;
        padding: 1.6rem;
        box-shadow: 0 16px 40px rgba(0,0,0,0.06);
        margin-bottom: 1.2rem;
    }
    .tier-card {
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .literal { background: #f8f9fa; border-left: 6px solid #6c757d; }
    .idiomatic { background: #e8f5e9; border-left: 6px solid #2e7d32; }
    .cultural { background: #fff8e1; border-left: 6px solid #f57f17; }
    .tier-label { font-weight: 700; margin-bottom: 0.4rem; }
    .example-buttons button {
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .note-box {
        border-radius: 14px;
        padding: 1rem;
        background: #eef9fb;
        border-left: 5px solid #0d6b74;
        color: #2d4f54;
    }
    .footer-note { color: #6c757d; font-size: 0.95rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🌍 Seka.ai Portal</h1><p>Explore the meaning of indigenous South African phrases, proverbs, and idioms in a simple, chat-style experience.</p></div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="prompt-card">', unsafe_allow_html=True)
    phrase = st.text_area("Ask Seka.ai about a phrase:", height=140)
    # Option to use central deployed backend (no key needed if it exposes an API)
    use_central = st.checkbox("Use central Seka.ai backend (no API key required)", value=True)
    central_backend_url = st.text_input("Central backend URL", value="http://localhost:5001")
    example_col1, example_col2 = st.columns(2)
    with example_col1:
        if st.button("Izandla ziyagezana"):
            phrase = "Izandla ziyagezana"
    with example_col2:
        if st.button("Kgomo e bolawa ke molapo"):
            phrase = "Kgomo e bolawa ke molapo"
    st.markdown('</div>', unsafe_allow_html=True)

    # Note removed: user-facing API-key reminder

if st.button("Translate with Seka.ai", type="primary", use_container_width=True):
    if not phrase.strip():
        st.warning("Please enter a phrase before translating.")
    else:
        with st.spinner("Seka.ai is interpreting your phrase..."):
                result = None
                # Try central backend first (if selected)
                if use_central and central_backend_url:
                    try:
                        resp = requests.post(
                            central_backend_url.rstrip("/") + "/api/translate",
                            json={
                                "phrase": phrase.strip(),
                                "language_hint": None,
                            },
                            timeout=15,
                        )
                        if resp.status_code == 200:
                            raw = resp.json()
                            # normalize into an object-like simple namespace
                            class R: pass
                            result = R()
                            result.literal_translation = raw.get("literal_translation")
                            result.idiomatic_intent = raw.get("idiomatic_intent")
                            result.cultural_provenance = raw.get("cultural_provenance")
                            result.community_note = raw.get("community_note")
                            result.source_language = raw.get("source_language")
                            result.source_phrase = raw.get("source_phrase")
                        else:
                            st.warning(f"Central backend returned {resp.status_code}: {resp.text[:200]}")
                    except Exception as e:
                        st.info(f"Central backend call failed: {e}")

                # Fallback to local engine if central not used or failed
                if not result:
                    try:
                        provider = "anthropic"
                        # engine will read environment variables for keys on the host
                        result = translate(
                            phrase=phrase.strip(),
                            provider=provider,
                            api_key=None,
                        )
                    except Exception as e:
                        st.error(f"Unable to translate this phrase right now: {e}")
                        result = None

        if result:
            st.markdown(f"<div class='tier-card literal'><div class='tier-label'>📝 Literal translation</div><div>{result.literal_translation}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='tier-card idiomatic'><div class='tier-label'>💡 Idiomatic meaning</div><div>{result.idiomatic_intent}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='tier-card cultural'><div class='tier-label'>🌍 Cultural context</div><div>{result.cultural_provenance}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='note-box'><strong>Insight:</strong> {result.community_note}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='footer-note'>Source language detected: {result.source_language}.</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div class='footer-note'>The existing deployed Seka.ai backend remains unchanged. This portal is a separate, user-friendly interface for exploring cultural meaning.</div>", unsafe_allow_html=True)
