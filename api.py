"""CrewAI API client — kickoff and poll for chat responses."""

import json

import requests
import streamlit as st


def _api_url() -> str:
    return st.secrets["CRW_API_URL"].rstrip("/")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {st.secrets['CRW_API_TOKEN']}",
        "Content-Type": "application/json",
    }


def api_request(endpoint: str, method: str = "GET", data: dict | None = None) -> dict | None:
    """Make an authenticated request to the CrewAI API."""
    url = f"{_api_url()}/{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=_headers(), timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=_headers(), json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None


def kickoff_chat(user_message: str, chat_id: str) -> str | None:
    """Send a message to CrewAI and return the kickoff_id."""
    payload = {
        "inputs": {
            "user_message": user_message,
            "id": chat_id,
        }
    }
    result = api_request("kickoff", method="POST", data=payload)
    if result and "kickoff_id" in result:
        return result["kickoff_id"]
    return None


def poll_status(kickoff_id: str) -> dict:
    """Poll the status endpoint and return the parsed status dict.

    Returns a dict with keys:
        state: str  — "PENDING", "RUNNING", "SUCCESS", "FAILURE", "TIMEOUT"
        result: dict | None — parsed result when state is SUCCESS
        last_executed_task: str | None — description of current progress
    """
    data = api_request(f"status/{kickoff_id}")
    if not data:
        return {"state": "ERROR", "result": None, "last_executed_task": None}

    state = data.get("state", "UNKNOWN")
    last_task = data.get("last_executed_task")

    parsed_result = None
    if state == "SUCCESS" and data.get("result"):
        raw = data["result"]
        # Handle result as either a JSON string or a dict
        if isinstance(raw, str):
            try:
                parsed_result = json.loads(raw)
            except json.JSONDecodeError:
                parsed_result = {"response": raw}
        elif isinstance(raw, dict):
            parsed_result = raw

    return {"state": state, "result": parsed_result, "last_executed_task": last_task}
