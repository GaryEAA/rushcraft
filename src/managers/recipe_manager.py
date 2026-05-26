import json

class RecipeManager:
    def __init__(self):
        """
        Gestiona las recetas cargándolas dinámicamente 
        desde un archivo JSON externo, evitando datos duros en código.
        """
        # Cargamos las recetas desde el archivo externo de forma dinámica
        self.recipes = self.load_recipes_data()

    def load_recipes_data(self):
        """ Lee el archivo JSON de recetas de crafteo"""
        try:
            with open("data/recipes.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                print("RecipeManager: Recetas cargadas exitosamente desde JSON.")
                return data.get("recipes", {})
        except Exception as e:
            print(f"Error al cargar data/recipes.json: {e}. Usando respaldo interno.")
            # Respaldo de emergencia idéntico por seguridad si el JSON falla
            return {
                "axe": {
                    "name": "Hacha de Madera (Backup)",
                    "ingredients": {"wood": 10},
                    "result": {"item_id": "axe", "quantity": 1}
                },
                "pickaxe": {
                    "name": "Pico de Madera (Backup)",
                    "ingredients": {"wood": 10},
                    "result": {"item_id": "pickaxe", "quantity": 1}
                }
            }

    def check_and_craft(self, recipe_id, inventory):
        """
        Verifica si el inventario tiene los materiales suficientes.
        Si es así, consume los ingredientes y añade el ítem fabricado o aplica la mejora.
        """
        if recipe_id not in self.recipes:
            print("La receta no existe.")
            return False

        recipe = self.recipes[recipe_id]
        
        # VALIDACIÓN PREVIA EXCLUSIVA PARA MOCHILAS JERÁRQUICAS:
        if recipe_id == "backpack_expedition" and inventory.backpack_level != 2:
            print("Error: Necesitas fabricar primero la Mochila de Montañero.")
            return False
            
        if recipe_id == "backpack_leather" and inventory.backpack_level >= 2:
            print("Ya tienes esta mochila o una mejor equipada.")
            return False
        if recipe_id == "backpack_expedition" and inventory.backpack_level >= 3:
            print("Ya tienes la mochila al nivel máximo.")
            return False

        ingredients = recipe["ingredients"]

        # 1. VERIFICACIÓN: Comprobar si hay suficiente de cada material
        for item_id, required_qty in ingredients.items():
            current_qty = inventory.get_total_quantity(item_id)
            if current_qty < required_qty:
                print(f"Materiales insuficientes para {recipe['name']}. Necesitas {required_qty} de {item_id}.")
                return False

        # 2. CONSUMO: Si pasó la verificación, descontamos los materiales
        for item_id, required_qty in ingredients.items():
            inventory.remove_item_amount(item_id, required_qty)

        # 3. ENTREGA O APLICACIÓN DE MEJORA:
        result = recipe["result"]
        result_id = result["item_id"]

        if result_id == "backpack_leather":
            inventory.backpack_level = 2
            print("¡Mochila mejorada con éxito: Mochila de Montañero! slots expandidos.")
        elif result_id == "backpack_expedition":
            inventory.backpack_level = 3
            print("¡Mochila mejorada con éxito: Mochila de Expedición! Capacidad máxima alcanzada.")
        else:
            # Flujo normal para herramientas u otros objetos físicos
            inventory.add_item(result_id, result["quantity"])
            print(f"¡Has fabricado con éxito: {recipe['name']}!")

        return True