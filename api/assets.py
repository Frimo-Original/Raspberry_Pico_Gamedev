import json


MAX_SPRITE8 = 32
MANIFEST_PATHS = (
    "assets/sprites/manifest.json",
    "/assets/sprites/manifest.json",
)

_sprite8_entries = None
_sprite8_ids = None


def _read_manifest():
    for path in MANIFEST_PATHS:
        try:
            with open(path, "r") as manifest_file:
                return json.loads(manifest_file.read())
        except OSError:
            pass
    return {"sprites": []}


def _is_sprite8(entry):
    return (
        entry.get("width") == 8
        and entry.get("height") == 8
        and entry.get("type") in ("tile", "item", "enemy", "free")
        and entry.get("file")
    )


def sprite8_entries():
    global _sprite8_entries, _sprite8_ids
    if _sprite8_entries is None:
        entries = []
        ids = {}
        for entry in _read_manifest().get("sprites", []):
            if not _is_sprite8(entry):
                continue
            if len(entries) >= MAX_SPRITE8:
                break
            sprite_id = len(entries)
            sprite_type = entry.get("type", "")
            name = entry.get("name", "")
            entries.append(
                {
                    "id": sprite_id,
                    "type": sprite_type,
                    "name": name,
                    "file": entry.get("file", ""),
                }
            )
            ids[(sprite_type, name)] = sprite_id
        _sprite8_entries = entries
        _sprite8_ids = ids
    return _sprite8_entries


def sprite8_id(sprite_type, name):
    sprite8_entries()
    return _sprite8_ids.get((sprite_type, name), -1)
