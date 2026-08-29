# entities.inventory
from entities.item import Item

class Inventory:
    MAX_STACK_SIZE = 100

    def __init__(self, slot_width:int, slot_height:int):
        self.width = slot_width
        self.height = slot_height
        self.slots = [[None for _ in range(slot_width)] for _ in range(slot_height)] # creates a 2D list of None values representing empty slots

    def compact(self):
        """Packs every occupied slot toward the start (row-major order),
        filling any empty slot left behind by a removal with whichever
        occupied slot is currently last, instead of leaving a hole. Called
        immediately whenever a removal empties a slot, so the grid never
        visibly sits with a gap in the middle.

        Deliberately NOT a full re-layout like sort() (which regroups
        everything by item id from scratch): that would move every stack
        after the change, not just the one needed to fill the gap - fine
        for a one-off tidy-up, but visually chaotic if it ran on every
        single item in/out during heavy belt throughput (stacks would
        appear to jump between slots, or briefly show in two places at
        once as they moved). This only ever touches the emptied slot plus,
        at most, whichever slot used to be last - everything else stays
        exactly where it was."""
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
        """Consolidates every stack of item_id into as few slots as
        possible (each up to MAX_STACK_SIZE), without moving any of them
        to a different position - only their amounts change, so a stack
        that isn't fully absorbed stays exactly where it was. A stack that
        does get fully absorbed is set to None; returns True if that
        happened, so the caller knows to compact() afterward.

        Only ever touches slots holding item_id - a removal elsewhere
        can't cause two unrelated stacks to visibly merge, keeping this as
        targeted as compact()."""
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
        """Empties this inventory in place, keeping the same object
        identity - important for e.g. the player's inventory, since
        HandcraftingComponent holds a direct reference to it captured once
        at construction time rather than looking it up through player.inventory
        each time; replacing the object instead of mutating it would silently
        orphan that reference."""
        self.slots = [[None for _ in range(self.width)] for _ in range(self.height)]

    def try_add_items(self, item, amount):
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