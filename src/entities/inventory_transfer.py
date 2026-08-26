# entities.inventory_transfer
"""Shared helpers for moving items between two Inventory objects - used by
every inventory-holding UI (player, storage, machine input/output) so the
"move this stack" / "move everything of this type" logic only lives once."""


def move_stack(source_inv, x, y, dest_inv):
    """Move as much of the stack at (x, y) in source_inv into dest_inv as
    fits, removing exactly what was moved. No-op on an empty slot."""
    slot = source_inv.slots[y][x]
    if not slot:
        return
    _move_amount(source_inv, dest_inv, slot["item"], slot["amount"])


def move_all_of_type(source_inv, x, y, dest_inv):
    """Move every unit of whichever item type occupies (x, y) in
    source_inv - not just that one slot's stack - into dest_inv, as much as
    fits. No-op on an empty slot."""
    slot = source_inv.slots[y][x]
    if not slot:
        return
    item_id = slot["item"]
    _move_amount(source_inv, dest_inv, item_id, source_inv.get_amount(item_id))


def _move_amount(source_inv, dest_inv, item_id, amount):
    moved = 0
    for _ in range(amount):
        if dest_inv.try_add_items(item_id, 1):
            moved += 1
        else:
            break
    if moved:
        source_inv.try_remove_item(item_id, moved)
