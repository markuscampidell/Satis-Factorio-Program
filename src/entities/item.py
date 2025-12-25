class Item:
    def __init__(self, item_id, name, stack_size=100):
        self.item_id = item_id      # e.g. "iron_plate"
        self.name = name            # e.g. "Iron Plate"
        self.stack_size = stack_size