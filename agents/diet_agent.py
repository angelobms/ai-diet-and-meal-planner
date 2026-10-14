"""Diet agent: filters ingredients by diet and suggests recipe ideas."""
import json
from typing import List

from models import DietResponse
from services.llm_client import LLMClient


class DietAgent:
    """Applies dietary rules (vegan, keto, ...) to a list of ingredients."""

    def __init__(self):
        self.llm = LLMClient()

    def run(self, items: List[str], diet: str) -> DietResponse:
        """Return compatible items and exactly five recipe ideas for `diet`."""
        prompt = (
            f"You are a nutrition assistant. Given the JSON array of ingredients:\n"
            f"{json.dumps(items)}\n"
            f"and the diet: {diet}\n"
            "Return a JSON object with:\n"
            "  compatible_items: an array containing only the ingredients that fit the diet "
            "(keep the original names),\n"
            "  suggested_recipe_ideas: an array of exactly five recipe name strings that "
            "use the compatible items and follow the diet.\n"
            "Respond ONLY with valid JSON."
        )
        return DietResponse(**self.llm.call_model_json(prompt))
