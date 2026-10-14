import json
import requests
from hstest import StageTest, CheckResult, dynamic_test
import docker
import re


class FastAPIStageTest(StageTest):
    BASE_IMAGE = "ai-diet-planner:latest"
    BASE_URL = "http://localhost:8000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = None
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            self.client = None
            print(f"Error initializing Docker client: {e}")


    @dynamic_test()
    def test_docker_container(self):
        if self.client is None:
            return CheckResult.wrong("Docker client not initialized. Is Docker installed and running?")

        try:
            containers = self.client.containers.list(all=True)
        except docker.errors.DockerException as e:
            return CheckResult.wrong(f"Cannot connect to Docker daemon: {e}")

        for c in containers:
            if c.name == "ai-diet-planner":
                image = c.attrs["Config"]["Image"]
                if image != self.BASE_IMAGE:
                    return CheckResult.wrong(f"Container 'ai-diet-planner' uses image '{image}', expected '{self.BASE_IMAGE}'.")
                if not c.attrs["State"]["Running"]:
                    return CheckResult.wrong("Container 'ai-diet-planner' is not running.")
                ports = c.attrs["NetworkSettings"]["Ports"] or {}
                if "8000/tcp" not in ports:
                    return CheckResult.wrong("Container 'ai-diet-planner' is not exposing port 8000.")
                return CheckResult.correct()
        return CheckResult.wrong("No container named 'ai-diet-planner' found.")


    @dynamic_test(time_limit=120_000)
    def test_root(self):
        try:
            response = requests.get(f"{self.BASE_URL}/")
        except requests.exceptions.ConnectionError:
            return CheckResult.wrong("Cannot connect to the server at 'http://localhost:8000'. Ensure the FastAPI app is running.")

        if response.status_code != 200:
            return CheckResult.wrong(f"Expected status code 200, but got {response.status_code}.")

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            return CheckResult.wrong("Response is not valid JSON.")
        
        if "Success" not in response_data.get("message", ""):
            return CheckResult.wrong(f"Expected 'Success' in the 'message' value, but got {response_data.get('message', '')}.")

        return CheckResult.correct()

    @dynamic_test(time_limit=120_000)
    def test_ask(self):
        payload = {
            "items": ["tomato", "chicken breast", "spinach", ""],
            "diet": "vegan"
        }

        try:
            response = requests.post(f"{self.BASE_URL}/ask", json=payload)
        except requests.exceptions.ConnectionError:
            return CheckResult.wrong("Cannot connect to the server at 'http://localhost:8000'. Ensure the FastAPI app is running.")

        if response.status_code != 200:
            return CheckResult.wrong(f"Expected status code 200, but got {response.status_code}.")

        try:
            body = response.json()
        except json.JSONDecodeError:
            return CheckResult.wrong("Response is not valid JSON.")

        if "usable_items" not in body:
            return CheckResult.wrong("'usable_items' key is missing in response.")
        if "diet_filtered" not in body:
            return CheckResult.wrong("'diet_filtered' key is missing in response.")
        if "suggestions" not in body:
            return CheckResult.wrong("'suggestions' key is missing in response.")
        if not isinstance(body.get("suggestions"), list):
            return CheckResult.wrong("'suggestions' should be a list.")

        return CheckResult.correct()

    @dynamic_test(time_limit=120_000)
    def test_plan(self):
        payload = {"base_recipe": "Vegan Salad"}
        
        try:
            response = requests.post(f"{self.BASE_URL}/plan", json=payload)
        except requests.exceptions.ConnectionError:
            return CheckResult.wrong("Cannot connect to the server at 'http://localhost:8000'. Ensure the FastAPI app is running.")

        if response.status_code != 200:
            return CheckResult.wrong(f"Expected status code 200, but got {response.status_code}.")

        try:
            body = response.json()
        except json.JSONDecodeError:
            return CheckResult.wrong("Response is not valid JSON.")

        if "title" not in body:
            return CheckResult.wrong("'title' key is missing in response.")
        if "ingredients" not in body or not isinstance(body["ingredients"], list):
            return CheckResult.wrong("'ingredients' key is missing or is not a list.")
        if "steps" not in body or not isinstance(body["steps"], list):
            return CheckResult.wrong("'steps' key is missing or is not a list.")

        return CheckResult.correct()

    @dynamic_test(time_limit=120_000)
    def test_recommend(self):
        payload = {
            "items": ["egg", "flour", "sugar", "milk"],
            "diet": "vegetarian",
            "recipe_count": 2
        }

        try:
            response = requests.post(f"{self.BASE_URL}/recommend", json=payload)
        except requests.exceptions.ConnectionError:
            return CheckResult.wrong("Cannot connect to the server at 'http://localhost:8000'. Ensure the FastAPI app is running.")

        if response.status_code != 200:
            return CheckResult.wrong(f"Expected status code 200, but got {response.status_code}.")

        try:
            body = response.json()
        except json.JSONDecodeError:
            return CheckResult.wrong("Response is not valid JSON.")

        if "recipes" not in body or not isinstance(body["recipes"], list):
            return CheckResult.wrong("'recipes' key is missing or is not a list.")
        if len(body["recipes"]) != 2:
            return CheckResult.wrong("Expected 2 recipes in the response but got a different number.")

        first = body["recipes"][0]
        if "title" not in first:
            return CheckResult.wrong("First recipe is missing 'title'.")
        if "ingredients" not in first:
            return CheckResult.wrong("First recipe is missing 'ingredients'.")
        if "steps" not in first:
            return CheckResult.wrong("First recipe is missing 'steps'.")

        return CheckResult.correct()

    @dynamic_test()
    def test_logging(self):
        if self.client is None:
            return CheckResult.wrong("Docker client not initialized. Is Docker installed and running?")
        try:
            containers = self.client.containers.list(all=True)
        except docker.errors.DockerException as e:
            return CheckResult.wrong(f"Cannot connect to Docker daemon: {e}")

        for c in containers:
            if c.name != "ai-diet-planner":
                continue

            try:
                raw = c.logs(stdout=True, tail=100)
                logs = raw.decode(errors="replace")
            except docker.errors.DockerException as e:
                return CheckResult.wrong(f"Failed to fetch logs: {e}")

            expected_patterns = [
                r".*Received /ask request",
                r".*Received /plan request",
                r".*Received /recommend request",
                r".*POST /ask HTTP/1.1",
                r".*INFO - /plan response",
                r".*INFO - /recommend response",
                r".*POST /plan HTTP/1.1",
                r".*POST /recommend HTTP/1.1",
            ]

            missing = [pattern for pattern in expected_patterns if not re.findall(pattern, logs)]
            if missing:
                missing_list = "\n".join(f"- {m}" for m in missing)
                return CheckResult.wrong(
                    f"Logs are missing expected entries:\n{missing_list}"
                )

            return CheckResult.correct()

        return CheckResult.wrong("No container named 'ai-diet-planner' found.")


if __name__ == '__main__':
    FastAPIStageTest().run_tests()