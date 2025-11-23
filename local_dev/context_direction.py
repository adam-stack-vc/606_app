import spacy, json, re
from dataclasses import dataclass, field
from typing import Optional, Dict, List

nlp = spacy.load("en_core_web_sm")

# ---- Load enriched grouped dictionary (Option 2) ----
with open("direction_map.json") as f:
    DIRECTION_MAP = json.load(f)

def get_direction_for_verb(verb: str):
    for direction, cfg in DIRECTION_MAP.items():
        if verb.lower() in cfg["verbs"]:
            return {
                "direction": direction,
                "subject_role": cfg["subject_role"],
                "object_role": cfg["object_role"],
                "implied_metric": cfg.get("implied_metric"),
            }
    return None


def disambiguate_context(user_input: str, tags: dict, debug: bool=False) -> dict:
    """Infer direction, metric, and entities (active or passive voice)."""
    text = user_input.lower()
    doc = nlp(text)

    # Optional debug parse tree
    if debug:
        print("\n--- spaCy Dependency Parse ---")
        for tok in doc:
            print(f"{tok.text:15s} {tok.dep_:15s} -> {tok.head.text}")
        print("------------------------------\n")

    direction_info = None
    for token in doc:
        direction_info = get_direction_for_verb(token.lemma_)
        if direction_info:
            tags["direction"] = direction_info["direction"]
            tags["subject_role"] = direction_info["subject_role"]
            tags["object_role"]  = direction_info["object_role"]
            tags["metric"] = direction_info.get("implied_metric")
            break

    # ----- Passive voice detection -----
    agent, recipient = None, None
    for tok in doc:
        if tok.dep_ == "agent":          # 'by Robinhood'
            for child in tok.children:
                if child.dep_ == "pobj":
                    agent = child.text
        elif tok.dep_ == "pobj" and tok.head.text.lower() in ["to", "from"]:
            recipient = tok.text
        elif tok.dep_ in ["dobj", "pobj"] and tok.head.lemma_ in ["pay", "send"]:
            recipient = tok.text

    if agent or recipient:
        if debug:
            print(f"Detected entities → agent:{agent}, recipient:{recipient}")

    # Assign based on direction
    if direction_info:
        subj_role = direction_info["subject_role"]
        obj_role  = direction_info["object_role"]
        if direction_info["direction"] == "executing_bd_to_venue":
            tags["executing_bd"] = agent or recipient if subj_role == "executing_bd" else agent
            tags["venue"] = recipient or agent if obj_role == "venue" else recipient
        elif direction_info["direction"] == "venue_to_executing_bd":
            tags["venue"] = agent or recipient if subj_role == "venue" else recipient
            tags["executing_bd"] = recipient or agent if obj_role == "executing_bd" else agent

    # ----- Metric fallback -----
    if not tags.get("metric"):
        if any(k in text for k in ["orders", "most orders", "routed"]):
            tags["metric"] = "volume"
        elif any(k in text for k in ["payment", "pfof", "rebate", "paid"]):
            tags["metric"] = "pfof"
        elif "rate" in text or "cents per" in text:
            tags["metric"] = "rate"

    # ----- Direction fallback -----
    if not tags.get("direction"):
        tags["direction"] = (
            "venue_to_executing_bd" if tags.get("metric") == "pfof"
            else "executing_bd_to_venue"
        )

    return tags
