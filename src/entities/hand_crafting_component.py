# entities.hand_crafting_component
from constants.recipes import smelter_recipes, assembler_recipes

class HandcraftingComponent:
    """Lets the player craft items by hand, straight out of their own
    inventory, without needing a machine."""

    def __init__(self, inventory):
        self.inventory = inventory
        self.recipes = smelter_recipes + assembler_recipes
        self.selected_recipe_index = 0

    def get_selected_recipe(self):
        if not self.recipes:
            return None
        return self.recipes[self.selected_recipe_index]

    def check_craft_status(self, recipe=None):
        """Checks whether a recipe could be crafted right now, without
        actually crafting it. Tries it on a fake copy of the inventory
        first, so nothing real changes."""
        recipe = recipe or self.get_selected_recipe()
        if not recipe or not self.inventory.has_enough_items(recipe.inputs):
            return "no_inputs"

        scratch = self.inventory.clone()
        scratch.try_remove_items(recipe.inputs)
        for item_id, amount in recipe.outputs.items():
            if not scratch.try_add_items(item_id, amount):
                return "no_space"

        return "ok"

    def try_craft_selected(self):
        """Actually crafts the selected recipe, if it's possible: takes
        out the ingredients and adds in the result. Returns False and
        changes nothing if it isn't possible."""
        recipe = self.get_selected_recipe()
        if self.check_craft_status(recipe) != "ok":
            return False

        self.inventory.try_remove_items(recipe.inputs)

        for item_id, amount in recipe.outputs.items():
            self.inventory.try_add_items(item_id, amount)

        return True