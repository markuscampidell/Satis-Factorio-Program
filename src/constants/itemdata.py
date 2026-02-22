from entities.item import Item

raw_materials = []
limestone = Item("limestone", "Limestone")
iron_ore = Item("iron_ore", "Iron Ore", sprite_path = "src/assets/sprites/items/raw_materials/iron_ore.png")
copper_ore = Item("copper_ore", "Copper Ore", sprite_path = "src/assets/sprites/items/raw_materials/copper_ore.png")
coal = Item("coal", "Coal", sprite_path = "src/assets/sprites/items/raw_materials/coal.png")
raw_materials.extend([limestone, iron_ore, copper_ore, coal])


ingots = []
iron_ingot = Item("iron_ingot", "Iron Ingot", sprite_path = "src/assets/sprites/items/ingots/iron_ingot.png")
copper_ingot = Item("copper_ingot", "Copper Ingot", sprite_path = "src/assets/sprites/items/ingots/copper_ingot.png")
steel = Item("steel", "Steel", sprite_path="src/assets/sprites/items/ingots/steel.png")
ingots.extend([iron_ingot, copper_ingot, steel])


minerals = []
concrete = Item("concrete", "Concrete", sprite_path="src/assets/sprites")
minerals.extend([concrete])


standard_parts = []
iron_plate = Item("iron_plate", "Iron Plate", sprite_path="src/assets/sprites/items/standard_parts/iron_plate.png")
iron_rod = Item("iron_rod", "Iron Rod", sprite_path="src/assets/sprites/items/standard_parts/iron_rod.png")
standard_parts.extend([iron_plate, iron_rod])



ITEMS = [raw_materials, ingots, minerals, standard_parts]
ITEMS = [item for category in ITEMS for item in category]



def get_item_by_id(item_id):
    for item in ITEMS:
        if item.item_id == item_id:
            return item
    return None