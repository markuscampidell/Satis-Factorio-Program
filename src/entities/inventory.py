# entities.inventory
from constants.itemdata import Item

class Inventory:
    """A grid of item slots, like a chest or a backpack. Each slot holds
    one kind of item and how many of it there are."""

    MAX_STACK_SIZE = 100

    def __init__(self, slot_width:int, slot_height:int):
        self.width = slot_width
        self.height = slot_height
        self.slots = [[None for _ in range(slot_width)] for _ in range(slot_height)] # creates a 2D list of None values representing empty slots

    def compact(self):
        """Packs every occupied slot toward the start. Called
        immediately whenever a removal empties a slot, so the grid never
        visibly sits with a gap in the middle."""

        flat = [self.slots[y][x] for y in range(self.height) for x in range(self.width)]

        last = len(flat) - 1
        for i in range(len(flat)):
            if flat[i] is not None:
                continue
            while last > i and flat[last] is None:
                last -= 1
            if last <= i:
                break
            flat[i] = flat[last]
            flat[last] = None
            last -= 1

        self.slots = [flat[y * self.width:(y + 1) * self.width] for y in range(self.height)]

    def merge_stacks(self, item_id):
        """Merges every stack of item_id into as few slots as
        possible using MAX_STACK_SIZE, without moving any of them to a different position in the grid.
        Returns True if any slots were emptied in the process, else False."""

        positions = [(y, x) for y in range(self.height) for x in range(self.width)
                     if self.slots[y][x] and self.slots[y][x]["item"] == item_id]
        if len(positions) < 2:
            return False

        remaining = sum(self.slots[y][x]["amount"] for y, x in positions)
        emptied = False

        for y, x in positions:
            if remaining <= 0:
                self.slots[y][x] = None
                emptied = True
                continue
            amount = min(self.MAX_STACK_SIZE, remaining)
            self.slots[y][x]["amount"] = amount
            remaining -= amount

        return emptied

    def clone(self):
        """A disposable copy for dry-running a sequence of add/remove
        operations before committing them to the real inventory."""
        copy = Inventory(self.width, self.height)
        copy.slots = [[dict(slot) if slot else None for slot in row] for row in self.slots]
        return copy

    def clear(self):
        """Empties the inventory completely."""
        self.slots = [[None for _ in range(self.width)] for _ in range(self.height)]

    def try_add_items(self, item, amount):
        """Tries to add `amount` of an item to the inventory. Tops up
        stacks that already have this item first, then uses empty slots
        for whatever's left. Returns False if there wasn't enough room
        anywhere."""
        if isinstance(item, Item): item_id = item.item_id
        else: item_id = item

        if not self.can_add_items(item_id, amount): return False  # Not enough space to add items

        remaining = amount

        # First, try to fill existing stacks
        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]
                if slot and slot["item"] == item_id and slot["amount"] < self.MAX_STACK_SIZE:
                    can_add = min(self.MAX_STACK_SIZE - slot["amount"], remaining)
                    slot["amount"] += can_add
                    remaining -= can_add
                    if remaining == 0:
                        return True

        # Then, add to empty slots
        for y in range(self.height):
            for x in range(self.width):
                if self.slots[y][x] is None:
                    to_add = min(self.MAX_STACK_SIZE, remaining)
                    self.slots[y][x] = {"item": item_id, "amount": to_add}
                    remaining -= to_add
                    if remaining == 0:
                        return True
        return remaining == 0

    
    def can_add_items(self, item_id: str, amount: int) -> bool:
        """Checks if there's room for `amount` of an item, without
        actually adding anything. An empty slot counts as a whole free
        stack of space."""
        remaining = amount

        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]

                if slot is None: remaining -= self.MAX_STACK_SIZE
                # Empty slot can take a full stack
                    
                elif slot["item"] == item_id: remaining -= (self.MAX_STACK_SIZE - slot["amount"])
                # Slot already contains this item, can add up to the stack limit
                    
                if remaining <= 0: return True
        return False

    def try_remove_item(self, item_id: str, amount: int) -> bool:
        """Tries to remove `amount` of an item from the inventory. Cleans
        up any empty gaps and squishes leftover stacks together
        afterward. Returns False if there wasn't enough to remove."""

        remaining = amount
        became_empty = False  # tracked so compact() runs once, after the scan below finishes,
                               # rather than mid-scan where it could disturb slots this loop hasn't visited yet

        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]

                if slot and slot["item"] == item_id:
                    # Remove as much as possible from this slot
                    to_remove = min(slot["amount"], remaining)
                    slot["amount"] -= to_remove
                    remaining -= to_remove

                    # If slot is empty after removal, set it to None
                    if slot["amount"] == 0:
                        self.slots[y][x] = None
                        became_empty = True

                    if remaining == 0:
                        if self.merge_stacks(item_id) or became_empty: self.compact()
                        return True

        if self.merge_stacks(item_id) or became_empty: self.compact()
        return False  # Not enough items to remove

    def get_amount(self, item_id: str) -> int:
        # Get the total amount of a specific item in the inventory

        total = 0
        for row in self.slots:
            for slot in row:
                if slot and slot["item"] == item_id:
                    total += slot["amount"]
        return total

    def has_enough_items(self, items: dict[str, int]) -> bool:
        for item_id, amount in items.items():
            if self.get_amount(item_id) < amount:
                return False
        return True

    def try_remove_items(self, items: dict[str, int]) -> bool:
        """Tries to remove a whole bunch of different items at once. Only
        does it if there's enough of everything - if even one item is
        short, nothing gets removed at all."""

        if not self.has_enough_items(items): return False
        for item_id, amount in items.items(): self.try_remove_item(item_id, amount)
        return True

    def contents_as_dict(self) -> dict[str, int]:
        """This inventory's total amount of each item it holds, as
        {item_id: amount}"""
        totals = {}
        for row in self.slots:
            for slot in row:
                if slot:
                    totals[slot["item"]] = totals.get(slot["item"], 0) + slot["amount"]
        return totals