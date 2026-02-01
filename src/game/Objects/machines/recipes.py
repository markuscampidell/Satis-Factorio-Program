from constants.itemdata import iron_ore, iron_ingot, copper_ore, copper_ingot, coal

class Recipe:
    def __init__(self, name, inputs, outputs, process_time):
        self.name = name
        self.inputs = inputs
        self.input_length = len(inputs)
        self.outputs = outputs
        self.process_time = process_time
    def outputs_per_minute(self):
        result = {}
        for item_id, amount in self.outputs.items():
            result[item_id] = amount * (60 / self.process_time)
        return result
    def inputs_per_minute(self):
        result = {}
        for item_id, amount in self.inputs.items():
            result[item_id] = amount * (60 / self.process_time)
        return result

smelter_recipes = []
iron_ingot_recipe = Recipe("Iron_Ingot", {"iron_ore": 3}, {"iron_ingot": 1}, 2)
copper_ingot_recipe = Recipe("Copper_Ingot", {"copper_ore": 3}, {"copper_ingot": 1}, 2)
test = Recipe("test", {"iron_ingot": 1}, {"copper_ore": 3}, 2)
smelter_recipes.extend([iron_ingot_recipe, copper_ingot_recipe, test])

foundry_recipes = []
steel_recipe = Recipe("Steel", {"iron_ingot": 2, "coal": 2}, {"steel": 1}, 3)
foundry_recipes.extend([steel_recipe])