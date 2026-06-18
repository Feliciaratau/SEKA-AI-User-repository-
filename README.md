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
