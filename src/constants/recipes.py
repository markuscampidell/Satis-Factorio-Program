# constants.recipes
class Recipe:
    """A recipe for turning some items into other items, like 3 iron ore
    into 1 iron ingot. Says what goes in, what comes out, and how long it
    takes."""
    def __init__(self, recipe_id:str, name:str, inputs:dict[str, int], outputs:dict[str, int], process_time:float):
        self.recipe_id = recipe_id
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.process_time = process_time

        if process_time <= 0:
            raise ValueError("process_time must be greater than 0")


    def outputs_per_minute(self):
        """How much of each output this recipe would make in one minute,
        if it ran over and over without stopping."""
        result = {}
        for item_id, amount in self.outputs.items():
            result[item_id] = amount * (60 / self.process_time)
        return result

    def inputs_per_minute(self):
        """How much of each input this recipe would eat up in one minute,
        if it ran over and over without stopping."""
        result = {}
        for item_id, amount in self.inputs.items():
            result[item_id] = amount * (60 / self.process_time)
        return result

smelter_recipes = []
iron_ingot_recipe = Recipe("iron_ingot", "Iron Ingot", {"iron_ore": 3}, {"iron_ingot": 1}, 2)
copper_ingot_recipe = Recipe("copper_ingot", "Copper Ingot", {"copper_ore": 3}, {"copper_ingot": 1}, 2)
test = Recipe("test", "Test", {"iron_ingot": 1}, {"copper_ore": 3}, 2)
steel_recipe = Recipe("steel", "Steel", {"iron_ingot": 2, "coal": 2}, {"steel": 1}, 3)
smelter_recipes.extend([iron_ingot_recipe, copper_ingot_recipe, test, steel_recipe])

assembler_recipes = []
iron_plate_recipe = Recipe("iron_plate", "Iron Plate", {"iron_ingot": 2}, {"iron_plate": 40, "coal": 40}, 1) # for testing
assembler_recipes.extend([iron_plate_recipe])


def get_recipe_by_id(recipe_id):
    for recipe in smelter_recipes + assembler_recipes:
        if recipe.recipe_id == recipe_id:
            return recipe
    return None