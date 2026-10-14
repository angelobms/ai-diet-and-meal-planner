"""Pydantic request and response schemas shared by the API and the agents."""
from typing import List

from pydantic import BaseModel, Field


class InventoryInput(BaseModel):
    """Request body for /inventory: raw grocery entries."""

    items: List[str]


class DietInput(BaseModel):
    """Request body for /diet: ingredients and the diet to apply (e.g. "vegan")."""

    items: List[str]
    diet: str


class AskInput(BaseModel):
    """Request body for /ask: raw items and a diet."""

    items: List[str]
    diet: str


class InventoryResponse(BaseModel):
    """Cleaned ingredient list and a short confirmation message."""

    usable_items: List[str]
    message: str


class DietResponse(BaseModel):
    """Diet-compatible ingredients and five recipe ideas."""

    compatible_items: List[str]
    suggested_recipe_ideas: List[str]


class AskResponse(BaseModel):
    """Combined pipeline output: cleaned items, diet-filtered items, suggestions."""

    usable_items: List[str]
    diet_filtered: List[str]
    suggestions: List[str]


class PlanInput(BaseModel):
    """Request body for /plan: the base recipe idea to expand."""

    base_recipe: str


class RecipeStep(BaseModel):
    """A single numbered cooking instruction."""

    step_number: int
    instruction: str


class RecipeResponse(BaseModel):
    """A complete recipe: title, ingredients and ordered steps."""

    title: str
    ingredients: List[str]
    steps: List[RecipeStep]


class RecommendInput(BaseModel):
    """Request body for /recommend. `recipe_count` is limited to 1-5."""

    items: List[str]
    diet: str
    recipe_count: int = Field(default=5, ge=1, le=5)


class RecommendResponse(BaseModel):
    """List of full recipes returned by /recommend."""

    recipes: List[RecipeResponse]
