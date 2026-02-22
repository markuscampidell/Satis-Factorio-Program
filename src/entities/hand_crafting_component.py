# entities/hand_crafting_component.py
from constants.recipes import smelter_recipes, assembler_recipes

class HandcraftingComponent:
    def __init__(self, inventory):
        self.inventory = inventory
        self.recipes = smelter_recipes + assembler_recipes
        self.selected_recipe_index = 0
        self.current_recipe = None
        self.timer = 0

    def get_selected_recipe(self):
        if not self.recipes:
            return None
        return self.recipes[self.selected_recipe_index]

    def try_craft_selected(self):
        recipe = self.get_selected_recipe()
        if not recipe: return False

        if not self.inventory.has_enough_items(recipe.inputs): return False

        self.inventory.try_remove_items(recipe.inputs)

        for item_id, amount in recipe.outputs.items():
            self.inventory.try_add_items(item_id, amount)

        return True

    def update(self, dt=0):
        if not self.current_recipe:return

        self.timer -= dt
        if self.timer <= 0:
            self.inventory.try_remove_items(self.current_recipe.inputs)
            for item_id, amount in self.current_recipe.outputs.items():
                self.inventory.try_add_items(item_id, amount)

            self.current_recipe = None
            self.timer = 0