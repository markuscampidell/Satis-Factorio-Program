# objects.machines.machine_output_pusher
from constants.itemdata import get_item_by_id


def push_output(machine, belt_map, machine_map):
    """Push one item from `machine`'s output inventories onto whatever's at
    an output tile - a belt, a splitter, or another machine. Tries each
    output direction in turn for the first available output item."""
    for item_id, inv in machine.output_inventories.items():
        for row in inv.slots:
            for i, slot in enumerate(row):
                if not (slot and slot["amount"] > 0):
                    continue

                item_obj = get_item_by_id(slot["item"])

                for (dx, dy), push_direction in machine._get_output_tiles():
                    tile_pos = (machine.grid_pos[0] + dx, machine.grid_pos[1] + dy)

                    if _try_push_to_tile(machine, item_obj, push_direction, tile_pos, belt_map, machine_map):
                        slot["amount"] -= 1
                        if slot["amount"] == 0:
                            row[i] = None
                        return True

    return False


def _try_push_to_tile(machine, item_obj, push_direction, tile_pos, belt_map, machine_map):
    belt = belt_map.get(tile_pos)
    if belt is not None:
        # Only a belt facing directly away from us (same direction as
        # the push) accepts - not perpendicular, not facing back in.
        if belt.item is not None or belt.direction != push_direction:
            return False

        belt.item = item_obj
        belt.item_progress = 0.0
        belt.current_incoming_direction = push_direction
        return True

    target = machine_map.get(tile_pos)
    if target is None:
        return False
    if hasattr(target, "receive_item"):
        return target.receive_item(item_obj, incoming_direction=push_direction)
    if hasattr(target, "try_receive_item"):
        return target.try_receive_item(item_obj, machine.grid_pos)

    return False
