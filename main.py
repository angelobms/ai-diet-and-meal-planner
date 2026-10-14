"""FastAPI entrypoint for the AI Diet & Meal Planner.

Endpoints:
    GET  /           health check
    POST /inventory  clean a list of groceries (InventoryAgent)
    POST /diet       filter items by diet and suggest recipe ideas (DietAgent)
    POST /ask        inventory + diet in one call (ManagerAgent)
    POST /plan       turn a recipe idea into a full recipe (PlannerAgent)
    POST /recommend  /ask followed by /plan for up to five full recipes

LLM failures are logged and surfaced to the client as HTTP 502.
"""
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastapi import FastAPI, HTTPException

from app_logging import get_logger
from agents.diet_agent import DietAgent
from agents.inventory_agent import InventoryAgent
from agents.manager_agent import ManagerAgent
from agents.planner_agent import PlannerAgent
from models import (
    AskInput,
    AskResponse,
    DietInput,
    DietResponse,
    InventoryInput,
    InventoryResponse,
    PlanInput,
    RecipeResponse,
    RecommendInput,
    RecommendResponse,
)

app = FastAPI(title="AI Diet & Meal Planner")
logger = get_logger("app")

inventory_agent = InventoryAgent()
diet_agent = DietAgent()
manager_agent = ManagerAgent()
planner_agent = PlannerAgent()


@app.get("/")
async def health_check():
    """Return a static payload confirming the server is up."""
    return {"message": "Success!"}


@app.post("/inventory", response_model=InventoryResponse)
def inventory(data: InventoryInput):
    """Remove blank/invalid grocery entries and return the usable items."""
    logger.info("Received /inventory request: items=%s", data.items)
    try:
        result = inventory_agent.run(data.items)
        logger.info("/inventory response: usable_items=%s", result.usable_items)
        return result
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        logger.error("LLM request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")


@app.post("/diet", response_model=DietResponse)
def diet(data: DietInput):
    """Keep only diet-compatible items and suggest five recipe ideas."""
    logger.info("Received /diet request: items=%s, diet=%s", data.items, data.diet)
    try:
        result = diet_agent.run(data.items, data.diet)
        logger.info("/diet response: compatible_items=%s", result.compatible_items)
        return result
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        logger.error("LLM request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")


@app.post("/ask", response_model=AskResponse)
def ask(data: AskInput):
    """Run the inventory -> diet pipeline and return items plus suggestions."""
    logger.info("Received /ask request: items=%s, diet=%s", data.items, data.diet)
    try:
        result = manager_agent.run(data.items, data.diet)
        logger.info("/ask response: suggestions=%s", result.suggestions)
        return result
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        logger.error("LLM request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")


@app.post("/plan", response_model=RecipeResponse)
def plan(data: PlanInput):
    """Expand a basic recipe idea into a structured recipe with steps."""
    logger.info("Received /plan request: base_recipe=%s", data.base_recipe)
    try:
        result = planner_agent.run(data.base_recipe)
        logger.info("/plan response: title=%s", result.title)
        return result
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        logger.error("LLM request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")


@app.post("/recommend", response_model=RecommendResponse)
def recommend(data: RecommendInput):
    """Return up to `recipe_count` full recipes built from the user's pantry.

    Runs the /ask pipeline, then plans each suggestion concurrently since the
    planner calls are independent network-bound LLM requests.
    """
    logger.info(
        "Received /recommend request: items=%s, diet=%s, recipe_count=%d",
        data.items, data.diet, data.recipe_count,
    )
    try:
        ask_result = manager_agent.run(data.items, data.diet)
        ideas = ask_result.suggestions[: data.recipe_count]
        with ThreadPoolExecutor(max_workers=max(len(ideas), 1)) as pool:
            recipes = list(
                pool.map(lambda idea: planner_agent.run(idea, ask_result.diet_filtered), ideas)
            )
        logger.info("/recommend response: %d recipes returned", len(recipes))
        return RecommendResponse(recipes=recipes)
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        logger.error("LLM request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")
