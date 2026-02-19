class Recipe:
    """example: Recipe(
            name = "Name", 
            inputs = {"input1": 2, "input2": 3},
            outputs = {"output1": 1, "output2": 2},
            process_time = 5) """  # process_time is given in seconds
    def __init__(self, name:str, inputs:dict[str, int], outputs:dict[str, int], process_time:float):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.process_time = process_time

        if process_time <= 0:
            raise ValueError("process_time must be greater than 0")


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
steel_recipe = Recipe("Steel", {"iron_ingot": 2, "coal": 2}, {"steel": 1}, 3)
smelter_recipes.extend([iron_ingot_recipe, copper_ingot_recipe, test, steel_recipe])

assembler_recipes = []
iron_plate_recipe = Recipe("Iron_Plate", {"iron_ingot": 2}, {"iron_plate": 1, "coal": 40}, 1) # for testing
assembler_recipes.extend([iron_plate_recipe])