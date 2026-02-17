# CrewAI Chat Frontend

A Streamlit chat interface for interacting with a deployed CrewAI Enterprise (AMP) crew via its REST API.

## Architecture

```
User  -->  Streamlit UI  --POST /kickoff-->  CrewAI AMP API  -->  Deployed Crew
                         <--GET /status/<id>--  (poll every 2s)
```

The frontend sends user messages to a deployed crew's `/kickoff` endpoint, then polls `/status/{kickoff_id}` every 2 seconds (up to 5 minutes) until the crew returns a result. Task progress is displayed in real time as the crew executes.

## How It Works

1. **User sends a message** — the Streamlit chat input captures the prompt.
2. **Kickoff** — `api.py` sends a `POST /kickoff` request with the message and a chat ID. The API returns a `kickoff_id`.
3. **Poll** — `app.py` polls `GET /status/{kickoff_id}` every 2 seconds. While waiting, it displays the currently executing task name from the status response.
4. **Display** — once the crew finishes (`state: SUCCESS`), the result is rendered as the assistant's reply and persisted to local SQLite.

## Building the Backend Flow

This frontend expects a **CrewAI Flow** (not a bare Crew) with the `@persist` decorator, deployed to CrewAI Enterprise (AMP). The `@persist` decorator saves and restores state keyed by the flow's `id` field, which the frontend supplies as a UUID per chat session — enabling multi-turn conversations with full message history.

### API Contract

**Request** — `POST /kickoff` with:

```json
{
  "inputs": {
    "user_message": "the user's current message",
    "id": "uuid-identifying-the-conversation"
  }
}
```

- `user_message` — the current user input.
- `id` — a UUID identifying the conversation. `@persist` uses this to resume state across turns.

**Response** — `GET /status/{kickoff_id}` returns `state`, `result`, and `last_executed_task`.

- `result` must contain `{"response": "assistant text", "id": "uuid"}`.
- `last_executed_task` is shown as a progress indicator while the flow is running.
- **Critical**: the `"response"` key is required — the frontend reads `result.get("response", "")` (see `app.py:267`).

### Flow State Model

Your Pydantic state must include `user_message` and `message_history` at minimum:

```python
from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    role: str        # "user" or "assistant"
    content: str

class FlowState(BaseModel):
    user_message: str = ""
    message_history: List[Message] = []
    # Add domain-specific fields as needed
```

> **Note:** `id` is a built-in field on `Flow` — no need to declare it in your state model. `@persist` uses `self.state.id` automatically.

### Minimal Flow Example

A copy-paste-ready skeleton you can extend with your own crews and logic:

```python
from crewai.flow.flow import Flow, listen, router, start
from crewai.flow.persistence import persist

@persist  # Saves/restores state keyed by self.state.id
class ChatFlow(Flow[FlowState]):

    def add_message(self, role: str, content: str):
        """Add a message to the message history."""
        self.state.message_history.append(
            Message(role=role, content=content)
        )

    @start()
    def receive_message(self):
        """Add the incoming user message to history."""
        self.add_message("user", self.state.user_message)

    @router(receive_message)
    def classify_intent(self):
        """Route to the appropriate handler based on intent."""
        # Replace with your own classification logic
        return "general_response"

    @listen("general_response")
    def handle_general(self):
        """Generate a response (replace with your crew kickoff)."""
        reply = "Hello! This is a placeholder response."
        self.add_message("assistant", reply)
        return {"response": reply, "id": str(self.state.id)}


def kickoff():
    """Entry point required by CrewAI Enterprise."""
    flow = ChatFlow()
    return flow.kickoff()
```

Every `@listen` handler that produces a final answer **must** return a dict with a `"response"` key and the flow's `"id"`.

### Reference Implementation

See [deep_research_paper_chat](https://github.com/crewAIInc/deep_research_paper_chat) for a complete working example of a multi-turn chat flow with `@persist`, crew integration, and this frontend.

## Project Structure

```
chat_frontend/
├── app.py                  # Streamlit UI — chat view, history, sidebar, polling loop
├── api.py                  # CrewAI API client — kickoff_chat() and poll_status()
├── db.py                   # SQLite persistence — chats and messages tables
├── main.py                 # Entry point (placeholder)
├── assets/
│   └── crewai_logo.svg     # Logo used in sidebar and empty state
├── .streamlit/
│   ├── config.toml         # Streamlit theme (dark, coral accent)
│   └── secrets.toml        # API URL and Bearer token (not committed)
├── pyproject.toml           # Project metadata and dependencies
└── uv.lock                  # Locked dependencies
```

## Setup & Run

### Prerequisites

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- A deployed crew on CrewAI Enterprise (AMP)

### Install dependencies

```bash
uv sync
```

### Configure secrets

Create `.streamlit/secrets.toml` with your deployed crew's API URL and token:

```toml
CRW_API_URL = "https://your-deployed-crew.crewai.com"
CRW_API_TOKEN = "your-bearer-token"
```

You can find these values in the CrewAI Enterprise dashboard after deploying your crew.

### Run the app

```bash
uv run streamlit run app.py
```

## CrewAI Enterprise References

- [Enterprise Introduction](https://docs.crewai.com/en/enterprise/introduction)
- [Prepare for Deployment](https://docs.crewai.com/en/enterprise/guides/prepare-for-deployment)
- [Deploy to AMP](https://docs.crewai.com/en/enterprise/guides/deploy-to-amp)
- [API Reference](https://docs.crewai.com/en/api-reference/introduction)
- [Webhook Streaming](https://docs.crewai.com/en/enterprise/features/webhook-streaming)

## Alternative: Webhook Streaming

This frontend uses **polling** — it hits `/status/{kickoff_id}` every 2 seconds until the crew finishes. Polling is simple to implement and works well for most use cases.

CrewAI Enterprise also supports **webhook streaming**, where you subscribe to a webhook URL and the server pushes status events to your app as they happen. Compared to polling:

- **Push-based delivery** — task progress and final results arrive as soon as they're available, rather than on the next poll interval.
- **No polling loop** — the server sends events to you, so there's no need for repeated `/status` calls.
- **Real-time streaming** — crew execution steps can be surfaced immediately as they occur.

To use webhooks, you would register a webhook URL when calling `/kickoff` and set up a server endpoint (or use Streamlit's experimental WebSocket support) to receive incoming status events. See the [Webhook Streaming docs](https://docs.crewai.com/en/enterprise/features/webhook-streaming) for details.
