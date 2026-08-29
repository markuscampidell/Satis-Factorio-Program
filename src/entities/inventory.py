# entities.inventory
from entities.item import Item

class Inventory:
    MAX_STACK_SIZE = 100
    SORT_SETTLE_DELAY = 0.25  # seconds of no further changes before auto-sort runs

    def __init__(self, slot_width:int, slot_height:int):
        self.width = slot_width
        self.height = slot_height
        self.slots = [[None for _ in range(slot_width)] for _ in range(slot_height)] # creates a 2D list of None values representing empty slots
        self.dirty = False  # set on any successful mutation; caller decides when/whether to sort() and clear it
        self._settle_timer = 0.0

    def mark_dirty(self):
        """Flags this inventory as changed and restarts its settle timer -
        call this (instead of setting .dirty directly) from anywhere that
        mutates .slots, so tick_dirty()'s debounce sees every change."""
        self.dirty = True
        self._settle_timer = 0.0

    def tick_dirty(self, dt):
        """Call once per frame: auto-sorts only after this inventory has
        gone SORT_SETTLE_DELAY seconds without a further change. Sorting on
        every single change (the old behavior) visibly reshuffled item
        positions on every belt tick during continuous throughput - e.g. a
        storage chest being fed and drained quickly looked like its slots
        were "duplicating" as stacks jumped position frame to frame.
        Debouncing lets rapid activity settle before the one-time tidy-up,
        instead of re-laying-out the whole grid on every single transfer."""
        if not self.dirty:
            return
        self._settle_timer += dt
        if self._settle_timer >= self.SORT_SETTLE_DELAY:
            self.sort()
            self.dirty = False

    def clone(self):
        """A disposable copy for dry-running a sequence of add/remove
        operations before committing them to the real inventory."""
        copy = Inventory(self.width, self.height)
        copy.slots = [[dict(slot) if slot else None for slot in row] for row in self.slots]
        return copy

    def clear(self):
        """Empties this inventory in place, keeping the same object
        identity - important for e.g. the player's inventory, since
        HandcraftingComponent holds a direct reference to it captured once
        at construction time rather than looking it up through player.inventory
        each time; replacing the object instead of mutating it would silently
        orphan that reference."""
        self.slots = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.dirty = False
        self._settle_timer = 0.0

    def try_add_items(self, item, amount):
        if isinstance(item, Item): item_id = item.item_id
        else: item_id = item

        if not self.can_add_items(item_id, amount): return False  # Not enough space to add items

        self.mark_dirty()  # can_add_items already guarantees this all-or-nothing add will succeed
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
        # Check if the inventory could add a specific amount of an item, return Tre if it can, else False
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
        # Tries to remove a specific amount of an item of the inventory, returns True if successful, else False

        remaining = amount

        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]

                if slot and slot["item"] == item_id:
                    # Remove as much as possible from this slot
                    to_remove = min(slot["amount"], remaining)
                    slot["amount"] -= to_remove
                    remaining -= to_remove
                    self.mark_dirty()

                    # If slot is empty after removal, set it to None
                    if slot["amount"] == 0: self.slots[y][x] = None

                    if remaining == 0: return True

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
        # Tries to remove all items needed for a build cost

        if not self.has_enough_items(items): return False
        for item_id, amount in items.items(): self.try_remove_item(item_id, amount)
        return True

    def contents_as_dict(self) -> dict[str, int]:
        """This inventory's total amount of each item it holds, as
        {item_id: amount} - e.g. for refunding/dumping everything at once."""
        totals = {}
        for row in self.slots:
            for slot in row:
                if slot:
                    totals[slot["item"]] = totals.get(slot["item"], 0) + slot["amount"]
        return totals

    def sort(self):
        """Compacts and groups this inventory's contents: same-item stacks
        are merged (up to MAX_STACK_SIZE), then everything is laid out from
        the top-left in item-id order, with empty slots pushed to the end."""
        totals = self.contents_as_dict()

        flat = [None] * (self.width * self.height)
        index = 0
        for item_id in sorted(totals):
            remaining = totals[item_id]
            while remaining > 0:
                amount = min(self.MAX_STACK_SIZE, remaining)
                flat[index] = {"item": item_id, "amount": amount}
                remaining -= amount
                index += 1

        self.slots = [flat[y * self.width:(y + 1) * self.width] for y in range(self.height)]