import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.agent import app, MODEL

async def run_query(prompt: str):
    print(f"\n==========================================")
    print(f"Model: {MODEL}")
    print(f"User:  {prompt}")
    print(f"==========================================")
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="app", user_id="test_user")
    runner = Runner(app=app, session_service=session_service)
    
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    async for event in runner.run_async(user_id="test_user", session_id=session.id, new_message=msg):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"Agent: {part.text.strip()}")

async def main():
    await run_query("What is the weather in San Francisco?")
    await run_query("What time is it in SF?")
    await run_query("Introduce yourself in one sentence.")

if __name__ == "__main__":
    asyncio.run(main())
