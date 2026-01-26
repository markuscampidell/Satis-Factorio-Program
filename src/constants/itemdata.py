from entities.item import Item

iron_ore = Item("iron_ore", "Iron Ore", sprite_path="assets/Sprites/items/iron_ore.png")
copper_ore = Item("copper_ore", "Copper Ore", sprite_path="assets/Sprites/items/copper_ore.png")
zinc_ore = Item("zinc_ore", "Zinc Ore", sprite_path= "assets/Sprites/items/zinc_ore.png")
coal = Item("coal", "Coal")


iron_ingot = Item("iron_ingot", "Iron Ingot", sprite_path="assets/Sprites/items/iron_ingot.png")
copper_ingot = Item("copper_ingot", "Copper Ingot", sprite_path = "assets/Sprites/items/copper_ingot.png")
zinc_ingot = Item("zinc_ingot", "Zinc Ingot", sprite_path="assets/Sprites/items/zinc_ingot.png")
steel = Item("steel", "Steel")


# Global list of all items
ITEMS = [iron_ore, iron_ingot, copper_ore, copper_ingot, zinc_ore, zinc_ingot, steel, coal]

def get_item_by_id(item_id):
    for item in ITEMS:
        if item.item_id == item_id:
            return item
    return None