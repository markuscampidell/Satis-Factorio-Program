# objects.machines.machine_output_pusher
from constants.itemdata import get_item_by_id
from game.grid import four_neighbor_coords


def push_output(machine, belt_map, machine_map):
    """Push one item from `machine`'s output inventories onto whatever's at
    an output tile - a belt, a splitter, or another machine. Tries each
    output direction in turn for the first available output item."""
    for item_id, inv in machine.output_inventories.items():
        if _push_from_inventory(machine, inv, belt_map, machine_map):
            return True
    return False


def push_storage_output(storage, belt_map, machine_map):
    """Same push behavior as push_output(), but for a Storage building's
    single flat inventory instead of a dict of per-item 1x1 inventories -
    lets belts/splitters pull items back out of a storage chest exactly
    like they already can from a producing machine's output."""
    return _push_from_inventory(storage, storage.inventory, belt_map, machine_map)


def _push_from_inventory(machine, inv, belt_map, machine_map):
    for row in inv.slots:
        for i, slot in enumerate(row):
            if not (slot and slot["amount"] > 0):
                continue

            item_obj = get_item_by_id(slot["item"])

            for (dx, dy), push_direction in machine._get_output_tiles():
                tile_pos = (machine.grid_pos[0] + dx, machine.grid_pos[1] + dy)

                if _try_push_to_tile(machine, item_obj, push_direction, tile_pos, belt_map, machine_map):
                    slot["amount"] -= 1
                    emptied = slot["amount"] == 0
                    if emptied:
                        row[i] = None
                    if inv.merge_stacks(item_obj.item_id) or emptied:
                        inv.compact()
                    return True

    return False


def _try_push_to_tile(machine, item_obj, push_direction, tile_pos, belt_map, machine_map):
    belt = belt_map.get(tile_pos)
    if belt is not None:
        # Only a belt facing directly away from us (same direction as
        # the push) accepts - not perpendicular, not facing back in.
        if belt.item is not None or belt.direction != push_direction or not belt.accepts_item(item_obj.item_id):
            return False

        belt.item = item_obj
        belt.item_progress = 0.0
        belt.current_incoming_direction = push_direction
        return True

    target = machine_map.get(tile_pos)
    if target is None:
        return False

    # A machine fed straight from another machine/storage push (rather
    # than from a belt behind it) has no belt speed of its own to inherit -
    # fall back to the fastest belt touching it (matters most for a
    # splitter, which needs a speed for its own internal item timer;
    # harmless for ProducingMachine/Storage, which just use it for the
    # input animation).
    source_speed = _fastest_neighboring_belt_speed(tile_pos, belt_map)
    return target.try_receive_item(item_obj, machine.grid_pos, direction=push_direction, source_speed=source_speed)


def _fastest_neighboring_belt_speed(tile_pos, belt_map):
    """The speed (tiles/sec) of the fastest belt touching any of the 4
    tiles adjacent to tile_pos, or None if there isn't one."""
    x, y = tile_pos
    speeds = [belt_map[pos].speed for pos in four_neighbor_coords(x, y) if pos in belt_map]
    return max(speeds) if speeds else None
