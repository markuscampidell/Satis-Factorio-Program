# objects.machines.machine_output_pusher
from constants.itemdata import get_item_by_id


def push_output(machine, belt_map):
    """Push one item from `machine`'s output inventories onto a belt at one
    of its output tiles. Tries each output direction in turn for the first
    available output item."""
    for item_id, inv in machine.output_inventories.items():
        if _push_from_inventory(machine, inv, belt_map):
            return True
    return False


def push_storage_output(storage, belt_map):
    """Same push behavior as push_output(), but for a Storage building's
    single flat inventory instead of a dict of per-item 1x1 inventories."""
    return _push_from_inventory(storage, storage.inventory, belt_map)


def _push_from_inventory(machine, inv, belt_map):
    """Looks through every slot of one inventory for something to push
    out, and pushes the first item that actually finds a belt to take it.
    Cleans up the slot afterward if it emptied out."""
    for row in inv.slots:
        for i, slot in enumerate(row):
            if not (slot and slot["amount"] > 0):
                continue

            item_obj = get_item_by_id(slot["item"])

            for (dx, dy), push_direction in machine._get_output_tiles():
                tile_pos = (machine.grid_pos[0] + dx, machine.grid_pos[1] + dy)

                if _try_push_to_belt(item_obj, push_direction, tile_pos, belt_map):
                    slot["amount"] -= 1
                    emptied = slot["amount"] == 0
                    if emptied:
                        row[i] = None
                    if inv.merge_stacks(item_obj.item_id) or emptied:
                        inv.compact()
                    return True

    return False


def _try_push_to_belt(item_obj, push_direction, tile_pos, belt_map):
    """Tries to push one item onto the belt sitting at a single tile - only
    a belt facing directly away from us (same direction as the push),
    currently empty, and whose filter allows this item accepts. A machine
    or storage at that tile is not a valid target - direct machine-to-machine
    hand-offs (most visibly two adjacent storages endlessly topping each
    other off) went straight through here, so routing everything through a
    belt is what keeps that from happening."""
    belt = belt_map.get(tile_pos)
    if belt is None:
        return False

    if belt.item is not None or belt.direction != push_direction or not belt.accepts_item(item_obj.item_id):
        return False

    belt.item = item_obj
    belt.item_progress = 0.0
    belt.current_incoming_direction = push_direction
    return True
