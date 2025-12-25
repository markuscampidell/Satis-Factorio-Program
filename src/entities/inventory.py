from entities.item import Item

class Inventory:
    def __init__(self):
        # An Inventory has items with an amount
        self.items = {}  # { item_id: amount }

    def add(self, item: Item, amount: int):
        self.items[item.item_id] = self.items.get(item.item_id, 0) + amount

    def remove(self, item: Item, amount: int) -> bool:
        if self.items.get(item.item_id, 0) < amount:
            return False
        self.items[item.item_id] -= amount
        if self.items[item.item_id] == 0:
            del self.items[item.item_id]
        return True

    def get_amount(self, item: Item):
        return self.items.get(item.item_id, 0)