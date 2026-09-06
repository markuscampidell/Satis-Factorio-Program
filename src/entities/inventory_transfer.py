# entities.inventory_transfer
"""Shared helpers for moving items between two Inventory objects"""

def move_stack(source_inv, x, y, dest_inv, expected_item_id=None):
    """Moves as much as fits of the stack sitting at (x, y) into another
    inventory. expected_item_id is a safety check - if the item there
    isn't what the caller expected to see, nothing is moved."""

    slot = source_inv.slots[y][x]
    if not slot:
        return
    if expected_item_id is not None and slot["item"] != expected_item_id:
        return
    _move_amount(source_inv, dest_inv, slot["item"], slot["amount"])

def move_all_of_type(source_inv, x, y, dest_inv, expected_item_id=None):
    """Moves every single item of that same type (not just the one stack
    at (x, y), but all of it) into another inventory. expected_item_id is
    a safety check - if the item there isn't what the caller expected to
    see, nothing is moved."""

    slot = source_inv.slots[y][x]
    if not slot:
        return
    if expected_item_id is not None and slot["item"] != expected_item_id:
        return
    item_id = slot["item"]
    _move_amount(source_inv, dest_inv, item_id, source_inv.get_amount(item_id))

def _move_amount(source_inv, dest_inv, item_id, amount):
    """Moves items one at a time into dest_inv, stopping early if it runs
    out of room - then only takes out of source_inv exactly how many
    actually made it across."""
    moved = 0
    for _ in range(amount):
        if dest_inv.try_add_items(item_id, 1):
            moved += 1
        else:
            break
    if moved:
        source_inv.try_remove_item(item_id, moved)