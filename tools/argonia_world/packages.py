"""AI packages of Argonia.esm, built natively on Skyrim's own package templates (lane block-build; PackageRecords.cs
documents the vanilla shape). The intermediate record carries the template link, flags, schedule and the location input;
ArgoniaGen copies the template's other inputs the way the CK does. Metres become units only through skyrim_units."""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su

SANDBOX_TEMPLATE = "01C254:Skyrim.esm"  # PACK EditorID Sandbox (PackageTemplate; data inputs 0 Location, 1..7, 14, 25, 27, 29, 31)
SLEEP_TEMPLATE = "019717:Skyrim.esm"  # PACK EditorID Sleep (PackageTemplate; inputs 0 Location, 1 Target, 2 Found Bed, 11..26)


def _record(alloc, edid, entity_key, template, flags, ref_form_key, radius_m, start_hour, hours) -> dict:
    if not 0 <= start_hour <= 23:
        raise ValueError(f"{edid}: start hour {start_hour} outside 0..23")
    if not 0 < hours <= 24:
        raise ValueError(f"{edid}: duration {hours} h outside (0, 24]")
    return {
        "type": "PACK", "formKey": alloc.form_key(edid, "PACK", entity_key), "edid": edid, "template": template,
        "flags": list(flags),
        "schedule": {"hour": int(start_hour), "minute": 0, "durationHours": hours, "dayOfWeek": "Any"},
        "location": {"ref": ref_form_key, "radius": su.rounded(su.metres_to_units(radius_m), 2)},
    }


def sandbox(alloc, edid, entity_key, ref_form_key, radius_m, start_hour, hours) -> dict:
    """Sandbox around a placed reference within radius_m, from start_hour for `hours`."""
    return _record(alloc, edid, entity_key, SANDBOX_TEMPLATE, [], ref_form_key, radius_m, start_hour, hours)


def sleep(alloc, edid, entity_key, ref_form_key, radius_m, start_hour, hours) -> dict:
    """Sleep in a bed found within radius_m of a placed reference (vanilla sleep packages carry WeaponsUnequipped)."""
    return _record(alloc, edid, entity_key, SLEEP_TEMPLATE, ["WeaponsUnequipped"], ref_form_key, radius_m, start_hour, hours)
