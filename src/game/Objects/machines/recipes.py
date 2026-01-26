from constants.itemdata import iron_ore, iron_ingot, copper_ore, copper_ingot, steel, coal

class Recipe():
    def __init__(self, name, inputs, outputs, process_time): # dictionaries
        self.name = name
        self.inputs = inputs # for example { "iron_ore": 3 }
        self.outputs = outputs # { "iron ingot": 1 }
        self.process_time = process_time

# Smelter Recipes
smelter_recipes = []
iron_ingot_recipe = Recipe("Iron_Ingot", {"iron_ore": 100}, {"iron_ingot": 100}, 2)
copper_ingot_recipe = Recipe("Copper_Ingot", {"copper_ore": 3}, {"copper_ingot": 1}, 2)
zinc_ingot_recipe = Recipe("Zinc_Ingot", {"zinc_ore": 1}, {"zinc_ingot": 1}, 2)
test = Recipe("test", {"iron_ingot": 1}, {"copper_ore": 3}, 2)

smelter_recipes.extend([iron_ingot_recipe, copper_ingot_recipe, zinc_ingot_recipe, test])

# Foundry Recipes
foundry_recipes = []
steel_recipe = Recipe("Steel", {"iron_ore": 2, "coal": 2}, {"steel": 1}, 3)
brass_recipe = Recipe("Brass", {"copper_ingot": 3, "zinc_ingot": 3}, {"brass_ingot": 1}, 5)
foundry_recipes.extend([steel_recipe, brass_recipe])