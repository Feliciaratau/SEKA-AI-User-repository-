# Seka.ai — Prototype

A three-tier cultural translation engine for South African indigenous languages.
Built for the AADHIH "Reclaiming African Voices" hackathon (Track 3 — Language
Preservation & NLP).

## What this is

Most translation tools answer "what does this say?" Seka.ai answers "what does
this *mean*, and where does that meaning come from?" Given a phrase, idiom, or
proverb in an indigenous South African language, it returns three layers:

1. **Literal translation** — the word-for-word meaning
2. **Idiomatic intent** — what the phrase actually communicates
3. **Cultural provenance** — the worldview or history behind that meaning

Every AI-generated result is flagged as provisional until verified by a fluent
speaker, and can optionally be logged — with explicit consent — to a mock
community registry that models the project's proposed data-governance approach.

## Project structure

```
seka-ai/
├── app.py                       # Streamlit interface (run this)
├── requirements.txt
├── seka_engine/
│   ├── engine.py                # Core translation logic (provider-agnostic)
│   └── registry.py              # Mock community registry with consent flow
└── data/
    ├── golden_dataset.json      # Curated idioms used for few-shot priming
    └── community_registry.json  # Created automatically when entries are logged
```

## Setup

1. **Install dependencies** (Python 3.10+ recommended):

   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key.** You need EITHER an Anthropic key OR an OpenAI key
   (the app lets you choose which provider to use from the sidebar).

   On macOS/Linux:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   # or
   export OPENAI_API_KEY="sk-your-key-here"
   ```

   On Windows (PowerShell):
   ```powershell
   $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

   Alternatively, you can paste your API key directly into the sidebar text
   box when the app is running — useful for a live demo where you don't want
   to expose environment variables.

3. **Run the app:**

   ```bash
   streamlit run app.py
   ```

   This opens automatically in your browser, usually at `http://localhost:8501`.

## Using the prototype for your demo video

1. Open Google Translate in one browser tab. Type in one of the golden dataset
   phrases (find them in the left-hand dropdown in Seka.ai, or in
   `data/golden_dataset.json`). Show the flat, often confusing literal output.
2. Switch to the Seka.ai tab. Select the same phrase from the dropdown (or type
   it in). Click "Translate with Seka.ai". Watch the three cards populate.
3. Walk through each card, especially Cultural Provenance — this is the
   differentiator.
4. Click through the consent checkbox and log the entry to the registry. Open
   the "View community registry log" expander at the bottom to show it was
   recorded.

This sequence mirrors the demo script in the written submission narrative.

## Important notes on the golden dataset

The five idioms in `data/golden_dataset.json` were sourced from general,
publicly available references on Southern African proverbs during the
hackathon build. They are marked with a `verification_status` field that is
intentionally honest: **some entries have lower confidence than others**, and
ideally all five would be reviewed by a fluent speaker or linguist before the
final submission. This isn't a flaw to hide — it's the same standard of
honesty about AI-generated cultural claims that Seka.ai itself is designed
to enforce. If you can get even one real conversation with a language
speaker before submission, prioritise verifying these five phrases.

## Extending the prototype

Some natural next steps if you have extra time before the deadline:

- Add more golden dataset entries across more of South Africa's 11 official
  languages — only 5 languages are represented so far.
- Add a "Submit a correction" flow so a community reviewer could actually
  change `verification_status` to `community_verified` from within the app.
- Replace the JSON file registry with Airtable (the brief's suggested
  approach) if you want a slightly more "real database" feel for judges.
- Sketch (even just as a diagram, not built code) the WhatsApp access-layer
  pipeline described in the written submission — this is explicitly *not*
  part of this prototype and shouldn't be implied as built.

## Deploying the user-facing `portal.py` to Streamlit Community Cloud

1. Push this repository to a GitHub repo (public or private).
2. Open https://share.streamlit.io and click **New app**. Connect your GitHub repo.
3. Set the entrypoint to `portal.py` and choose the branch you pushed.
4. In the app Settings → Secrets, add one of the following (do NOT commit keys to Git):
   - `ANTHROPIC_API_KEY` — if you plan to use Anthropic
   - `OPENAI_API_KEY` — if you plan to use OpenAI
   Streamlit will expose these as environment variables to the running app.
5. Launch the app. Users will be able to use the portal without needing their
   own API keys; the backend credentials remain private to the deployment.

Recommended production considerations:
- Add an ingress quota or proxy in front of the app if you expect open public traffic.
- Use Streamlit's built-in app metrics and/or an external observability tool to monitor usage and costs.
- If you want centralised control over model provider selection, consider a small backend API that the portal calls; that backend holds the key and can enforce quotas.

If you'd like, I can prepare a simple `deploy` checklist and the exact Git commands to push this repo to GitHub next.

## Optional: Expose a small translate API on the central backend

If you prefer the portal to call a central deployed Seka.ai backend (so the portal never needs any keys), add a tiny API route to the deployed app that wraps `seka_engine.translate` and returns JSON. Example Flask-style endpoint (add to `webhook.py` or a small Flask app on the same host):

```python
from flask import Flask, request, jsonify
from seka_engine.engine import translate

app = Flask(__name__)

@app.route('/api/translate', methods=['POST'])
def api_translate():
   data = request.get_json() or {}
   phrase = data.get('phrase', '')
   language_hint = data.get('language_hint')
   try:
      result = translate(phrase=phrase, provider='anthropic', language_hint=language_hint, api_key=None)
      return jsonify({
         'source_language': result.source_language,
         'source_phrase': result.source_phrase,
         'literal_translation': result.literal_translation,
         'idiomatic_intent': result.idiomatic_intent,
         'cultural_provenance': result.cultural_provenance,
         'community_note': result.community_note,
         'google_translate_failure': result.google_translate_failure if hasattr(result, 'google_translate_failure') else '',
      })
   except Exception as e:
      return jsonify({'error': str(e)}), 500

```

Deploy that alongside your central app (ensure `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set on that host). Then set the portal's "Central backend URL" to that host (e.g. `https://seka-ai-...streamlit.app` if you host the Flask endpoint there).
