"""Device catalog for the smart-home demo.

Rooms, device constructors, and the two fixture houses live here.
``jev_lab.home.plan`` is the policy that reads this catalog.
"""

from __future__ import annotations

import copy
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


def all_devices(home: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for room in home["rooms"]:
        for device in room["devices"]:
            out.append({**device, "room": room["id"]})
    return out


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


def homes_catalog() -> list[dict[str, str]]:
    return [{"id": key, "label": value["label"]} for key, value in HOMES.items()]
