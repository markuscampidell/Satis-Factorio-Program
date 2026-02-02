from entities.item import Item

class Inventory:
    MAX_STACK_SIZE = 100
    def __init__(self, slot_width, slot_height):
        self.width = slot_width
        self.height = slot_height
        self.slots = [[None for _ in range(slot_width)] for _ in range(slot_height)]

    def add_items(self, item, amount):
        if isinstance(item, Item): item_id = item.item_id
        else: item_id = item
        remaining = amount
        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]
                if slot and slot["item"] == item_id and slot["amount"] < self.MAX_STACK_SIZE:
                    can_add = min(self.MAX_STACK_SIZE - slot["amount"], remaining)
                    slot["amount"] += can_add
                    remaining -= can_add
                    if remaining == 0:
                        return True
                    
        for y in range(self.height):
            for x in range(self.width):
                if self.slots[y][x] is None:
                    to_add = min(self.MAX_STACK_SIZE, remaining)
                    self.slots[y][x] = {"item": item_id, "amount": to_add}
                    remaining -= to_add
                    if remaining == 0:
                        return True
        return remaining == 0

    
    def can_add_items(self, item_id, amount):
        remaining = amount
        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]
                if slot is None:
                    remaining -= self.MAX_STACK_SIZE
                elif slot["item"] == item_id:
                    remaining -= (self.MAX_STACK_SIZE - slot["amount"])
                if remaining <= 0:
                    return True
        return False


    def remove_item(self, item_id, amount):
        remaining = amount

        for y in range(self.height):
            for x in range(self.width):
                slot = self.slots[y][x]
                if slot and slot["item"] == item_id:
                    to_remove = min(slot["amount"], remaining)
                    slot["amount"] -= to_remove
                    remaining -= to_remove

                    if slot["amount"] == 0:
                        self.slots[y][x] = None
                    if remaining == 0:
                        return True
                    
        return False


    def get_amount(self, item_id):
        total = 0

        for row in self.slots:
            for slot in row:
                if slot and slot["item"] == item_id:
                    total += slot["amount"]

        return total


    def has_enough_build_cost_items(self, items: dict) -> bool:
        for item_id, amount in items.items():
            if self.get_amount(item_id) < amount:
                return False
        return True

    def remove_build_cost_items(self, items: dict) -> bool:
        if not self.has_enough_build_cost_items(items):
            return False
        for item_id, amount in items.items():
            self.remove_item(item_id, amount)
        return True