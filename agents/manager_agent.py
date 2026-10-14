"""Manager agent: orchestrates the inventory and diet agents."""
from typing import List

from agents.diet_agent import DietAgent
from agents.inventory_agent import InventoryAgent
from models import AskResponse


class ManagerAgent:
    """Chains InventoryAgent -> DietAgent into a single workflow."""

    def __init__(self):
        self.inventory_agent = InventoryAgent()
        self.diet_agent = DietAgent()

    def run(self, items: List[str], diet: str) -> AskResponse:
        """Clean `items`, then filter the result by `diet` and collect suggestions."""
        inventory = self.inventory_agent.run(items)
        diet_result = self.diet_agent.run(inventory.usable_items, diet)
        return AskResponse(
            usable_items=inventory.usable_items,
            diet_filtered=diet_result.compatible_items,
            suggestions=diet_result.suggested_recipe_ideas,
        )
