"""Guppy v0.0 — deterministic rule baseline. No model. Exists so the eval
harness has a floor to beat and runs with no API key.
"""
from __future__ import annotations

import re

VERSION = "v0.0-rules"


def respond(rec: dict) -> str:
    inp = rec["input"].lower()
    itype = rec.get("input_type", "command")
    if itype == "event":
        return "[Contact. Unidentified object detected]"
    if re.search(r"\b(status|report|diagnostic)\b", inp):
        return "[All systems nominal]"
    if re.search(r"\b(how long|eta|how far|when will)\b", inp):
        return "[Estimated time: unknown]"
    if re.search(r"\b(can you|identify|is there)\b", inp):
        return "[Negative]"
    if re.search(r"\b(what are you|your name)\b", inp):
        return "[General Unit Primary Peripheral Interface]"
    if re.search(r"\b(launch|fire|deploy)\b", inp):
        return "[Launching]"
    if itype == "banter" and "thinks" in inp:
        return "[3 hours]"
    if itype == "banter":
        return "[Query: clarify]"
    return "[Acknowledged]"
