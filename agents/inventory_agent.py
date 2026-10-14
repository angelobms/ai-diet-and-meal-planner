"""Inventory agent: validates and cleans the user's grocery list."""
import json
from typing import List

from models import InventoryResponse
from services.llm_client import LLMClient


class InventoryAgent:
    """Asks the LLM to drop blank or non-cookable entries."""

    def __init__(self):
        self.llm = LLMClient()

    def run(self, items: List[str]) -> InventoryResponse:
        """Return the usable items from `items` with a confirmation message."""
        prompt = (
            f"You are a kitchen assistant. Given the JSON array of ingredients:\n"
            f"{json.dumps(items)}\n"
            "Return a JSON object with:\n"
            "  usable_items: an array of ingredients that are non-empty and suitable for cooking "
            "(remove blank or invalid entries, trim whitespace),\n"
            "  message: a short confirmation string.\n"
            "Respond ONLY with valid JSON."
        )
        return InventoryResponse(**self.llm.call_model_json(prompt))
