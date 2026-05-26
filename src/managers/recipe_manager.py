class RecipeManager:
    def __init__(self):
        """
        Almacena y gestiona las recetas de crafteo de RushCraft.
        Cada receta define los ingredientes requeridos y el resultado.
        """
        self.recipes = {
            "stone_pickaxe": {
                "name": "Pico de Piedra",
                "ingredients": {"wood": 20, "stone": 15},
                "result": {"item_id": "stone_pickaxe", "quantity": 1}
            },
            "stone_axe": {
                "name": "Hacha de Piedra",
                "ingredients": {"wood": 30, "stone": 10},
                "result": {"item_id": "stone_axe", "quantity": 1}
            }
        }

    def check_and_craft(self, recipe_id, inventory):
        """
        Verifica si el inventario tiene los materiales suficientes.
        Si es así, consume los ingredientes y añade el ítem fabricado.
        """
        if recipe_id not in self.recipes:
            print("La receta no existe.")
            return False

        recipe = self.recipes[recipe_id]
        ingredients = recipe["ingredients"]

        # 1. VERIFICACIÓN: Comprobar si hay suficiente de cada material
        for item_id, required_qty in ingredients.items():
            # Buscamos cuánto tiene el jugador de este material en total
            current_qty = inventory.get_total_quantity(item_id)
            if current_qty < required_qty:
                print(f"Materiales insuficientes para {recipe['name']}. Necesitas {required_qty} de {item_id}.")
                return False

        # 2. CONSUMO: Si pasó la verificación, descontamos los materiales
        for item_id, required_qty in ingredients.items():
            inventory.remove_item_amount(item_id, required_qty)

        # 3. ENTREGA: Añadimos el nuevo objeto crafteado al inventario
        result = recipe["result"]
        inventory.add_item(result["item_id"], result["quantity"])
        print(f"¡Has fabricado con éxito: {recipe['name']}!")
        return True