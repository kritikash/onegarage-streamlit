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

## Potential Improvements: Webhook Streaming

The current implementation uses polling — the frontend hits `/status/{kickoff_id}` every 2 seconds until the crew finishes. This works but introduces latency (up to 2 seconds per update) and generates unnecessary API calls while the crew is still working.

CrewAI Enterprise supports **webhook streaming**, which pushes status updates to your app as they happen instead of requiring repeated polling. With webhooks:

- **Lower latency** — task progress and final results arrive as soon as they're available.
- **Fewer API calls** — no more polling loop; the server pushes events to you.
- **Better UX** — real-time streaming of crew execution steps.

To implement this, you would register a webhook URL when calling `/kickoff` and set up a server endpoint (or use Streamlit's experimental WebSocket support) to receive incoming status events. See the [Webhook Streaming docs](https://docs.crewai.com/en/enterprise/features/webhook-streaming) for details.
