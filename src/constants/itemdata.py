from entities.item import Item

raw_materials = []
iron_ore = Item("iron_ore", "Iron Ore", sprite_path="assets/Sprites/items/iron_ore.png")
copper_ore = Item("copper_ore", "Copper Ore", sprite_path="assets/Sprites/items/copper_ore.png")
zinc_ore = Item("zinc_ore", "Zinc Ore", sprite_path= "assets/Sprites/items/zinc_ore.png")
coal = Item("coal", "Coal")
raw_materials.extend([iron_ore, copper_ore, zinc_ore, coal])

ingots = []
iron_ingot = Item("iron_ingot", "Iron Ingot", sprite_path="assets/Sprites/items/iron_ingot.png")
copper_ingot = Item("copper_ingot", "Copper Ingot", sprite_path = "assets/Sprites/items/copper_ingot.png")
zinc_ingot = Item("zinc_ingot", "Zinc Ingot", sprite_path="assets/Sprites/items/zinc_ingot.png")
ingots.extend([iron_ingot, copper_ingot, zinc_ingot])

alloys = []
steel = Item("steel", "Steel")
brass = Item("brass", "Brass")
alloys.extend([steel, brass])

# Global list of all items
ITEMS = [raw_materials, ingots, alloys]
ITEMS = [item for category in ITEMS for item in category]

def get_item_by_id(item_id):
    for item in ITEMS:
        if item.item_id == item_id:
            return item
    return None