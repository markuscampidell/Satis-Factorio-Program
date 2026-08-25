# game.save_system
import json
import os
import re
from pathlib import Path

from core.vector2 import Vector2
from entities.inventory import Inventory
from objects.conveyors.belt_segment import BeltSegment
from objects.machines.producing_machine import ProducingMachine
from objects.machines.smelter import Smelter
from objects.machines.assembler import Assembler
from objects.machines.splitter import Splitter
from constants.itemdata import get_item_by_id
from constants.recipes import get_recipe_by_id

SAVE_VERSION = 1

_SAVES_DIR = Path(__file__).resolve().parents[2] / "saves"
_LAST_OPENED_FILE = _SAVES_DIR / ".last_opened"

_MACHINE_TYPES = {
    Smelter: "smelter",
    Assembler: "assembler",
}


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

    world.machines.clear()
    world.belt_segments.clear()
    world.machine_map.clear()
    world.belt_map.clear()

    _deserialize_player(player, data["player"])

    # Older saves (before camera position was tracked) just fall back to
    # the initializer's already-centered-on-player default instead of
    # snapping to (0, 0).
    camera_data = data.get("camera")
    if camera_data:
        camera.x = camera_data["x"]
        camera.y = camera_data["y"]
    else:
        camera.x = player.rect.centerx - camera.screen_width // 2
        camera.y = player.rect.centery - camera.screen_height // 2

    for entry in data["belts"]:
        world.add_belt_segment(_deserialize_belt(entry))

    for entry in data["machines"]:
        world.add_machine(_deserialize_machine(entry))

    belt_system.update_belt_incoming_directions()

    _set_last_opened(name)


def new_game(world, player, camera, name: str) -> None:
    """Reset world/player to a brand-new game state (empty world, starting
    grant inventory) and immediately persist it."""
    world.machines.clear()
    world.belt_segments.clear()
    world.machine_map.clear()
    world.belt_map.clear()

    player.inventory = Inventory(5, 9)
    player.rect.centerx = 0
    player.rect.centery = 0
    player.dx = 0
    player.dy = 0

    player.inventory.try_add_items("iron_ingot", 4300)
    player.inventory.try_add_items("copper_ingot", 200)

    camera.x = player.rect.centerx - camera.screen_width // 2
    camera.y = player.rect.centery - camera.screen_height // 2

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
    player.inventory = Inventory(5, 9)
    player.inventory.slots = data["inventory"]
    player.dx = 0
    player.dy = 0


def _serialize_belt(seg):
    return {
        "grid_pos": list(seg.grid_pos),
        "direction": [seg.direction.x, seg.direction.y],
        "belt_type": seg.belt_type,
        "item": seg.item.item_id if seg.item else None,
    }


def _deserialize_belt(entry):
    seg = BeltSegment(
        tuple(entry["grid_pos"]),
        Vector2(*entry["direction"]),
        [],
        belt_type=entry["belt_type"],
    )
    seg.item = get_item_by_id(entry["item"]) if entry["item"] else None
    return seg


def _serialize_machine(m):
    if isinstance(m, Splitter):
        return {
            "type": "splitter",
            "grid_pos": list(m.grid_pos),
            "direction": [m.direction.x, m.direction.y],
            "current_item": m.current_item.item_id if m.current_item else None,
        }

    # Smelter / Assembler (both ProducingMachine)
    return {
        "type": _MACHINE_TYPES[type(m)],
        "grid_pos": list(m.grid_pos),
        "recipe_id": m.recipe.recipe_id if m.recipe else None,
        "input_inventories": {item_id: inv.slots for item_id, inv in m.input_inventories.items()},
        "output_inventories": {item_id: inv.slots for item_id, inv in m.output_inventories.items()},
    }


def _deserialize_machine(entry):
    if entry["type"] == "splitter":
        m = Splitter(grid_pos=tuple(entry["grid_pos"]), direction=Vector2(*entry["direction"]))
        m.current_item = get_item_by_id(entry["current_item"]) if entry["current_item"] else None
        # receive_item() only ever accepts incoming_direction == self.direction
        # and sets current_incoming_direction to it - it's otherwise never
        # initialized, so a loaded splitter holding an item needs it set
        # here too (world_renderer reads it unconditionally when drawing).
        m.current_incoming_direction = m.direction
        m.item_progress = 0.0
        m.current_output_index = 0
        m.current_item_speed = Splitter.DEFAULT_TILES_PER_SEC
        return m

    cls = Smelter if entry["type"] == "smelter" else Assembler
    m = cls(tuple(entry["grid_pos"]))

    recipe = get_recipe_by_id(entry["recipe_id"]) if entry["recipe_id"] else None
    m.recipe = recipe
    m.process_time = recipe.process_time if recipe else 1.0

    if recipe:
        m._reset_inventories(recipe)
    else:
        m.input_inventories = {}
        m.output_inventories = {}

    for item_id, slots in entry["input_inventories"].items():
        m.input_inventories[item_id].slots = slots
    for item_id, slots in entry["output_inventories"].items():
        m.output_inventories[item_id].slots = slots

    m.processing = False
    m.process_timer = 0.0

    return m
