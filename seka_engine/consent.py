"""
Seka.ai Consent State Manager
--------------------------------
Tracks which WhatsApp senders are currently mid-consent-flow
(i.e. they received a translation and we're waiting for their yes/no).

Uses a simple in-memory dict for the prototype. In production this
would be Redis or a database so state survives server restarts.

Key design decision: we hold the translation result in memory ONLY
until the sender responds. Nothing is written to the registry until
they explicitly say yes. This is the POPIA-compliant consent gate.
"""

from seka_engine.engine import TranslationResult
from typing import Optional

# In-memory state stores
# Key: sender WhatsApp number (e.g. "whatsapp:+27821234567")
_awaiting_consent: set[str] = set()
_pending_translations: dict[str, TranslationResult] = {}


def is_awaiting_consent(sender: str) -> bool:
    """Return True if this sender is mid-consent-flow."""
    return sender in _awaiting_consent


def set_awaiting_consent(sender: str) -> None:
    """Mark this sender as awaiting a consent response."""
    _awaiting_consent.add(sender)


def clear_consent_state(sender: str) -> None:
    """Clear consent state for this sender (after they respond)."""
    _awaiting_consent.discard(sender)
    _pending_translations.pop(sender, None)


def set_pending_translation(sender: str, result: TranslationResult) -> None:
    """Store the translation result while waiting for consent."""
    _pending_translations[sender] = result


def get_pending_translation(sender: str) -> Optional[TranslationResult]:
    """Retrieve the pending translation for this sender."""
    return _pending_translations.get(sender)
