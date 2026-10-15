"""Smart-home dispatcher: speculative fan-out, then code acts.

Mirrors TypeSafe's public smart-home demo
(https://docs.typesafe.ai/demos/smart-home): one request asks every
question the app might need, including per-device-type actions that are
irrelevant for most utterances. ``plan()`` reads only the answers its
branch needs. The device catalog is ``home_catalog``; the offline parser
is ``home_mock``.
"""

from __future__ import annotations

from typing import Any

from jev_lab.home_catalog import (
    ACTIONS,
    EXAMPLES,
    HOMES,
    ICON,
    NONE,
    QUESTION_LABELS,
    RISKY,
    ROOM_ICON,
    all_devices,
    clone_home,
    describe,
    find_device,
    homes_catalog,
    overlay_house,
    public_home,
)
from jev_lab.home_mock import general_reply, mock_answers, split_request

__all__ = [
    "ACTIONS",
    "EXAMPLES",
    "HOMES",
    "ICON",
    "NONE",
    "QUESTION_LABELS",
    "RISKY",
    "ROOM_ICON",
    "all_devices",
    "apply_plan",
    "build_questions",
    "build_state",
    "clone_home",
    "describe",
    "find_device",
    "general_reply",
    "homes_catalog",
    "mock_answers",
    "overlay_house",
    "plan",
    "public_home",
    "split_request",
    "trace_rows",
]


def build_state(request: str, home: dict[str, Any], speaking_to: str | None) -> dict[str, Any]:
    devices = all_devices(home)
    ctx = next((device for device in devices if device["id"] == speaking_to), None)
    room_name = None
    if ctx:
        room_name = next(room["name"] for room in home["rooms"] if room["id"] == ctx["room"])
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
                    {"name": device["name"], "type": device["type"], "status": describe(device)}
                    for device in room["devices"]
                ],
            }
            for room in home["rooms"]
        ],
    }


def build_questions(home: dict[str, Any]) -> dict[str, Any]:
    rooms = {room["id"]: room["name"] for room in home["rooms"]}
    devices = {
        device["id"]: f"{device['name']}: the {device['type']} in the {rooms[device['room']]}"
        for device in all_devices(home)
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
    for question_id in ids:
        answer = answers.get(question_id) or {}
        if "confidence" in answer and answer["confidence"] is not None:
            values.append(float(answer["confidence"]))
    return min(values) if values else 1.0


def plan(
    answers: dict[str, Any],
    home: dict[str, Any],
    speaking_to: str | None = None,
) -> dict[str, Any]:
    """Turn typed answers into one action. Side effects stay in ``apply_plan``."""
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
    context_room = next((device["room"] for device in devices if device["id"] == speaking_to), None)
    targets: list[dict[str, Any]] = []
    clarify = None
    scope = (answers.get("scope") or {}).get("choice")

    if scope == "whole_house":
        targets = [device for device in devices if device["type"] == type_id]
    else:
        used.append("device")
        if device_id and device_id != NONE:
            found = next((device for device in devices if device["id"] == device_id), None)
            if found:
                type_id = found["type"]
                targets = [found]
        else:
            used.append("room")
            room = room_id if room_id and room_id != NONE else context_room
            if room:
                targets = [
                    device for device in devices if device["room"] == room and device["type"] == type_id
                ]
            else:
                of_type = [device for device in devices if device["type"] == type_id]
                if len(of_type) == 1:
                    targets = of_type
                else:
                    label = ACTIONS.get(type_id or "", {}).get("label", "devices")
                    clarify = f"Which {label}? I couldn't tell which room you meant."

    slim = [
        {"id": target["id"], "name": target["name"], "type": target["type"], "room": target["room"]}
        for target in targets
    ]
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
        for target in planned["targets"]:
            live = find_device(home, target["id"])
            lines.append(f"{target['name']}: {describe(live) if live else '?'}")
        return {"status": "ok", "message": "\n".join(lines), "changed": []}
    if kind != "command":
        return {"status": "warn", "message": f"Not a command ({kind}).", "changed": []}
    if planned.get("clarify"):
        return {"status": "warn", "message": planned["clarify"], "changed": []}
    targets = planned.get("targets") or []
    if not targets:
        return {"status": "bad", "message": "No matching devices to change.", "changed": []}
    if planned.get("needs_confirm") and not force:
        names = ", ".join(target["name"] for target in targets)
        verb = ASK.get(planned.get("action") or "", planned.get("action"))
        return {
            "status": "confirm",
            "message": f"Not sure. Should I {verb} {names}?",
            "changed": [],
        }
    changed = []
    action = planned.get("action") or ""
    for target in targets:
        live = find_device(home, target["id"])
        if not live:
            continue
        apply_action(live, action)
        changed.append(target["id"])
    names = ", ".join(target["name"] for target in targets)
    verb = VERB.get(action, action.replace("_", " ").title())
    return {"status": "ok", "message": f"{verb} {names}.", "changed": changed}


def trace_rows(questions: dict[str, Any], answers: dict[str, Any], used: list[str]) -> list[dict[str, Any]]:
    rows = []
    for question_id, spec in questions.items():
        answer = answers.get(question_id) or {}
        row: dict[str, Any] = {
            "id": question_id,
            "type": spec.get("type"),
            "label": question_label(question_id),
            "used": question_id in used,
            "instructions": spec.get("instructions"),
        }
        if answer.get("type") == "noul":
            row["noul"] = answer.get("noul")
            row["choice"] = None
            row["confidence"] = None
            row["probabilities"] = {"yes": answer.get("noul")}
        else:
            row["choice"] = answer.get("choice")
            row["confidence"] = answer.get("confidence")
            row["probabilities"] = answer.get("probabilities") or {}
        rows.append(row)
    used_rows = [row for question_id in used for row in rows if row["id"] == question_id]
    rest = [row for row in rows if row["id"] not in used]
    return used_rows + rest
