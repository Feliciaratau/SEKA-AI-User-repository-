"""
Seka.ai WhatsApp Reply Formatter
-----------------------------------
Formats TranslationResult objects into WhatsApp-friendly text messages.

WhatsApp supports basic markdown:
  *bold*   _italic_   ```code```
Keep messages concise — long messages are hard to read on a phone screen.
"""

from seka_engine.engine import TranslationResult


def format_translation_reply(result: TranslationResult) -> str:
    """
    Format the three-tier translation as a readable WhatsApp message.
    Keeps it warm and human — not a data dump.
    """
    lines = [
        f"🌍 *Seka.ai — Cultural Translation*\n",
        f"*Phrase:* _{result.source_phrase}_",
        f"*Language:* {result.source_language}\n",
        f"📖 *Literal:*\n{result.literal_translation}\n",
        f"💬 *What it really means:*\n{result.idiomatic_intent}\n",
        f"🌱 *Where this comes from:*\n{result.cultural_provenance}\n",
    ]

    if result.community_note:
        lines.append(f"_Note: {result.community_note}_\n")

    lines.append(
        "⚠️ _This is AI-generated and provisional — not yet community-verified._"
    )

    return "\n".join(lines)


def format_consent_request(result: TranslationResult) -> str:
    """
    Sends the translation result AND asks for consent to log it,
    in a single WhatsApp message. Combines both to reduce back-and-forth.
    """
    translation_section = format_translation_reply(result)

    consent_section = (
        "\n─────────────────────\n"
        "🗂️ *Would you like to add this to the Seka.ai community archive?*\n\n"
        "Your contribution helps preserve this knowledge for future generations. "
        "Your number will never be stored — contributions are anonymous.\n\n"
        "Reply *Yes* to contribute · *No* to keep it private"
    )

    return translation_section + consent_section


def format_welcome_message() -> str:
    """Sent when someone messages the number for the first time or sends 'hi'."""
    return (
        "👋 *Welcome to Seka.ai*\n\n"
        "I unpack the cultural meaning of South African indigenous language "
        "phrases — not just what the words say, but what they *mean* and "
        "where that meaning comes from.\n\n"
        "Send me a proverb, idiom, or phrase in:\n"
        "isiZulu · isiXhosa · Sepedi · Sesotho · Setswana · Tshivenda · "
        "Xitsonga · siSwati · isiNdebele\n\n"
        "Type it as a message, or send a 🎤 voice note.\n\n"
        "_Built for the AADHIH Reclaiming African Voices Hackathon_"
    )
