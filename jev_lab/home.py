"""Smart-home dispatcher: speculative fan-out, then code acts.

Mirrors TypeSafe's public smart-home demo
(https://docs.typesafe.ai/demos/smart-home): one request asks every
question the app might need, including per-device-type actions that are
irrelevant for most utterances. `plan()` reads only the answers its
branch needs.
"""

from __future__ import annotations

import copy
import re
from typing import Any

NONE = "none_of_these"

ACTIONS: dict[str, dict[str, Any]] = {
    "light": {
        "label": "lights",
        "criteria": {
            "turn_on": "Switch the lights on",
            "turn_off": "Switch the lights off",
            "dim": "Make the lights dimmer or softer, but keep them on",
            "brighten": "Make the lights brighter or full brightness",
        },
    },
    "fan": {
        "label": "fans",
        "criteria": {"turn_on": "Start the fans", "turn_off": "Stop the fans"},
    },
    "speaker": {
        "label": "speakers",
        "criteria": {
            "turn_on": "Start playing music or audio",
            "turn_off": "Stop, pause, or silence the music or audio",
        },
    },
    "thermostat": {
        "label": "thermostats",
        "criteria": {
            "turn_off": "Turn heating and cooling off",
            "ac_on": "Cool the space: air conditioning on",
            "heat_on": "Warm the space: heating on",
        },
    },
    "appliance": {
        "label": "appliances",
        "criteria": {
            "turn_on": "Start the appliance (brew, boil, run)",
            "turn_off": "Stop or switch off the appliance",
        },
    },
    "lock": {
        "label": "locks",
        "criteria": {
            "lock": "Lock or secure the door",
            "unlock": "Unlock or open the door",
        },
    },
}

RISKY = {"lock.unlock"}

QUESTION_LABELS = {
    "category": "What category of request is this?",
    "is_compound": "Is this more than one distinct action?",
    "scope": "What domain is this request targeting?",
    "available": "Does this home have a matching device?",
    "device_type": "What type of device is this request targeting?",
    "room": "Which room is the user referring to?",
    "device": "Which specific device should receive the command?",
}

EXAMPLES = [
    "Turn on the living room lights",
    "Turn off all the lights",
    "Turn on my kid's light",
    "Is the kitchen light on?",
    "Shut off all the music in the house",
    "Get the coffee boiling",
    "Let's get some outside music going",
    "It's going to be a hot day — turn on all the fans",
    "Turn off the kitchen lights and lock the office door",
    "Lock up the whole house",
    "Set the bedroom to heat",
    "Who won the World Series in 1989?",
    "Turn on the living room lights and turn off the kitchen. Oh, and can you get the coffee started?",
]

ICON = {
    "light": "💡",
    "fan": "🌀",
    "speaker": "🔊",
    "appliance": "☕",
    "lock": "🔒",
    "thermostat": "🌡️",
}
ROOM_ICON = {
    "living_room": "🛋️",
    "kitchen": "🍳",
    "bedroom": "🛏️",
    "primary_bedroom": "🛏️",
    "kids_room": "🧸",
    "office": "🖥️",
    "patio": "🌿",
    "entry": "🚪",
}


def _light(id: str, name: str, on: bool = False, brightness: int = 100) -> dict[str, Any]:
    return {"id": id, "name": name, "type": "light", "on": on, "brightness": brightness}


def _fan(id: str, name: str, on: bool = False) -> dict[str, Any]:
    return {"id": id, "name": name, "type": "fan", "on": on}


def _speaker(id: str, name: str, on: bool = False) -> dict[str, Any]:
    return {"id": id, "name": name, "type": "speaker", "on": on}


def _appliance(id: str, name: str, on: bool = False) -> dict[str, Any]:
    return {"id": id, "name": name, "type": "appliance", "on": on}


def _lock(id: str, name: str, locked: bool = True) -> dict[str, Any]:
    return {"id": id, "name": name, "type": "lock", "locked": locked}


def _thermostat(id: str, name: str, mode: str = "off", target: int = 72) -> dict[str, Any]:
    return {"id": id, "name": name, "type": "thermostat", "mode": mode, "target": target}


HOMES: dict[str, dict[str, Any]] = {
    "1br": {
        "id": "1br",
        "label": "1BR (10 devices)",
        "rooms": [
            {
                "id": "living_room",
                "name": "Living Room",
                "devices": [
                    _light("living_room_overhead", "Overhead Lights", True, 80),
                    _light("living_room_lamp", "Floor Lamp"),
                    _fan("living_room_fan", "Ceiling Fan"),
                    _speaker("living_room_speaker", "Smart Speaker"),
                ],
            },
            {
                "id": "kitchen",
                "name": "Kitchen",
                "devices": [
                    _light("kitchen_light", "Kitchen Lights", True, 100),
                    _appliance("kitchen_coffee_maker", "Coffee Maker"),
                ],
            },
            {
                "id": "bedroom",
                "name": "Bedroom",
                "devices": [
                    _light("bedroom_light", "Bedroom Light"),
                    _thermostat("bedroom_thermostat", "Thermostat", "ac", 72),
                ],
            },
            {
                "id": "office",
                "name": "Office",
                "devices": [
                    _light("office_light", "Desk Lamp", True, 90),
                    _lock("office_lock", "Door Lock", True),
                ],
            },
        ],
    },
    "family": {
        "id": "family",
        "label": "Family home (19 devices)",
        "rooms": [
            {
                "id": "living_room",
                "name": "Living Room",
                "devices": [
                    _light("living_room_overhead", "Overhead Lights", True, 80),
                    _light("living_room_lamp", "Floor Lamp"),
                    _fan("living_room_fan", "Ceiling Fan"),
                    _speaker("living_room_speaker", "Sonos Speaker"),
                    _thermostat("hallway_thermostat", "Main Thermostat", "off", 70),
                ],
            },
            {
                "id": "kitchen",
                "name": "Kitchen",
                "devices": [
                    _light("kitchen_light", "Kitchen Lights", True),
                    _appliance("kitchen_coffee_maker", "Coffee Maker"),
                    _appliance("kitchen_kettle", "Electric Kettle"),
                ],
            },
            {
                "id": "primary_bedroom",
                "name": "Primary Bedroom",
                "devices": [
                    _light("primary_bedroom_light", "Bedside Lamps"),
                    _fan("primary_bedroom_fan", "Ceiling Fan"),
                ],
            },
            {
                "id": "kids_room",
                "name": "Maya's Room (kid)",
                "devices": [
                    _light("kids_room_light", "Night Light"),
                    _fan("kids_room_fan", "Tower Fan"),
                    _speaker("kids_room_speaker", "Story Speaker"),
                ],
            },
            {
                "id": "office",
                "name": "Office",
                "devices": [
                    _light("office_light", "Desk Lamp", True, 60),
                    _lock("office_lock", "Door Lock", False),
                ],
            },
            {
                "id": "patio",
                "name": "Patio",
                "devices": [
                    _light("patio_lights", "String Lights"),
                    _speaker("patio_speakers", "Outdoor Speakers"),
                ],
            },
            {
                "id": "entry",
                "name": "Entry & Garage",
                "devices": [
                    _lock("front_door_lock", "Front Door", False),
                    _lock("garage_door_lock", "Garage Door", True),
                ],
            },
        ],
    },
}


def clone_home(home_id: str) -> dict[str, Any]:
    if home_id not in HOMES:
        raise KeyError(home_id)
    return copy.deepcopy(HOMES[home_id])


def overlay_house(home: dict[str, Any], snapshot: dict[str, Any] | None) -> dict[str, Any]:
    """Copy live on/brightness/lock/mode from a client snapshot onto a clone."""
    if not snapshot:
        return home
    by_id = {d["id"]: d for d in all_devices(snapshot)}
    for room in home["rooms"]:
        for device in room["devices"]:
            live = by_id.get(device["id"])
            if not live:
                continue
            for key in ("on", "brightness", "locked", "mode", "target"):
                if key in live:
                    device[key] = live[key]
    return home


def all_devices(home: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for room in home["rooms"]:
        for device in room["devices"]:
            out.append({**device, "room": room["id"]})
    return out


def describe(device: dict[str, Any]) -> str:
    kind = device["type"]
    if kind == "light":
        return f"On · {device.get('brightness', 100)}%" if device.get("on") else "Off"
    if kind == "fan":
        return "On" if device.get("on") else "Off"
    if kind == "speaker":
        return "Playing" if device.get("on") else "Off"
    if kind == "appliance":
        return "On" if device.get("on") else "Off"
    if kind == "lock":
        return "Locked" if device.get("locked") else "Unlocked"
    if kind == "thermostat":
        mode = device.get("mode") or "off"
        if mode == "off":
            return "Off"
        label = "A/C" if mode == "ac" else "Heat"
        return f"{label} · {device.get('target', 72)}°F"
    return ""


def is_active(device: dict[str, Any]) -> bool:
    if device["type"] == "lock":
        return bool(device.get("locked"))
    if device["type"] == "thermostat":
        return (device.get("mode") or "off") != "off"
    return bool(device.get("on"))


def find_device(home: dict[str, Any], device_id: str) -> dict[str, Any] | None:
    for room in home["rooms"]:
        for device in room["devices"]:
            if device["id"] == device_id:
                return device
    return None


def public_home(home: dict[str, Any]) -> dict[str, Any]:
    rooms = []
    for room in home["rooms"]:
        devices = []
        for device in room["devices"]:
            devices.append(
                {
                    **device,
                    "status": describe(device),
                    "active": is_active(device),
                    "icon": ICON.get(device["type"], "▫️"),
                }
            )
        rooms.append(
            {
                "id": room["id"],
                "name": room["name"],
                "icon": ROOM_ICON.get(room["id"], "▫️"),
                "devices": devices,
            }
        )
    return {"id": home.get("id"), "label": home.get("label"), "rooms": rooms}


def build_state(request: str, home: dict[str, Any], speaking_to: str | None) -> dict[str, Any]:
    devices = all_devices(home)
    ctx = next((d for d in devices if d["id"] == speaking_to), None)
    room_name = None
    if ctx:
        room_name = next(r["name"] for r in home["rooms"] if r["id"] == ctx["room"])
    return {
        "request": request,
        "speaking_to": (
            {"device": ctx["name"], "room": room_name}
            if ctx
            else "unknown (the user is not talking to a device in a particular room)"
        ),
        "home": [
            {
                "room": room["name"],
                "devices": [
                    {"name": d["name"], "type": d["type"], "status": describe(d)}
                    for d in room["devices"]
                ],
            }
            for room in home["rooms"]
        ],
    }


def build_questions(home: dict[str, Any]) -> dict[str, Any]:
    rooms = {r["id"]: r["name"] for r in home["rooms"]}
    devices = {
        d["id"]: f"{d['name']}: the {d['type']} in the {rooms[d['room']]}"
        for d in all_devices(home)
    }
    questions: dict[str, Any] = {
        "category": {
            "type": "choice",
            "instructions": "What category of request is `request`, given the smart home described in `home`?",
            "criteria": {
                "command": "Asks to change something in the home: switch, dim, play, stop, lock, heat, cool, or start a device",
                "status_question": "Asks about the current state of a device or room, without asking to change anything",
                "general": "General knowledge, conversation, or anything that is not about the devices in this home",
            },
        },
        "is_compound": {
            "type": "noul",
            "instructions": (
                "Does `request` ask for two or more distinct actions, such as different actions, "
                "device types, or rooms? One action applied to a group (\"turn off all the lights\") "
                "counts as a single action."
            ),
        },
        "scope": {
            "type": "choice",
            "instructions": "What domain of the home is `request` targeting?",
            "criteria": {
                "whole_house": 'Every matching device anywhere in the house: "all the lights", "the whole house", "everywhere"',
                "specific": "A particular room or a particular device",
            },
        },
        "available": {
            "type": "noul",
            "instructions": (
                "Is at least one device listed in `home` a match for what `request` asks for? "
                "Only the devices listed in `home` exist."
            ),
            "criteria": {
                "true": "A listed device matches the kind of device and the location the request asks for",
                "false": (
                    "The request needs a device or location that is not listed in `home`, "
                    "such as outdoor speakers in a home with no outdoor room"
                ),
            },
        },
        "device_type": {
            "type": "choice",
            "instructions": "What type of device is `request` about?",
            "criteria": {
                "light": "Lights and lamps",
                "fan": "Fans",
                "speaker": "Speakers, music, podcasts, audio",
                "thermostat": "Heating, cooling, air conditioning, temperature",
                "appliance": "Kitchen appliances such as a coffee maker or kettle",
                "lock": "Door locks, locking up, security",
            },
        },
        "room": {
            "type": "choice",
            "instructions": (
                "Which room of `home` is `request` referring to? If the request names no room or says "
                '"here", use the room in `speaking_to` when one is given. Answer none_of_these when no '
                "room of this home fits."
            ),
            "criteria": {**rooms, NONE: "No room in this home fits, or the request is not about one room"},
        },
        "device": {
            "type": "choice",
            "instructions": (
                "Which specific device in `home` should receive `request`? Answer none_of_these if the "
                "request is about a group of devices, or if no device in this home matches what the user describes."
            ),
            "criteria": {
                **devices,
                NONE: "A group of devices, or no device in this home matches",
            },
        },
    }
    for type_id, spec in ACTIONS.items():
        questions[f"action.{type_id}"] = {
            "type": "choice",
            "instructions": (
                f"Assume `request` is about {spec['label']}. "
                f"What should happen to the {spec['label']}?"
            ),
            "criteria": spec["criteria"],
        }
    return questions


def question_label(question_id: str) -> str:
    if question_id in QUESTION_LABELS:
        return QUESTION_LABELS[question_id]
    if question_id.startswith("action."):
        kind = question_id.split(".", 1)[1]
        return f"What should happen to the {ACTIONS.get(kind, {}).get('label', kind)}?"
    return question_id


def _min_confidence(answers: dict[str, Any], ids: list[str]) -> float:
    values: list[float] = []
    for qid in ids:
        ans = answers.get(qid) or {}
        if "confidence" in ans and ans["confidence"] is not None:
            values.append(float(ans["confidence"]))
    return min(values) if values else 1.0


def plan(
    answers: dict[str, Any],
    home: dict[str, Any],
    speaking_to: str | None = None,
) -> dict[str, Any]:
    devices = all_devices(home)
    used = ["category"]
    category = (answers.get("category") or {}).get("choice")

    if category == "general":
        return {
            "kind": "general",
            "used": used,
            "confidence": round(_min_confidence(answers, used), 4),
            "targets": [],
        }

    if category == "command" and float((answers.get("is_compound") or {}).get("noul") or 0) > 0.5:
        used = ["category", "is_compound"]
        return {
            "kind": "compound",
            "used": used,
            "confidence": round(_min_confidence(answers, used), 4),
            "targets": [],
        }

    used = ["category", "is_compound", "available", "scope", "device_type"]
    if float((answers.get("available") or {}).get("noul") or 0) < 0.5:
        return {
            "kind": "unavailable",
            "used": used,
            "confidence": round(_min_confidence(answers, used), 4),
            "targets": [],
            "message": "I don't see a device in this home that can do that.",
        }

    type_id = (answers.get("device_type") or {}).get("choice")
    device_id = (answers.get("device") or {}).get("choice")
    room_id = (answers.get("room") or {}).get("choice")
    context_room = next((d["room"] for d in devices if d["id"] == speaking_to), None)
    targets: list[dict[str, Any]] = []
    clarify = None
    scope = (answers.get("scope") or {}).get("choice")

    if scope == "whole_house":
        targets = [d for d in devices if d["type"] == type_id]
    else:
        used.append("device")
        if device_id and device_id != NONE:
            found = next((d for d in devices if d["id"] == device_id), None)
            if found:
                type_id = found["type"]
                targets = [found]
        else:
            used.append("room")
            room = room_id if room_id and room_id != NONE else context_room
            if room:
                targets = [d for d in devices if d["room"] == room and d["type"] == type_id]
            else:
                of_type = [d for d in devices if d["type"] == type_id]
                if len(of_type) == 1:
                    targets = of_type
                else:
                    label = ACTIONS.get(type_id or "", {}).get("label", "devices")
                    clarify = f"Which {label}? I couldn't tell which room you meant."

    slim = [{"id": t["id"], "name": t["name"], "type": t["type"], "room": t["room"]} for t in targets]
    if category == "status_question":
        return {
            "kind": "status",
            "used": used,
            "confidence": round(_min_confidence(answers, used), 4),
            "targets": slim,
            "type": type_id,
            "clarify": clarify,
        }

    action_q = f"action.{type_id}"
    used.append(action_q)
    action = (answers.get(action_q) or {}).get("choice")
    confidence = _min_confidence(answers, used)
    threshold = 0.85 if f"{type_id}.{action}" in RISKY else 0.5
    return {
        "kind": "command",
        "used": used,
        "confidence": round(confidence, 4),
        "action": action,
        "needs_confirm": confidence < threshold,
        "threshold": threshold,
        "targets": slim,
        "type": type_id,
        "clarify": clarify,
    }


def apply_action(device: dict[str, Any], action: str) -> None:
    kind = device["type"]
    if kind == "light":
        if action == "turn_on":
            device["on"] = True
            device["brightness"] = device.get("brightness") or 100
        elif action == "turn_off":
            device["on"] = False
        elif action == "dim":
            device["on"] = True
            device["brightness"] = max(10, min(30, int(device.get("brightness") or 100) - 30))
        elif action == "brighten":
            device["on"] = True
            device["brightness"] = 100
    elif kind == "lock":
        device["locked"] = action == "lock"
    elif kind == "thermostat":
        device["mode"] = {"turn_off": "off", "ac_on": "ac", "heat_on": "heat"}.get(action, device.get("mode"))
    else:
        device["on"] = action == "turn_on"


def apply_plan(home: dict[str, Any], planned: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    kind = planned.get("kind")
    if kind == "unavailable":
        return {"status": "bad", "message": planned.get("message") or "No matching device.", "changed": []}
    if kind == "status":
        if planned.get("clarify") or not planned.get("targets"):
            return {
                "status": "warn",
                "message": planned.get("clarify") or "I couldn't find that device.",
                "changed": [],
            }
        lines = []
        for t in planned["targets"]:
            live = find_device(home, t["id"])
            lines.append(f"{t['name']}: {describe(live) if live else '?'}")
        return {"status": "ok", "message": "\n".join(lines), "changed": []}
    if kind != "command":
        return {"status": "warn", "message": f"Not a command ({kind}).", "changed": []}
    if planned.get("clarify"):
        return {"status": "warn", "message": planned["clarify"], "changed": []}
    targets = planned.get("targets") or []
    if not targets:
        return {"status": "bad", "message": "No matching devices to change.", "changed": []}
    if planned.get("needs_confirm") and not force:
        names = ", ".join(t["name"] for t in targets)
        verb = ASK.get(planned.get("action") or "", planned.get("action"))
        return {
            "status": "confirm",
            "message": f"Not sure. Should I {verb} {names}?",
            "changed": [],
        }
    changed = []
    action = planned.get("action") or ""
    for t in targets:
        live = find_device(home, t["id"])
        if not live:
            continue
        apply_action(live, action)
        changed.append(t["id"])
    names = ", ".join(t["name"] for t in targets)
    verb = VERB.get(action, action.replace("_", " ").title())
    return {"status": "ok", "message": f"{verb} {names}.", "changed": changed}


VERB = {
    "turn_on": "Turned on",
    "turn_off": "Turned off",
    "dim": "Dimmed",
    "brighten": "Brightened",
    "lock": "Locked",
    "unlock": "Unlocked",
    "ac_on": "Switched A/C on:",
    "heat_on": "Switched heat on:",
}
ASK = {
    "turn_on": "turn on",
    "turn_off": "turn off",
    "dim": "dim",
    "brighten": "brighten",
    "lock": "lock",
    "unlock": "unlock",
    "ac_on": "switch A/C on for",
    "heat_on": "switch heat on for",
}


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


def trace_rows(questions: dict[str, Any], answers: dict[str, Any], used: list[str]) -> list[dict[str, Any]]:
    rows = []
    for qid, spec in questions.items():
        ans = answers.get(qid) or {}
        row: dict[str, Any] = {
            "id": qid,
            "type": spec.get("type"),
            "label": question_label(qid),
            "used": qid in used,
            "instructions": spec.get("instructions"),
        }
        if ans.get("type") == "noul":
            row["noul"] = ans.get("noul")
            row["choice"] = None
            row["confidence"] = None
            row["probabilities"] = {"yes": ans.get("noul")}
        else:
            row["choice"] = ans.get("choice")
            row["confidence"] = ans.get("confidence")
            row["probabilities"] = ans.get("probabilities") or {}
        rows.append(row)
    used_rows = [r for uid in used for r in rows if r["id"] == uid]
    rest = [r for r in rows if r["id"] not in used]
    return used_rows + rest


def _choice(winner: str, options: list[str], confidence: float = 0.86) -> dict[str, Any]:
    if winner not in options:
        winner = options[0]
    leftover = max(0.0, 1.0 - 0.72)
    others = [o for o in options if o != winner]
    share = leftover / len(others) if others else 0.0
    probs = {o: (0.72 if o == winner else share) for o in options}
    total = sum(probs.values()) or 1.0
    probs = {k: round(v / total, 4) for k, v in probs.items()}
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
    """Keyword stand-in so the house demo runs with no API key."""
    text = request.lower()
    rooms = [r["id"] for r in home["rooms"]]
    devices = all_devices(home)
    device_ids = [d["id"] for d in devices]

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

    if any(c in text for c in general_cues):
        category = "general"
    elif status_cues:
        category = "status_question"
    else:
        category = "command"

    compound_split = split_request(request)
    is_compound = 0.92 if len(compound_split) >= 2 and "all the" not in text and "whole house" not in text else 0.04

    if any(w in text for w in ("lock", "unlock", "lock up", "secure")):
        dtype = "lock"
    elif any(w in text for w in ("music", "speaker", "audio", "song", "podcast")):
        dtype = "speaker"
    elif "fan" in text:
        dtype = "fan"
    elif any(w in text for w in ("coffee", "kettle", "boil", "brew")):
        dtype = "appliance"
    elif any(w in text for w in ("heat", "thermostat", "a/c", "ac on", "cool the")) and "fan" not in text:
        dtype = "thermostat"
    else:
        dtype = "light"

    outdoor = any(w in text for w in ("outside", "outdoor", "patio"))
    has_outdoor = any(d["room"] == "patio" for d in devices)
    available = 0.08 if outdoor and not has_outdoor else 0.94

    whole = any(w in text for w in ("all the", "whole house", "everywhere", "lock up"))
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
    for needles, rid in room_map:
        if any(n in text for n in needles) and rid in rooms:
            room = rid
            break
        if any(n in text for n in needles) and rid == "bedroom" and "primary_bedroom" in rooms:
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
    for needle, did in name_map:
        if needle in text and did in device_ids:
            device = did
            break

    if "unlock" in text:
        lock_action = "unlock"
    else:
        lock_action = "lock"
    if any(w in text for w in ("off", "shut", "stop", "silence", "kill")):
        power = "turn_off"
    elif "dim" in text:
        power = "dim"
    elif "bright" in text:
        power = "brighten"
    else:
        power = "turn_on"
    if "heat" in text:
        climate = "heat_on"
    elif any(w in text for w in ("cool", "a/c", "ac")):
        climate = "ac_on"
    else:
        climate = "turn_off" if power == "turn_off" else "ac_on"

    answers: dict[str, Any] = {}
    for qid, spec in questions.items():
        qtype = spec["type"]
        if qid == "category":
            answers[qid] = _choice(category, list(spec["criteria"]), 0.9 if category != "command" else 0.84)
        elif qid == "is_compound":
            answers[qid] = _noul(is_compound)
        elif qid == "scope":
            answers[qid] = _choice(scope, list(spec["criteria"]), 0.8 if whole else 0.7)
        elif qid == "available":
            answers[qid] = _noul(available)
        elif qid == "device_type":
            answers[qid] = _choice(dtype, list(spec["criteria"]), 0.82)
        elif qid == "room":
            answers[qid] = _choice(room, list(spec["criteria"]), 0.75 if room != NONE else 0.55)
        elif qid == "device":
            answers[qid] = _choice(device, list(spec["criteria"]), 0.72 if device != NONE else 0.6)
        elif qid == "action.light":
            answers[qid] = _choice(power if power in spec["criteria"] else "turn_on", list(spec["criteria"]))
        elif qid == "action.fan":
            answers[qid] = _choice("turn_off" if power == "turn_off" else "turn_on", list(spec["criteria"]))
        elif qid == "action.speaker":
            answers[qid] = _choice("turn_off" if power == "turn_off" else "turn_on", list(spec["criteria"]))
        elif qid == "action.thermostat":
            answers[qid] = _choice(climate if climate in spec["criteria"] else "ac_on", list(spec["criteria"]))
        elif qid == "action.appliance":
            answers[qid] = _choice("turn_off" if power == "turn_off" else "turn_on", list(spec["criteria"]))
        elif qid == "action.lock":
            answers[qid] = _choice(lock_action, list(spec["criteria"]), 0.88)
        elif qtype == "noul":
            answers[qid] = _noul(0.1)
        else:
            keys = list(spec.get("criteria") or {})
            answers[qid] = _choice(keys[0], keys, 0.4) if keys else _choice(NONE, [NONE], 0.4)
    return answers


def homes_catalog() -> list[dict[str, str]]:
    return [{"id": k, "label": v["label"]} for k, v in HOMES.items()]
