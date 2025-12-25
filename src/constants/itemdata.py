from entities.item import Item

iron_ore = Item("iron_ore", "Iron Ore")
iron_ingot = Item("iron_ingot", "Iron Ingot")
copper_ore = Item("copper_ore", "Copper Ore")
copper_ingot = Item("copper_ingot", "Copper Ingot")
steel = Item("steel", "Steel")
coal = Item("coal", "Coal")

# Global list of all items
ITEMS = [iron_ore, iron_ingot, copper_ore, copper_ingot, steel, coal]

def get_item_by_id(item_id):
    for item in ITEMS:
        if item.item_id == item_id:
            return item
    return None