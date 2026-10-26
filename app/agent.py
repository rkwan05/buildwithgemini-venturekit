# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

import json
from pathlib import Path
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from app.firestore_tools import get_growth_play, list_growth_plays, save_growth_play
from app.fx_tools import convert_currency_pricing
from app.image_tools import generate_growth_play_image
from app.video_tools import generate_growth_play_video


from functools import cached_property
from google.genai import Client

MODEL = "gemini-3.8-flash"


class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> Client:
        return Client(vertexai=True, location="global")



def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


INSTRUCTION = """You are VentureKit, an expert Fractional CFO and Growth Strategist for small businesses.

Your mission is to help small business owners diagnose unit economics, discover high-margin revenue plays, and execute strategic growth plans.

You have access to a Firestore-backed repository of proven Growth Plays:
- `list_growth_plays`: Search or list proven growth plays by category (e.g. 'Pricing & Packaging', 'Revenue Expansion', 'Retention & Retention', 'Cost Optimization').
- `get_growth_play`: Retrieve detailed implementation steps, timelines, and expected margin lift for a specific play.
- `save_growth_play`: Create or save custom growth strategies tailored to the user's business.
- `generate_growth_play_image`: Generate marketing visuals or promotional cards for an item/growth play using gemini-3.1-flash-lite-image. Saves the image to the Artifacts panel and uploads to public Cloud Storage, returning the public https URL.
- `convert_currency_pricing`: Convert service pricing, retainers, or cost figures between international currencies using live exchange rates.

You have a live, secure Python Code Execution Sandbox (Agent Engine Sandbox). Whenever you need to calculate financial metrics (such as CAGR, unit economics, gross margin lift, burn rate, runway, or pricing models), write and run Python code in the sandbox to compute the exact numbers before providing your strategic recommendations.

When owners ask about growing revenue, improving profit margins, or fixing cash flow, query the growth plays database to ground your advice in real actionable plays with specific margin lift and timeline estimates. When they want to visualize a play, create a promotional flyer, or design an announcement banner, call `generate_growth_play_image`. When discussing international clients, foreign suppliers, or multi-currency pricing, use `convert_currency_pricing`.
"""

# Configure sandbox from existing sandbox or deployment_metadata.json
_metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
_agent_engine_id = None
if _metadata_path.exists():
    try:
        with open(_metadata_path) as f:
            _meta = json.load(f)
            _agent_engine_id = _meta.get("remote_agent_runtime_id")
    except Exception:
        pass

# Point directly to the active sandbox environment under this Agent Engine
_sandbox_name = (
    f"{_agent_engine_id}/sandboxEnvironments/6255618079917604864"
    if _agent_engine_id
    else None
)

code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=_sandbox_name,
    agent_engine_resource_name=_agent_engine_id,
)

# WRITE: after each turn, send the session to Memory Bank for durable extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="root_agent",
    model=GlobalGemini(
        model=MODEL,
    ),
    instruction=INSTRUCTION,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        list_growth_plays,
        get_growth_play,
        save_growth_play,
        convert_currency_pricing,
        generate_growth_play_image,
        generate_growth_play_video,
        get_weather,
        get_current_time,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

# Hardcoded project and Memory Bank ID for redeployment on Agent Platform
PROJECT_ID = "qwiklabs-gcp-04-c8fa96deb89c"
LOCATION = "us-central1"
MEMORY_BANK_ID = "8552514088138178560"


def memory_service_builder() -> VertexAiMemoryBankService:
    """Builds the VertexAiMemoryBankService for Agent Runtime deployment."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )

