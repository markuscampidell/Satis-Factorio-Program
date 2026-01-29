from entities.item import Item

from entities.item import Item

class Inventory:
    # Maximum number of items per slot
    MAX_STACK_SIZE = 100
    def __init__(self, slot_width, slot_height):
        # Number of slots horizontally and vertically
        self.width = slot_width
        self.height = slot_height
        # 2D grid of slots
        # Each slot is either:
        #   None
        #   {"item": item_id, "amount": int}
        self.slots = [[None for _ in range(slot_width)] for _ in range(slot_height)]

    def add_items(self, item, amount):
        # Accept either an Item object or a raw item_id
        if isinstance(item, Item): item_id = item.item_id
        else: item_id = item
        remaining = amount
        # 1) First pass: try to add to existing stacks of the same item
        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]
                # If slot contains the same item and is not full
                if slot and slot["item"] == item_id and slot["amount"] < self.MAX_STACK_SIZE:
                    # How many items can fit into this stack
                    can_add = min(self.MAX_STACK_SIZE - slot["amount"], remaining)
                    slot["amount"] += can_add
                    remaining -= can_add

                    # Stop early if everything was added
                    if remaining == 0:
                        return True

        # 2) Second pass: put items into empty slots
        for y in range(self.height):
            for x in range(self.width):
                if self.slots[y][x] is None:
                    # Create a new stack in this slot
                    to_add = min(self.MAX_STACK_SIZE, remaining)
                    self.slots[y][x] = {"item": item_id, "amount": to_add}
                    remaining -= to_add
                    if remaining == 0:
                        return True
        # Return True only if all items were added
        return remaining == 0

    
    def can_add_items(self, item_id, amount):
        # Simulates adding items WITHOUT modifying the inventory
        remaining = amount
        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]
                # Empty slot can accept a full stack
                if slot is None:
                    remaining -= self.MAX_STACK_SIZE
                # Existing stack of same item can accept partial stack
                elif slot["item"] == item_id:
                    remaining -= (self.MAX_STACK_SIZE - slot["amount"])
                # If we've accounted for all items, it's possible
                if remaining <= 0:
                    return True
        return False


    def remove_item(self, item_id, amount):
        remaining = amount

        # Walk through inventory top-left → bottom-right
        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]

                # Only touch slots that contain this item
                if slot and slot["item"] == item_id:
                    # Remove as much as possible from this slot
                    to_remove = min(slot["amount"], remaining)
                    slot["amount"] -= to_remove
                    remaining -= to_remove

                    # Clear slot if empty
                    if slot["amount"] == 0:
                        self.slots[y][x] = None

                    # Stop early if enough items were removed
                    if remaining == 0:
                        return True

        # Inventory did not contain enough items
        return False


    def get_amount(self, item_id):
        # Counts total amount of an item across all slots
        total = 0

        for row in self.slots:
            for slot in row:
                if slot and slot["item"] == item_id:
                    total += slot["amount"]

        return total


    def has_enough_build_cost_items(self, items: dict) -> bool:
        # items = {item_id: required_amount}
        for item_id, amount in items.items():
            # If any required item is missing or insufficient → fail
            if self.get_amount(item_id) < amount:
                return False
        return True

    def remove_build_cost_items(self, items: dict) -> bool:
        if not self.has_enough_build_cost_items(items):
            return False
        for item_id, amount in items.items():
            self.remove_item(item_id, amount)
        return True