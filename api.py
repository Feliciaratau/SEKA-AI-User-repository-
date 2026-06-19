from flask import Flask, request, jsonify
from seka_engine.engine import translate
import os

app = Flask(__name__)


@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json() or {}
    phrase = data.get("phrase", "")
    language_hint = data.get("language_hint")
    if not phrase:
        return jsonify({"error": "phrase required"}), 400
    try:
        # Use provider from env or default to anthropic
        provider = os.environ.get("SEKA_PROVIDER", "anthropic")
        result = translate(
            phrase=phrase,
            provider=provider,
            language_hint=language_hint,
            api_key=None,
        )
        return jsonify({
            "source_language": result.source_language,
            "source_phrase": result.source_phrase,
            "literal_translation": result.literal_translation,
            "idiomatic_intent": result.idiomatic_intent,
            "cultural_provenance": result.cultural_provenance,
            "community_note": result.community_note,
        })
    except Exception as e:
        msg = str(e)
        # If keys are missing locally, return a mock example so the portal can be tested
        if "No Anthropic API key" in msg or "No OpenAI" in msg or "No API key" in msg:
            return jsonify({
                "source_language": "IsiXhosa",
                "source_phrase": phrase,
                "literal_translation": "Hands wash each other",
                "idiomatic_intent": "People help each other; mutual assistance",
                "cultural_provenance": "Common proverb in Xhosa emphasizing communal support.",
                "community_note": "Used to encourage cooperation and reciprocity in communities.",
            }), 200
        return jsonify({"error": msg}), 500


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5001))
    print(f"Starting local Seka.ai translate API on port {port}")
    app.run(host="0.0.0.0", port=port)
