"""Keyword stand-in for the smart-home demo.

This is not Jev. It returns the same answer shape so the house moves with
no API key. ``plan()`` does not know which one produced the answers.
"""

from __future__ import annotations

import re
from typing import Any

from jev_lab.home_catalog import NONE, all_devices


def split_request(request: str) -> list[str]:
    parts = re.split(
        r"\s*(?:[.;!?]+\s*|,?\s+and\s+(?:then\s+)?|,\s*then\s+|\boh,?\s*)",
        request,
        flags=re.I,
    )
    out: list[str] = []
    for part in parts:
        cleaned = re.sub(r"^(and|also|oh|then|can you)\b[,\s]*", "", part.strip(), flags=re.I)
        cleaned = cleaned.strip(" .")
        if len(cleaned.split()) >= 2:
            out.append(cleaned[0].upper() + cleaned[1:] if cleaned else cleaned)
    return out or [request]


def general_reply(request: str) -> str:
    lower = request.lower()
    if "world series" in lower and "1989" in lower:
        return "The Oakland Athletics beat the San Francisco Giants in 1989."
    return (
        "That isn't a home command. In the live demo a generative model would answer; "
        "Jev only classified it as general."
    )


def _choice(winner: str, options: list[str], confidence: float = 0.86) -> dict[str, Any]:
    if winner not in options:
        winner = options[0]
    leftover = max(0.0, 1.0 - 0.72)
    others = [option for option in options if option != winner]
    share = leftover / len(others) if others else 0.0
    probs = {option: (0.72 if option == winner else share) for option in options}
    total = sum(probs.values()) or 1.0
    probs = {key: round(value / total, 4) for key, value in probs.items()}
    return {
        "type": "choice",
        "choice": winner,
        "probabilities": probs,
        "confidence": round(confidence, 4),
    }


def _noul(p: float) -> dict[str, Any]:
    return {"type": "noul", "noul": round(min(1.0, max(0.0, p)), 4)}


def mock_answers(
    request: str,
    home: dict[str, Any],
    speaking_to: str | None,
    questions: dict[str, Any],
) -> dict[str, Any]:
    """Keyword stand-in so the house demo runs with no API key.

    ``speaking_to`` is part of the live state. The keyword parser reads the
    utterance only, so the argument is accepted and ignored.
    """
    text = request.lower()
    rooms = [room["id"] for room in home["rooms"]]
    devices = all_devices(home)
    device_ids = [device["id"] for device in devices]

    general_cues = (
        "who won",
        "world series",
        "what is",
        "tell me",
        "joke",
        "capital of",
        "weather in",
    )
    status_cues = text.startswith("is ") or text.startswith("are ") or "is the" in text and text.endswith("?")

    if any(cue in text for cue in general_cues):
        category = "general"
    elif status_cues:
        category = "status_question"
    else:
        category = "command"

    compound_split = split_request(request)
    is_compound = (
        0.92 if len(compound_split) >= 2 and "all the" not in text and "whole house" not in text else 0.04
    )

    if any(word in text for word in ("lock", "unlock", "lock up", "secure")):
        dtype = "lock"
    elif any(word in text for word in ("music", "speaker", "audio", "song", "podcast")):
        dtype = "speaker"
    elif "fan" in text:
        dtype = "fan"
    elif any(word in text for word in ("coffee", "kettle", "boil", "brew")):
        dtype = "appliance"
    elif any(word in text for word in ("heat", "thermostat", "a/c", "ac on", "cool the")) and "fan" not in text:
        dtype = "thermostat"
    else:
        dtype = "light"

    outdoor = any(word in text for word in ("outside", "outdoor", "patio"))
    has_outdoor = any(device["room"] == "patio" for device in devices)
    available = 0.08 if outdoor and not has_outdoor else 0.94

    whole = any(word in text for word in ("all the", "whole house", "everywhere", "lock up"))
    scope = "whole_house" if whole else "specific"

    room = NONE
    room_map = [
        (("kid", "maya", "child"), "kids_room"),
        (("outside", "outdoor", "patio"), "patio"),
        (("living",), "living_room"),
        (("kitchen",), "kitchen"),
        (("primary", "master"), "primary_bedroom"),
        (("bedroom", "bed "), "bedroom"),
        (("office", "desk"), "office"),
        (("garage", "entry", "front door"), "entry"),
    ]
    for needles, room_id in room_map:
        if any(needle in text for needle in needles) and room_id in rooms:
            room = room_id
            break
        if any(needle in text for needle in needles) and room_id == "bedroom" and "primary_bedroom" in rooms:
            room = "primary_bedroom"
            break
    if room == "bedroom" and "bedroom" not in rooms and "primary_bedroom" in rooms:
        room = "primary_bedroom"

    device = NONE
    name_map = [
        ("floor lamp", "living_room_lamp"),
        ("overhead", "living_room_overhead"),
        ("coffee", "kitchen_coffee_maker"),
        ("kettle", "kitchen_kettle"),
        ("desk", "office_light"),
        ("night light", "kids_room_light"),
        ("story", "kids_room_speaker"),
        ("string", "patio_lights"),
        ("outdoor", "patio_speakers"),
        ("front door", "front_door_lock"),
        ("garage", "garage_door_lock"),
    ]
    for needle, device_id in name_map:
        if needle in text and device_id in device_ids:
            device = device_id
            break

    lock_action = "unlock" if "unlock" in text else "lock"
    if any(word in text for word in ("off", "shut", "stop", "silence", "kill")):
        power = "turn_off"
    elif "dim" in text:
        power = "dim"
    elif "bright" in text:
        power = "brighten"
    else:
        power = "turn_on"
    if "heat" in text:
        climate = "heat_on"
    elif any(word in text for word in ("cool", "a/c", "ac")):
        climate = "ac_on"
    else:
        climate = "turn_off" if power == "turn_off" else "ac_on"

    answers: dict[str, Any] = {}
    for question_id, spec in questions.items():
        question_type = spec["type"]
        if question_id == "category":
            answers[question_id] = _choice(
                category, list(spec["criteria"]), 0.9 if category != "command" else 0.84
            )
        elif question_id == "is_compound":
            answers[question_id] = _noul(is_compound)
        elif question_id == "scope":
            answers[question_id] = _choice(scope, list(spec["criteria"]), 0.8 if whole else 0.7)
        elif question_id == "available":
            answers[question_id] = _noul(available)
        elif question_id == "device_type":
            answers[question_id] = _choice(dtype, list(spec["criteria"]), 0.82)
        elif question_id == "room":
            answers[question_id] = _choice(room, list(spec["criteria"]), 0.75 if room != NONE else 0.55)
        elif question_id == "device":
            answers[question_id] = _choice(device, list(spec["criteria"]), 0.72 if device != NONE else 0.6)
        elif question_id == "action.light":
            answers[question_id] = _choice(power if power in spec["criteria"] else "turn_on", list(spec["criteria"]))
        elif question_id == "action.fan":
            answers[question_id] = _choice(
                "turn_off" if power == "turn_off" else "turn_on", list(spec["criteria"])
            )
        elif question_id == "action.speaker":
            answers[question_id] = _choice(
                "turn_off" if power == "turn_off" else "turn_on", list(spec["criteria"])
            )
        elif question_id == "action.thermostat":
            answers[question_id] = _choice(
                climate if climate in spec["criteria"] else "ac_on", list(spec["criteria"])
            )
        elif question_id == "action.appliance":
            answers[question_id] = _choice(
                "turn_off" if power == "turn_off" else "turn_on", list(spec["criteria"])
            )
        elif question_id == "action.lock":
            answers[question_id] = _choice(lock_action, list(spec["criteria"]), 0.88)
        elif question_type == "noul":
            answers[question_id] = _noul(0.1)
        else:
            keys = list(spec.get("criteria") or {})
            answers[question_id] = _choice(keys[0], keys, 0.4) if keys else _choice(NONE, [NONE], 0.4)
    return answers
