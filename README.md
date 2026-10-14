# AI Diet & Meal Planner

A FastAPI service built from small, single-purpose LLM agents that clean a pantry list, apply a diet, and generate complete recipes. Agents exchange structured JSON validated with Pydantic.

## Agents

| Agent | File | Role |
|---|---|---|
| `InventoryAgent` | `agents/inventory_agent.py` | Removes blank/invalid grocery entries |
| `DietAgent` | `agents/diet_agent.py` | Filters items by diet and suggests five recipe ideas |
| `ManagerAgent` | `agents/manager_agent.py` | Chains Inventory -> Diet into one call |
| `PlannerAgent` | `agents/planner_agent.py` | Expands a recipe idea into title, ingredients and numbered steps |

All LLM calls go through `services/llm_client.py` (`LLMClient`), which requests JSON-mode output from an OpenAI-compatible chat completions API.

## Project layout

```
├── agents/            # the four agents
├── services/
│   └── llm_client.py  # single gateway for LLM requests
├── app_logging.py     # centralized logger (get_logger)
├── main.py            # FastAPI app and routes
├── models.py          # Pydantic request/response schemas
├── requirements.txt
└── Dockerfile
```

> The logger lives in `app_logging.py`, not `logging.py`: a file named `logging.py` next to `main.py` shadows Python's standard library module and breaks uvicorn.

## Configuration

Create a `.env` file in the project root with one of:

```
GROQ_API_KEY=your-groq-key      # uses Groq (llama-3.1-8b-instant)
OPENAI_API_KEY=your-openai-key  # used when no Groq key is set (gpt-4o-mini)
```

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Run it from this folder; the server listens on <http://localhost:8000> (interactive docs at `/docs`).

## Run with Docker

```bash
docker build -t ai-diet-planner .
docker run --name ai-diet-planner --env-file .env -p 8000:8000 ai-diet-planner:latest
```

The API key is passed at runtime and is not baked into the image. Request and response logs appear in `docker logs ai-diet-planner`.

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/` | – | `{"message": "Success!"}` |
| POST | `/inventory` | `{"items": [...]}` | `{"usable_items": [...], "message": "..."}` |
| POST | `/diet` | `{"items": [...], "diet": "vegan"}` | `{"compatible_items": [...], "suggested_recipe_ideas": [...]}` |
| POST | `/ask` | `{"items": [...], "diet": "keto"}` | `{"usable_items": [...], "diet_filtered": [...], "suggestions": [...]}` |
| POST | `/plan` | `{"base_recipe": "Vegan Stir Fry"}` | `{"title", "ingredients", "steps": [{"step_number", "instruction"}]}` |
| POST | `/recommend` | `{"items": [...], "diet": "vegan", "recipe_count": 2}` | `{"recipes": [<recipe>, ...]}` |

`recipe_count` is optional (default 5, range 1-5). If the LLM call fails or returns invalid JSON, endpoints respond with HTTP 502.

### Examples

```bash
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"items":["tomato","chicken","spinach"],"diet":"keto"}'

curl -X POST http://localhost:8000/recommend \
  -H 'Content-Type: application/json' \
  -d '{"items":["tofu","bell pepper","garlic","oil"],"diet":"vegan","recipe_count":2}'
```

Diet filtering and recipes are produced by the LLM, so results can vary between runs.
