"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.
"""

import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google.protobuf.json_format import MessageToDict, ParseDict
import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import AgentCard, Message, Part, Role, SendMessageRequest

load_dotenv()

RESOURCE = os.environ.get(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/745655802959/locations/us-central1/reasoningEngines/7393400134043697152",
)
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

_A2UI_MIME = "application/json+a2ui"

_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Reuse ONE A2A context per user so the agent remembers the conversation.
_contexts: dict[str, str] = {}
_card: AgentCard | None = None


async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        data = resp.json()
        card = ParseDict(data, AgentCard(), ignore_unknown_fields=True)
        for iface in card.supported_interfaces:
            iface.url = A2A_BASE
        _card = card
    return _card


def _extract_parts(parts) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        if hasattr(p, "DESCRIPTOR"):
            d = MessageToDict(p, preserving_proto_field_name=True)
            if "text" in d and d["text"]:
                out.append({"kind": "text", "text": d["text"]})
            elif "data" in d and d["data"] is not None:
                meta = d.get("metadata", {})
                mime = meta.get("mimeType") if isinstance(meta, dict) else None
                if mime == _A2UI_MIME:
                    out.append({"kind": "a2ui", "data": d["data"]})
            elif "url" in d and d["url"]:
                out.append({"kind": "text", "text": d["url"]})
        else:
            text = getattr(p, "text", None) or (p.get("text") if isinstance(p, dict) else None)
            if text:
                out.append({"kind": "text", "text": text})
    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        config = ClientConfig(
            httpx_client=client,
            supported_protocol_bindings=["JSONRPC", "HTTP_JSON"],
        )
        factory = ClientFactory(config)
        a2a_client = factory.create(card)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=message)],
        )
        if _contexts.get(user_id):
            msg.context_id = _contexts[user_id]

        send_req = SendMessageRequest(message=msg)

        got_artifact_update = False
        async for event in a2a_client.send_message(send_req):
            if hasattr(event, "task") and event.HasField("task"):
                if event.task.context_id:
                    _contexts[user_id] = event.task.context_id
            if hasattr(event, "status_update") and event.HasField("status_update"):
                if event.status_update.context_id:
                    _contexts[user_id] = event.status_update.context_id
                if not got_artifact_update and event.status_update.status.HasField("message"):
                    parts.extend(_extract_parts(event.status_update.status.message.parts))
            elif hasattr(event, "artifact_update") and event.HasField("artifact_update"):
                got_artifact_update = True
                parts = _extract_parts(event.artifact_update.artifact.parts)

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


# Serve the chat UI
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
