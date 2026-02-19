from entities.item import Item

class Inventory:
    MAX_STACK_SIZE = 100
    def __init__(self, slot_width:int, slot_height:int):
        self.width = slot_width
        self.height = slot_height
        self.slots = [[None for _ in range(slot_width)] for _ in range(slot_height)] # creates a 2D list of None values representing empty slots

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

        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]

                if slot and slot["item"] == item_id:
                    # Remove as much as possible from this slot
                    to_remove = min(slot["amount"], remaining)
                    slot["amount"] -= to_remove
                    remaining -= to_remove

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