"""Planner agent: turns a recipe idea into a full structured recipe."""
from typing import Any, List, Optional

from models import RecipeResponse, RecipeStep
from services.llm_client import LLMClient


def _text(value: Any) -> str:
    """Flatten an LLM-provided ingredient/step (string or object) into a string."""
    if isinstance(value, dict):
        for key in ("instruction", "step", "description", "text", "name", "ingredient"):
            if value.get(key):
                return str(value[key]).strip()
        return " ".join(str(v) for v in value.values()).strip()
    return str(value).strip()


class PlannerAgent:
    """Generates a complete recipe (title, ingredients, numbered steps) via the LLM."""

    def __init__(self):
        self.llm = LLMClient()

    def run(self, base_recipe: str, available_items: Optional[List[str]] = None) -> RecipeResponse:
        """Plan a recipe for `base_recipe`, optionally favoring `available_items`.

        The LLM output is normalized: ingredients/steps may arrive as strings or
        objects, and steps are renumbered from 1 so numbering is always valid.
        """
        pantry = ""
        if available_items:
            pantry = f"Prefer using these available ingredients: {available_items}.\n"
        prompt = (
            "You are a professional chef. Create a complete, ready-to-cook recipe for: "
            f"\"{base_recipe}\".\n"
            f"{pantry}"
            "Return a JSON object with exactly these fields:\n"
            "  title: string, the recipe name,\n"
            "  ingredients: array of strings, e.g. [\"tofu\", \"garlic\"],\n"
            "  steps: array of objects, each {\"step_number\": integer starting at 1, "
            "\"instruction\": string}.\n"
            "Respond ONLY with valid JSON."
        )
        data = self.llm.call_model_json(prompt)

        ingredients = [t for t in (_text(i) for i in data.get("ingredients", [])) if t]
        steps = [
            RecipeStep(step_number=n, instruction=text)
            for n, text in enumerate(
                (t for t in (_text(s) for s in data.get("steps", [])) if t), start=1
            )
        ]
        return RecipeResponse(
            title=str(data.get("title") or base_recipe).strip(),
            ingredients=ingredients,
            steps=steps,
        )
