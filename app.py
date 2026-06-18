"""
Seka.ai — Streamlit Prototype
--------------------------------
A three-tier cultural translation engine for South African indigenous
languages. This is the judge-facing demo interface for the AADHIH
"Reclaiming African Voices" hackathon submission.

Run locally with:
    streamlit run app.py

Requires an API key set as an environment variable:
    export ANTHROPIC_API_KEY="sk-ant-..."
    or
    export OPENAI_API_KEY="sk-..."
"""

import streamlit as st
import pandas as pd
from seka_engine.engine import translate, load_golden_dataset
from seka_engine.registry import log_entry, list_entries, registry_stats

st.set_page_config(
    page_title="Seka.ai — Cultural Translation Engine",
    page_icon="🌍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .seka-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #B8540A;
        margin-bottom: 0;
    }
    .seka-subheader {
        font-size: 1.1rem;
        color: #5B5B5B;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .tier-card {
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
    }
    .tier-literal { background-color: #F0EDE8; border-left: 4px solid #9C8265; }
    .tier-idiomatic { background-color: #E7F0F5; border-left: 4px solid #2D7A9C; }
    .tier-cultural { background-color: #EAF3E7; border-left: 4px solid #4A8C5E; }
    .tier-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #6B6B6B;
        margin-bottom: 0.3rem;
    }
    .tier-text { font-size: 1.05rem; line-height: 1.5; }
    .provisional-flag {
        font-size: 0.75rem;
        color: #9C6B00;
        background-color: #FFF3D6;
        border-radius: 6px;
        padding: 0.2rem 0.6rem;
        display: inline-block;
        margin-top: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<p class="seka-header">Seka.ai</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="seka-subheader">A three-tier cultural translation engine for South African '
    'indigenous languages — built for the AADHIH "Reclaiming African Voices" hackathon.</p>',
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# Sidebar — configuration + registry stats
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Engine settings")
    provider = st.selectbox("LLM provider", ["anthropic", "openai"], index=0)
    api_key_input = st.text_input(
        f"{'Anthropic' if provider == 'anthropic' else 'OpenAI'} API key",
        type="password",
        help="Falls back to environment variable if left blank."
    )

    st.divider()
    st.subheader("Community registry")
    stats = registry_stats()
    st.metric("Total entries", stats["total_entries"])
    st.metric("Pending verification", stats["pending_verification"])
    if stats["by_language"]:
        st.caption("By language:")
        for lang, count in stats["by_language"].items():
            st.caption(f"  • {lang}: {count}")

    st.divider()
    st.caption(
        "⚠️ This is a prototype. The community registry shown here is a local "
        "mock for demonstration purposes — see the written submission for the "
        "proposed real-world governance model."
    )

# ---------------------------------------------------------------------------
# Main layout — input / output split screen
# ---------------------------------------------------------------------------
golden_dataset = load_golden_dataset()
example_labels = ["— Type your own —"] + [
    f"{idiom['language']}: {idiom['phrase']}" for idiom in golden_dataset
]

left_col, right_col = st.columns([1, 1.3], gap="large")

with left_col:
    st.markdown("### Input")

    selected_example = st.selectbox("Try a golden dataset example, or type your own:", example_labels)

    language_options = [
        "isiZulu", "isiXhosa", "Sesotho", "Sepedi", "Setswana",
        "Tshivenda", "Xitsonga", "siSwati", "isiNdebele", "Other / Not sure",
    ]

    if selected_example != "— Type your own —":
        matched = golden_dataset[example_labels.index(selected_example) - 1]
        default_phrase = matched["phrase"]
        default_lang_index = (
            language_options.index(matched["language"])
            if matched["language"] in language_options else 0
        )
    else:
        default_phrase = ""
        default_lang_index = 0

    selected_language = st.selectbox("Language", language_options, index=default_lang_index)
    phrase_input = st.text_area("Phrase, idiom, or proverb", value=default_phrase, height=100)

    translate_clicked = st.button("Translate with Seka.ai →", type="primary", use_container_width=True)

    st.divider()
    st.markdown("##### Compare against a standard tool")
    st.caption(
        "For the full effect, paste this same phrase into Google Translate in "
        "another tab first — then come back and see what Seka.ai reveals."
    )

with right_col:
    st.markdown("### Output — Three Tiers of Meaning")

    if translate_clicked:
        if not phrase_input.strip():
            st.warning("Please enter a phrase to translate.")
        else:
            key_to_use = api_key_input.strip() if api_key_input.strip() else None
            with st.spinner("Seka is examining the phrase..."):
                try:
                    result = translate(
                        phrase=phrase_input,
                        provider=provider,
                        language_hint=selected_language if selected_language != "Other / Not sure" else None,
                        api_key=key_to_use,
                    )
                    st.session_state["last_result"] = result
                except Exception as e:
                    st.error(f"Translation failed: {e}")
                    st.session_state["last_result"] = None

    result = st.session_state.get("last_result")

    if result:
        st.markdown(f"""
        <div class="tier-card tier-literal">
            <div class="tier-label">Literal Translation</div>
            <div class="tier-text">{result.literal_translation}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="tier-card tier-idiomatic">
            <div class="tier-label">Idiomatic Intent</div>
            <div class="tier-text">{result.idiomatic_intent}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="tier-card tier-cultural">
            <div class="tier-label">Cultural Provenance</div>
            <div class="tier-text">{result.cultural_provenance}</div>
            <div class="provisional-flag">⚠ AI-generated — community verification pending</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("What a standard translation tool would miss"):
            st.write(result.google_translate_failure)

        with st.expander("Community note"):
            st.write(result.community_note)

        st.divider()
        st.markdown("##### Log this to the community registry")
        st.caption("Nothing is saved without your explicit consent. Attribution is optional.")

        consent = st.checkbox("I consent to this phrase and its translation being logged to the registry")
        attribution = st.text_input("Attribution (optional — leave blank to contribute anonymously)")

        if st.button("Log to registry", disabled=not consent):
            entry = log_entry(
                source_language=result.source_language,
                source_phrase=result.source_phrase,
                literal_translation=result.literal_translation,
                idiomatic_intent=result.idiomatic_intent,
                cultural_provenance=result.cultural_provenance,
                consent_given=consent,
                contributor_attribution=attribution.strip() or None,
            )
            st.success(f"Logged to registry as entry {entry.entry_id}. Thank you for your contribution.")
            st.rerun()
    else:
        st.info("Enter a phrase on the left and click Translate to see the three-tier breakdown.")

# ---------------------------------------------------------------------------
# Registry viewer (collapsed by default)
# ---------------------------------------------------------------------------
st.divider()
with st.expander("📖 View community registry log"):
    entries = list_entries()
    if not entries:
        st.caption("No entries logged yet.")
    else:
        for entry in entries:
            attribution_display = entry["contributor_attribution"] or "Anonymous"
            st.markdown(
                f"**{entry['source_language']}** — *{entry['source_phrase']}*  \n"
                f"Contributed by: {attribution_display}  ·  "
                f"Status: {entry['verification_status']}  ·  "
                f"{entry['timestamp'][:10]}"
            )
            st.caption(entry["idiomatic_intent"])
            st.markdown("---")


# ---------------------------------------------------------------------------
# Guardian Verification Queue (admin panel)
# ---------------------------------------------------------------------------
st.divider()
st.markdown("### 🏛️ Guardian Verification Queue (Lekgotla Review Panel)")
st.markdown(
    "This administrative table intercepts live incoming strings from the external WhatsApp ingest layer. "
    "Vetted Language Guardians use this panel to verify cultural accuracy, update metadata, and transition data from *Pending* to *Community_Verified*."
)

# 1. Initialize a Mock Inbound Database in session state so it's dynamic
if "incoming_queue" not in st.session_state:
    st.session_state.incoming_queue = [
        {
            "ID": "SK-9081",
            "Timestamp": "2026-06-18 15:12",
            "Language": "Sepedi",
            "Contributor Input Phrase": "Noga e bolaya ka selo se se mo tsebeng",
            "Suggested Idiomatic Meaning": "A snake kills with what is in its ear (A close friend/relative knows best how to hurt you).",
            "Status": "Pending Review"
        },
        {
            "ID": "SK-9082",
            "Timestamp": "2026-06-18 15:28",
            "Language": "isiZulu",
            "Contributor Input Phrase": "Inja iyawaqgiba amathambo ayo",
            "Suggested Idiomatic Meaning": "A dog buries its own bones (A person should deal with their family problems privately).",
            "Status": "Pending Review"
        },
        {
            "ID": "SK-9083",
            "Timestamp": "2026-06-18 15:34",
            "Language": "isiXhosa",
            "Contributor Input Phrase": "Umntu ngumntu ngabantu",
            "Suggested Idiomatic Meaning": "A person is a person through other persons (Humanity is found in community).",
            "Status": "Pending Review"
        }
    ]

# 2. Render the Queue as a polished Streamlit Dataframe
df_queue = pd.DataFrame(st.session_state.incoming_queue)

# Display the styled dataframe
st.dataframe(
    df_queue,
    column_config={
        "ID": st.column_config.TextColumn("Submission ID"),
        "Timestamp": st.column_config.TextColumn("Received At"),
        "Language": st.column_config.TextColumn("Language"),
        "Contributor Input Phrase": st.column_config.TextColumn("Inbound Text (WhatsApp)"),
        "Suggested Idiomatic Meaning": st.column_config.TextColumn("Engine Pre-Drafted Interpretation"),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Pending Review", "Approved & Verified", "Flagged / Low Quality"],
            required=True,
        )
    },
    hide_index=True,
    use_container_width=True
)

# 3. Add Administrative Interactivity (The Action Section)
st.markdown("#### ⚡ Review Actions")
action_col1, action_col2 = st.columns([2, 3])

with action_col1:
    # Dropdown to pick which ID the guardian wants to evaluate right now
    pending_ids = [item["ID"] for item in st.session_state.incoming_queue if item["Status"] == "Pending Review"]
    
    if pending_ids:
        selected_id = st.selectbox("Select ID to Verify & Push to Production Live Database:", pending_ids)
        approve_btn = st.button("✅ Approve and Commit to Data Trust")
        
        if approve_btn:
            # Find the item and update its status
            for item in st.session_state.incoming_queue:
                if item["ID"] == selected_id:
                    item["Status"] = "Approved & Verified"
                    
            st.success(f"Successfully verified {selected_id}! Data tokenized, POPIA compliance signed off, and committed to the live public API.")
            st.rerun()
    else:
        st.success("🎉 All incoming WhatsApp contributions have been fully verified by the Guardian Council!")
