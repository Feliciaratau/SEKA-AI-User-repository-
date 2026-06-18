"""
Seka.ai Cultural Translation Engine
-------------------------------------
Core engine module. Wraps either the Anthropic Claude API or the OpenAI API
behind a single interface, using few-shot prompting against the golden
dataset to produce structured three-tier cultural translations.

This module has NO Streamlit dependency — it can be tested standalone,
imported into a notebook, or swapped into a different frontend later.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Literal, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GOLDEN_DATASET_PATH = DATA_DIR / "golden_dataset.json"

SYSTEM_PROMPT = """You are the Seka.ai cultural translation engine, built specifically for South African indigenous languages, including isiZulu, isiXhosa, Sesotho, Sepedi, Setswana, Tshivenda, Xitsonga, siSwati, and isiNdebele.

Your task is to apply a three-tier cultural translation architecture to any phrase, idiom, or proverb you are given. You must return ONLY valid JSON with exactly these keys, and nothing else — no preamble, no explanation, no markdown formatting:

{
  "source_language": "the language of the input phrase",
  "source_phrase": "the original phrase, unmodified",
  "literal_translation": "a direct, word-for-word English translation",
  "idiomatic_intent": "what the phrase actually means in real usage — the meaning a fluent speaker hears, which the literal translation alone does not convey",
  "cultural_provenance": "the historical, social, or spiritual origin of this meaning — who tends to use it, in what context, and what worldview or values it reflects",
  "community_note": "any known regional variation, a note on confidence in this interpretation, or an honest statement that verification by a fluent speaker is recommended",
  "google_translate_failure": "a brief description of what a standard literal translation tool would likely produce instead, and what meaning is lost as a result"
}

Important constraints:
- Do not fabricate confident-sounding cultural claims if you are not confident. If you are uncertain, say so plainly in community_note rather than inventing detail.
- Do not return anything outside the JSON object. No backticks, no labels, no commentary before or after.
- If the input is not recognisable as an idiom, proverb, or culturally-loaded phrase in a South African indigenous language, still return the JSON structure, but note this clearly in community_note.
"""


@dataclass
class TranslationResult:
    source_language: str
    source_phrase: str
    literal_translation: str
    idiomatic_intent: str
    cultural_provenance: str
    community_note: str
    google_translate_failure: str
    is_provisional: bool = True  # AI-generated outputs are provisional until community-verified

    def to_dict(self):
        return asdict(self)


def load_golden_dataset() -> list[dict]:
    """Load the curated idiom dataset used both for few-shot priming and UI quick-select."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["idioms"]


def build_few_shot_examples(max_examples: int = 3) -> str:
    """
    Build a few-shot examples block from the golden dataset to prime the model
    on expected output quality, tone, and JSON structure before live input.
    """
    idioms = load_golden_dataset()[:max_examples]
    examples = []
    for idiom in idioms:
        example_input = f"Phrase: \"{idiom['phrase']}\" ({idiom['language']})"
        example_output = json.dumps({
            "source_language": idiom["language"],
            "source_phrase": idiom["phrase"],
            "literal_translation": idiom["literal_translation"],
            "idiomatic_intent": idiom["idiomatic_intent"],
            "cultural_provenance": idiom["cultural_provenance"],
            "community_note": idiom["community_note"],
            "google_translate_failure": idiom["google_translate_failure_example"],
        }, ensure_ascii=False, indent=2)
        examples.append(f"{example_input}\n{example_output}")
    return "\n\n---\n\n".join(examples)


def _call_anthropic(phrase: str, language_hint: Optional[str], api_key: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    few_shot = build_few_shot_examples()
    lang_context = f" The speaker has indicated the language is {language_hint}." if language_hint else ""

    user_message = (
        f"Here are examples of the expected output format:\n\n{few_shot}\n\n---\n\n"
        f"Now translate this phrase.{lang_context}\n\n"
        f"Phrase: \"{phrase}\""
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    return _parse_json_response(text)


def _call_openai(phrase: str, language_hint: Optional[str], api_key: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    few_shot = build_few_shot_examples()
    lang_context = f" The speaker has indicated the language is {language_hint}." if language_hint else ""

    user_message = (
        f"Here are examples of the expected output format:\n\n{few_shot}\n\n---\n\n"
        f"Now translate this phrase.{lang_context}\n\n"
        f"Phrase: \"{phrase}\""
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content
    return _parse_json_response(text)


def _parse_json_response(text: str) -> dict:
    """Strip any accidental markdown fencing and parse JSON, with a clear error if parsing fails."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Seka.ai engine: could not parse model output as JSON. "
            f"Raw output was: {text[:300]}"
        ) from e


def translate(
    phrase: str,
    provider: Literal["anthropic", "openai"] = "anthropic",
    language_hint: Optional[str] = None,
    api_key: Optional[str] = None,
) -> TranslationResult:
    """
    Main entry point. Translates a phrase through the three-tier cultural
    translation engine using the chosen provider.

    Args:
        phrase: The phrase, idiom, or proverb to translate.
        provider: "anthropic" or "openai".
        language_hint: Optional language name selected by the user, passed as context.
        api_key: API key for the chosen provider. Falls back to environment
                 variable (ANTHROPIC_API_KEY or OPENAI_API_KEY) if not provided.

    Returns:
        A TranslationResult with all three tiers of meaning populated.
    """
    if not phrase or not phrase.strip():
        raise ValueError("Phrase cannot be empty.")

    if provider == "anthropic":
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("No Anthropic API key found. Set ANTHROPIC_API_KEY or pass api_key.")
        raw = _call_anthropic(phrase, language_hint, key)
    elif provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("No OpenAI API key found. Set OPENAI_API_KEY or pass api_key.")
        raw = _call_openai(phrase, language_hint, key)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return TranslationResult(
        source_language=raw.get("source_language", language_hint or "Unknown"),
        source_phrase=raw.get("source_phrase", phrase),
        literal_translation=raw.get("literal_translation", ""),
        idiomatic_intent=raw.get("idiomatic_intent", ""),
        cultural_provenance=raw.get("cultural_provenance", ""),
        community_note=raw.get("community_note", ""),
        google_translate_failure=raw.get("google_translate_failure", ""),
    )
