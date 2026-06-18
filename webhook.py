"""
Seka.ai WhatsApp Webhook Server
---------------------------------
Receives incoming WhatsApp messages via Twilio, runs them through
the Seka.ai cultural translation engine, logs to the community
registry (with consent), and replies to the sender on WhatsApp.

Run alongside app.py — this is a separate Flask server, not Streamlit.

Start with:
    python webhook.py

Then expose publicly with ngrok:
    ngrok http 5000
    (paste the https URL into your Twilio WhatsApp sandbox webhook field)
"""

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from seka_engine.engine import translate
from seka_engine.registry import log_entry
from seka_engine.consent import (
    is_awaiting_consent,
    set_awaiting_consent,
    clear_consent_state,
    get_pending_translation,
    set_pending_translation,
)
from seka_engine.reply_formatter import format_translation_reply, format_consent_request

app = Flask(__name__)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """
    Main webhook endpoint. Twilio POSTs here every time a WhatsApp
    message arrives on your sandbox number.
    """
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")         # e.g. "whatsapp:+27821234567"
    num_media = int(request.form.get("NumMedia", 0))
    media_url = request.form.get("MediaUrl0", "") if num_media > 0 else ""
    media_type = request.form.get("MediaContentType0", "") if num_media > 0 else ""

    resp = MessagingResponse()

    # ---------------------------------------------------------------
    # CONSENT FLOW: if this sender is waiting to confirm consent
    # ---------------------------------------------------------------
    if is_awaiting_consent(sender):
        reply = _handle_consent_response(sender, incoming_msg)
        resp.message(reply)
        return str(resp)

    # ---------------------------------------------------------------
    # VOICE NOTE: transcribe and translate
    # ---------------------------------------------------------------
    if num_media > 0 and "audio" in media_type:
        phrase, language_hint = _transcribe_voice_note(media_url, media_type)
        if not phrase:
            resp.message(
                "Seka.ai received your voice note but could not transcribe it clearly. "
                "Please try again, or type the phrase directly as a text message."
            )
            return str(resp)
    # ---------------------------------------------------------------
    # TEXT MESSAGE: use directly as the phrase
    # ---------------------------------------------------------------
    elif incoming_msg:
        phrase = incoming_msg
        language_hint = None
    else:
        resp.message(
            "Seka.ai is listening. Send a proverb, idiom, or phrase in any South "
            "African indigenous language — as a voice note or typed text — and I "
            "will unpack its cultural meaning for you."
        )
        return str(resp)

    # ---------------------------------------------------------------
    # TRANSLATE
    # ---------------------------------------------------------------
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        result = translate(
            phrase=phrase,
            provider="anthropic",
            language_hint=language_hint,
            api_key=api_key,
        )
    except Exception as e:
        resp.message(
            f"Seka.ai could not process that phrase right now: {str(e)[:120]}. "
            "Please try again in a moment."
        )
        return str(resp)

    # ---------------------------------------------------------------
    # STORE PENDING TRANSLATION + ASK FOR CONSENT
    # ---------------------------------------------------------------
    set_pending_translation(sender, result)
    set_awaiting_consent(sender)

    consent_request = format_consent_request(result)
    resp.message(consent_request)
    return str(resp)


def _handle_consent_response(sender: str, message: str) -> str:
    """
    Handle a yes/no consent reply from a sender who just received a translation.
    """
    result = get_pending_translation(sender)
    clear_consent_state(sender)

    if not result:
        return "Something went wrong — I lost track of your translation. Please send the phrase again."

    affirmative = {"yes", "ya", "yebo", "ewe", "ee", "jo", "ehe", "y", "1", "ok", "sure"}
    negative = {"no", "nope", "n", "2", "nah", "hayibo", "aikona"}

    response_lower = message.lower().strip().rstrip(".")

    if response_lower in affirmative:
        try:
            entry = log_entry(
                source_language=result.source_language,
                source_phrase=result.source_phrase,
                literal_translation=result.literal_translation,
                idiomatic_intent=result.idiomatic_intent,
                cultural_provenance=result.cultural_provenance,
                consent_given=True,
                contributor_attribution=None,  # always anonymous via WhatsApp
            )
            return (
                f"✅ Thank you. Your contribution has been added to the Seka.ai "
                f"community registry (entry {entry.entry_id}).\n\n"
                "Your voice is now part of the archive. 🌍"
            )
        except Exception as e:
            return f"Your consent was noted, but logging failed: {str(e)[:80]}. Please try again."

    elif response_lower in negative:
        return (
            "Understood — your phrase was not saved. "
            "The translation was shown to you only and nothing was stored. "
            "Send another phrase any time."
        )
    else:
        # Unclear response — re-ask once
        set_pending_translation(sender, result)
        set_awaiting_consent(sender)
        return (
            "I didn't quite catch that. Please reply *Yes* to add your phrase to "
            "the community archive, or *No* to keep it private."
        )


def _transcribe_voice_note(media_url: str, media_type: str) -> tuple[str, str | None]:
    """
    Transcribe a voice note to text.

    For the hackathon prototype, this uses a simple approach:
    download the audio and use the OpenAI Whisper API if available,
    otherwise return an empty string so the caller can ask for text instead.

    In production, this would use a more robust pipeline (e.g. Azure
    Speech Services with South African language model support).
    """
    try:
        import requests
        import tempfile

        twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")

        audio_response = requests.get(
            media_url,
            auth=(twilio_account_sid, twilio_auth_token),
            timeout=30,
        )
        audio_response.raise_for_status()

        extension = "ogg" if "ogg" in media_type else "mp4"
        with tempfile.NamedTemporaryFile(suffix=f".{extension}", delete=False) as tmp:
            tmp.write(audio_response.content)
            tmp_path = tmp.name

        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )
            return transcript.text.strip(), None

        # If no Whisper key, return empty so caller handles gracefully
        return "", None

    except Exception:
        return "", None


if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", 5000))
    print(f"\n🌍 Seka.ai WhatsApp webhook running on port {port}")
    print(f"   Expose publicly with: ngrok http {port}")
    print("   Then paste the ngrok URL into your Twilio sandbox webhook field\n")
    app.run(debug=False, port=port)
