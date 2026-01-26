class Slot:
    """Represents one slot in a machine inventory."""
    def __init__(self, allowed_item_id):
        self.allowed_item_id = allowed_item_id
        self.amount = 0
        self.max_stack = 100


    def can_add(self, item_id, amount):
        # Find the slot for this item
        for slot in self.slots:
            if slot.allowed_item_id == item_id:
                return slot.amount + amount <= slot.max_stack
        return False


    def add(self, amount, max_stack=100):
        self.amount += amount
        if self.amount > max_stack:
            leftover = self.amount - max_stack
            self.amount = max_stack
            return leftover
        return 0

    def remove(self, amount):
        removed = min(self.amount, amount)
        self.amount -= removed
        return removed

class MachineInventory:
    """Inventory with one slot per allowed item."""
    def __init__(self, allowed_items: list):
        # allowed_items: list of item_ids for this inventory
        self.slots = [Slot(item_id) for item_id in allowed_items]

    def get_total_amount(self, item_id):
        for slot in self.slots:
            if slot.allowed_item_id == item_id:
                return slot.amount
        return 0

    def can_add(self, item_id, amount):
        for slot in self.slots:
            if slot.allowed_item_id == item_id:
                return True  # Can always add (we assume stack limits are enforced)
        return False

    def add_item(self, item_id, amount, max_stack=100):
        for slot in self.slots:
            if slot.allowed_item_id == item_id:
                return slot.add(amount, max_stack)
        return amount  # leftover (item not allowed in this inventory)

    def remove_item(self, item_id, amount):
        for slot in self.slots:
            if slot.allowed_item_id == item_id:
                return slot.remove(amount)
        return 0