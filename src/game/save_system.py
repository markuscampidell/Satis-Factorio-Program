# game.save_system
import json
import os
import re
from pathlib import Path

from core.vector2 import Vector2
from objects.conveyors.belt_segment import BeltSegment
from objects.item_filter import ItemFilter
from objects.machines.smelter import Smelter
from objects.machines.assembler import Assembler
from objects.machines.splitter import Splitter
from objects.machines.storage import Storage
from constants.itemdata import get_item_by_id

SAVE_VERSION = 1

_SAVES_DIR = Path(__file__).resolve().parents[2] / "saves"
_LAST_OPENED_FILE = _SAVES_DIR / ".last_opened"

# Every machine class that can appear in a save file, keyed by its own
# SAVE_TYPE tag - each owns its (de)serialization via to_dict()/from_dict(),
# so adding a new machine type only means adding it here, not touching
# _serialize_machine/_deserialize_machine at all.
_SAVABLE_MACHINE_TYPES = {cls.SAVE_TYPE: cls for cls in (Smelter, Assembler, Splitter, Storage)}


def _saves_dir() -> Path:
    _SAVES_DIR.mkdir(parents=True, exist_ok=True)
    return _SAVES_DIR


def _sanitize_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Save name cannot be empty")

    name = re.sub(r"[^A-Za-z0-9 _-]", "_", name)
    name = name.strip(" ._")

    if not name:
        raise ValueError("Save name has no valid characters")

    return name[:64]


def _save_path(name: str) -> Path:
    return _saves_dir() / f"{_sanitize_name(name)}.json"


def is_valid_save_name(name: str) -> bool:
    """True if `name` is already clean - i.e. sanitizing it wouldn't change
    it. Used to reject special characters up front with a clear message,
    instead of silently mangling the name or letting a name that sanitizes
    to nothing raise ValueError deep in path construction."""
    stripped = (name or "").strip()
    if not stripped:
        return False
    try:
        return _sanitize_name(name) == stripped
    except ValueError:
        return False


def save_exists(name: str) -> bool:
    return _save_path(name).exists()


def list_saves() -> list[str]:
    return sorted(p.stem for p in _saves_dir().glob("*.json"))


def delete_save(name: str) -> None:
    path = _save_path(name)
    if path.exists():
        path.unlink()


def rename_save(old_name: str, new_name: str) -> None:
    old_path = _save_path(old_name)
    new_path = _save_path(new_name)
    was_last_opened = (get_last_opened() == old_name)

    old_path.replace(new_path)

    if was_last_opened:
        _set_last_opened(new_name)


def get_last_opened() -> str | None:
    """The name of the save that was last created/loaded, or None if
    there isn't one (never opened one, or it's since been deleted)."""
    if not _LAST_OPENED_FILE.exists():
        return None

    name = _LAST_OPENED_FILE.read_text().strip()
    return name if name and save_exists(name) else None


def _set_last_opened(name: str) -> None:
    _saves_dir()
    _LAST_OPENED_FILE.write_text(name)


def save_game(world, player, camera, name: str) -> None:
    data = {
        "version": SAVE_VERSION,
        "player": _serialize_player(player),
        "camera": {"x": camera.x, "y": camera.y},
        "belts": [_serialize_belt(seg) for seg in world.belt_segments],
        "machines": [_serialize_machine(m) for m in world.machines],
    }

    path = _save_path(name)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def load_game(world, player, camera, belt_system, name: str) -> None:
    path = _save_path(name)
    with open(path, "r") as f:
        data = json.load(f)

    world.clear()

    _deserialize_player(player, data["player"])

    # Older saves (before camera position was tracked) just fall back to
    # the initializer's already-centered-on-player default instead of
    # snapping to (0, 0).
    camera_data = data.get("camera")
    if camera_data:
        camera.x = camera_data["x"]
        camera.y = camera_data["y"]
    else:
        camera.center_on(player.rect)

    for entry in data["belts"]:
        world.add_belt_segment(_deserialize_belt(entry))

    for entry in data["machines"]:
        world.add_machine(_deserialize_machine(entry))

    belt_system.update_belt_incoming_directions()

    _set_last_opened(name)


def new_game(world, player, camera, name: str) -> None:
    """Reset world/player to a brand-new game state (empty world, starting
    grant inventory) and immediately persist it."""
    world.clear()

    player.inventory.clear()
    player.rect.centerx = 0
    player.rect.centery = 0
    player.dx = 0
    player.dy = 0

    player.inventory.try_add_items("iron_ingot", 4300)
    player.inventory.try_add_items("copper_ingot", 200)

    camera.center_on(player.rect)

    save_game(world, player, camera, name)
    _set_last_opened(name)


# --- serialization helpers ---

def _serialize_player(player):
    return {
        "x": player.rect.centerx,
        "y": player.rect.centery,
        "inventory": player.inventory.slots,
    }


def _deserialize_player(player, data):
    player.rect.centerx = data["x"]
    player.rect.centery = data["y"]
    player.inventory.slots = data["inventory"]
    player.inventory.dirty = False
    player.dx = 0
    player.dy = 0


def _serialize_belt(seg):
    return {
        "grid_pos": list(seg.grid_pos),
        "direction": [seg.direction.x, seg.direction.y],
        "belt_type": seg.belt_type,
        "item": seg.item.item_id if seg.item else None,
        "filter": seg.filter.to_dict(),
    }


def _deserialize_belt(entry):
    seg = BeltSegment(
        tuple(entry["grid_pos"]),
        Vector2(*entry["direction"]),
        [],
        belt_type=entry["belt_type"],
    )
    seg.item = get_item_by_id(entry["item"]) if entry["item"] else None

    if "filter" in entry:
        seg.filter = ItemFilter.from_dict(entry["filter"])
    else:
        # Back-compat with saves from before the filter was nested under
        # its own "filter" key (it used to be two flat top-level fields).
        seg.filter = ItemFilter.from_dict({
            "enabled": entry.get("filter_enabled", False),
            "allowed_items": entry.get("allowed_items", []),
        })

    return seg


def _serialize_machine(m):
    return m.to_dict()


def _deserialize_machine(entry):
    cls = _SAVABLE_MACHINE_TYPES[entry["type"]]
    return cls.from_dict(entry)
