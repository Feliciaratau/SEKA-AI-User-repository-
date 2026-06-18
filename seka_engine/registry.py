"""
Seka.ai Community Registry (Mock)
------------------------------------
A lightweight, file-based mock of the community-verified idiom registry
described in the project's data governance model. In production this would
be a properly governed database (e.g. managed by a community trust or
academic partner) — for the hackathon prototype, a JSON file demonstrates
the same data shape and consent flow without needing real infrastructure.

Every record models the fields that matter for POPIA-aligned consent:
- explicit consent flag and timestamp
- optional, opt-in attribution (never required)
- verification status, defaulting to "pending" for any AI-generated entry
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional

REGISTRY_PATH = Path(__file__).parent.parent / "data" / "community_registry.json"


@dataclass
class RegistryEntry:
    entry_id: str
    timestamp: str
    source_language: str
    source_phrase: str
    literal_translation: str
    idiomatic_intent: str
    cultural_provenance: str
    contributor_attribution: Optional[str]  # None if anonymous — never required
    consent_given: bool
    verification_status: str  # "pending" | "community_verified" | "disputed"

    def to_dict(self):
        return asdict(self)


def _load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def _save_registry(entries: list[dict]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def log_entry(
    source_language: str,
    source_phrase: str,
    literal_translation: str,
    idiomatic_intent: str,
    cultural_provenance: str,
    consent_given: bool,
    contributor_attribution: Optional[str] = None,
) -> RegistryEntry:
    """
    Log a translation result to the community registry, but ONLY if consent
    was given. This mirrors the POPIA-aligned consent flow: nothing is
    persisted without an explicit, affirmative consent signal.
    """
    if not consent_given:
        raise PermissionError(
            "Cannot log entry without explicit consent. "
            "Seka.ai never persists a contribution without affirmative consent."
        )

    entry = RegistryEntry(
        entry_id=str(uuid.uuid4())[:8],
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_language=source_language,
        source_phrase=source_phrase,
        literal_translation=literal_translation,
        idiomatic_intent=idiomatic_intent,
        cultural_provenance=cultural_provenance,
        contributor_attribution=contributor_attribution,  # None = anonymous, by design
        consent_given=consent_given,
        verification_status="pending",  # all new entries start unverified
    )

    entries = _load_registry()
    entries.append(entry.to_dict())
    _save_registry(entries)
    return entry


def list_entries() -> list[dict]:
    """Return all logged entries, most recent first."""
    entries = _load_registry()
    return list(reversed(entries))


def remove_entry(entry_id: str) -> bool:
    """
    Remove an entry by ID. Models the POPIA right to withdraw consent —
    a contributor can request their entry be deleted at any time.
    """
    entries = _load_registry()
    filtered = [e for e in entries if e["entry_id"] != entry_id]
    if len(filtered) == len(entries):
        return False  # nothing was removed
    _save_registry(filtered)
    return True


def registry_stats() -> dict:
    """Quick summary stats for display in the UI sidebar."""
    entries = _load_registry()
    languages = {}
    for e in entries:
        lang = e["source_language"]
        languages[lang] = languages.get(lang, 0) + 1
    return {
        "total_entries": len(entries),
        "by_language": languages,
        "pending_verification": sum(1 for e in entries if e["verification_status"] == "pending"),
        "community_verified": sum(1 for e in entries if e["verification_status"] == "community_verified"),
    }
