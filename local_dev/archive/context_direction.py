import json
import re
from dataclasses import dataclass, field  # kept for potential future use
from typing import Optional, Dict, List

# Try to import spaCy, but don't fail hard if unavailable
try:  # pragma: no cover - optional dependency
    import spacy  # type: ignore
    _NLP = spacy.load("en_core_web_sm")
except Exception:  # pragma: no cover
    spacy = None
    _NLP = None

# Load direction mapping
with open("direction_map.json") as f:
    DIRECTION_MAP = json.load(f)


def get_direction_for_verb(verb: str):
    """Lookup direction info for a given verb based on the direction map."""
    v = verb.lower()
    for direction, cfg in DIRECTION_MAP.items():
        if v in cfg.get("verbs", []):
            return {
                "direction": direction,
                "subject_role": cfg.get("subject_role"),
                "object_role": cfg.get("object_role"),
                "implied_time": cfg.get("implied_time"),
                "implied_metric": cfg.get("implied_metric"),
            }
    return None


def disambiguate(user_input: str, tags: dict, debug: bool = False) -> dict:
    """
    Infer direction, roles, and metric using spaCy if available; otherwise fall back
    to simple keyword heuristics. Updates and returns the provided tags dict.
    """
    text = (user_input or "").lower()

    # First, try spaCy if available
    if _NLP is not None:
        doc = _NLP(text)
        if debug:  # pragma: no cover
            print("\n--- Dependency Parse ---")
            for tok in doc:
                print(f"{tok.text:12s} {tok.dep_:12s} -> {tok.head.text}")
            print("------------------------\n")

        info = None
        for token in doc:  # look for governing verb that matches our map
            info = get_direction_for_verb(token.lemma_)
            if info:
                tags["direction"] = info.get("direction")
                if info.get("subject_role"):
                    tags["subject_role"] = info.get("subject_role")
                if info.get("object_role"):
                    tags["object_role"] = info.get("object_role")
                if info.get("implied_metric") and not tags.get("metric"):
                    tags["metric"] = info.get("implied_metric")
                break

        # crude agent/recipient extraction
        agent = None
        recipient = None
        for tok in doc:
            if tok.dep_ == "agent":
                for child in tok.children:
                    if child.dep_ == "pobj":
                        agent = child.text
            if tok.dep_ == "pobj" and tok.head.text.lower() in ("to", "from"):
                recipient = tok.text
            if tok.dep_ in ("dobj", "pobj") and tok.head.lemma_ in ("send", "pay"):
                recipient = tok.text
        if info:
            if info.get("direction") == "executing_bd_to_venue":
                if agent:
                    tags["executing_bd"] = tags.get("executing_bd") or agent
                if recipient:
                    tags["venue"] = tags.get("venue") or recipient
            elif info.get("direction") == "venue_to_executing_bd":
                if agent:
                    tags["venue"] = tags.get("venue") or agent
                if recipient:
                    tags["executing_bd"] = tags.get("executing_bd") or recipient
    else:
        # Fallback heuristics when spaCy isn't available
        if not tags.get("metric"):
            if any(k in text for k in ["order", "orders", "routed", "volume"]):
                tags["metric"] = "volume"
            elif any(k in text for k in ["pfof", "payment", "rebate"]):
                tags["metric"] = "pfof"
            elif "rate" in text or "cents per" in text:
                tags["metric"] = "rate"
        if not tags.get("direction"):
            tags["direction"] = "venue_to_executing_bd" if "pfof" in text else "executing_bd_to_venue"

    # Derive default direction if still missing
    if not tags.get("direction"):
        tags["direction"] = "venue_to_executing_bd" if tags.get("metric") == "pfof" else "executing_bd_to_venue"

    return tags
