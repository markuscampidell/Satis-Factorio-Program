from entities.item import Item

raw_ores = []
limestone = Item("limestone", "Limestone")
iron_ore = Item("iron_ore", "Iron Ore", sprite_path="src/assets/sprites/items/iron_ore.png")
copper_ore = Item("copper_ore", "Copper Ore", sprite_path="src/assets/sprites/items/copper_ore.png")
coal = Item("coal", "Coal")
quartz = Item("quartz", "Quartz")
sulfur = Item("sulfur", "Sulfur")
raw_ores.extend([limestone, iron_ore, copper_ore, coal, quartz, sulfur])


ingots = []
iron_ingot = Item("iron_ingot", "Iron Ingot", sprite_path="src/assets/sprites/items/iron_ingot.png")
copper_ingot = Item("copper_ingot", "Copper Ingot", sprite_path = "src/assets/sprites/items/copper_ingot.png")
steel = Item("steel", "Steel")
ingots.extend([iron_ingot, copper_ingot, steel])


minerals = []
concrete = Item("concrete", "Concrete")
silica = Item("silica", "Silica")
minerals.extend([concrete, silica])


standard_parts = []
iron_plate = Item("iron_plate", "Iron Plate")
iron_rod = Item("iron_rod", "Iron Rod")
standard_parts.extend([iron_plate, iron_rod])



ITEMS = [raw_ores, ingots, minerals, standard_parts]
ITEMS = [item for category in ITEMS for item in category]



def get_item_by_id(item_id):
    for item in ITEMS:
        if item.item_id == item_id:
            return item
    return None