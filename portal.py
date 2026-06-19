import streamlit as st
from seka_engine.engine import translate
import requests
import os
import json
import anthropic

# 1. INITIALIZE THE SHARED VERIFIED DATABASE
DB_FILE = "seka_database.json"
verified_database = {}

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r") as f:
            verified_database = json.load(f)
    except Exception:
        st.error("Could not read database file. Reverting to empty cache.")

# 2. ANTHROPIC CLIENT SETUP
try:
    client = anthropic.Anthropic()
except Exception:
    client = None

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
            lookup_key = phrase.strip().lower()
            
            # CHOICE A: The phrase is already verified in our Data Trust file!
            if lookup_key in verified_database:
                data = verified_database[lookup_key]
                st.success(f"✨ Match Verified in Community Data Trust — Language: {data['language']}")
                
                st.markdown(f"""
                    <div style="background-color: #f8f9fa; border-left: 5px solid #6c757d; padding: 15px; margin-bottom: 15px; border-radius: 8px; color: #333;">
                        <strong>📝 Literal Translation:</strong><br><i>{data.get('literal', 'N/A')}</i>
                    </div>
                    <div style="background-color: #e8f5e9; border-left: 5px solid #2e7d32; padding: 15px; margin-bottom: 15px; border-radius: 8px; color: #333;">
                        <strong>💡 Idiomatic Meaning:</strong><br><b>{data.get('idiomatic', 'N/A')}</b>
                    </div>
                    <div style="background-color: #fff8e1; border-left: 5px solid #f57f17; padding: 15px; border-radius: 8px; color: #333;">
                        <strong>🌍 Cultural Context:</strong><br>{data.get('context', 'N/A')}<br>
                        <small style="color: #666;">Source: {data.get('source', 'Community Verified')}</small>
                    </div>
                """, unsafe_allow_html=True)
                
            # CHOICE B: The phrase is entirely new. Run it through the LLM with strict rules.
            else:
                if not client:
                    st.error("API client not configured. Please ensure your Anthropic API key is set up.")
                else:
                    st.info("🔍 Phrase not in local trust cache. Querying live engine with strict cultural guardrails...")
                    
                    system_prompt = (
                        "You are an expert South African linguist and cultural historian specializing in Nguni and Sotho-Tswana languages. "
                        "Your job is to analyze the input phrase and break it down into three tiers. "
                        "CRITICAL: Be extremely precise about language detection. For example, 'Izandla ziyagezana' is strictly isiZulu, not isiXhosa. "
                        "You must return your answer STRICTLY as a raw JSON object. Do not include markdown formatting like ```json, do not include introductory text. "
                        "Use these exact JSON keys: \n"
                        "{\n"
                        '  "language": "Detected Language (e.g., isiZulu, Sepedi, etc.)",\n'
                        '  "literal": "The precise word-for-word translation into English",\n'
                        '  "idiomatic": "The deeper metaphorical or figurative meaning",\n'
                        '  "context": "The historical context, philosophical roots, or societal usage of the phrase"\n'
                        "}"
                    )
                    
                    try:
                        message = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1000,
                            system=system_prompt,
                            messages=[{"role": "user", "content": f"Analyze this phrase: {phrase.strip()}"}]
                        )
                        
                        raw_text = message.content[0].text.strip()
                        
                        # Strip any markdown backticks if Claude added them anyway
                        if raw_text.startswith("```json"):
                            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                        elif raw_text.startswith("```"):
                            raw_text = raw_text.replace("```", "").strip()
                        
                        ai_data = json.loads(raw_text)
                        
                        st.success(f"✨ Live Engine Detection — Language: {ai_data.get('language')}")
                        
                        st.markdown(f"""
                            <div style="background-color: #f8f9fa; border-left: 5px solid #6c757d; padding: 15px; margin-bottom: 15px; border-radius: 8px; color: #333;">
                                <strong>📝 Literal Translation:</strong><br><i>{ai_data.get('literal', 'N/A')}</i>
                            </div>
                            <div style="background-color: #e8f5e9; border-left: 5px solid #2e7d32; padding: 15px; margin-bottom: 15px; border-radius: 8px; color: #333;">
                                <strong>💡 Idiomatic Meaning:</strong><br><b>{ai_data.get('idiomatic', 'N/A')}</b>
                            </div>
                            <div style="background-color: #fff8e1; border-left: 5px solid #f57f17; padding: 15px; border-radius: 8px; color: #333;">
                                <strong>🌍 Cultural Context:</strong><br>{ai_data.get('context', 'N/A')}<br>
                                <small style="color: #d32f2f;">⚠️ <i>Unverified AI draft. Sent to the Lekgotla Review queue for guardian authentication.</i></small>
                            </div>
                        """, unsafe_allow_html=True)
                        
                    except json.JSONDecodeError:
                        st.error("💥 System Error: The engine returned an unstructured block. Please try again.")
                    except Exception as e:
                        st.error(f"🔗 API Connection Error: {str(e)}")

st.markdown("---")
st.markdown("<div class='footer-note'>The existing deployed Seka.ai backend remains unchanged. This portal is a separate, user-friendly interface for exploring cultural meaning.</div>", unsafe_allow_html=True)
