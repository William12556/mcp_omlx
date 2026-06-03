# SPDX-License-Identifier: MIT
"""oMLX MCP server.

Exposes the oMLX local inference server (OpenAI-compatible API plus admin
model-management routes) to MCP clients. Provides inference, inspection, and
model lifecycle tools.

Configuration via environment variables:
    OMLX_BASE_URL   oMLX server root (default: http://127.0.0.1:8000).
                    A trailing "/v1" is accepted and normalized away.
    OMLX_API_KEY    Optional. Sent as a Bearer token on every request.
    OMLX_TIMEOUT    Optional request timeout in seconds (default: 300).
"""

from __future__ import annotations

import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Constants and configuration
# --------------------------------------------------------------------------- #

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 300.0

V1_PREFIX = "/v1"
ADMIN_PREFIX = "/admin/api"


def _base_url() -> str:
    """Return the normalized oMLX server root without a trailing slash or /v1."""
    raw = os.environ.get("OMLX_BASE_URL", DEFAULT_BASE_URL).strip()
    raw = raw.rstrip("/")
    if raw.endswith("/v1"):
        raw = raw[: -len("/v1")]
    return raw


def _timeout() -> float:
    """Return the configured request timeout in seconds."""
    try:
        return float(os.environ.get("OMLX_TIMEOUT", DEFAULT_TIMEOUT))
    except ValueError:
        return DEFAULT_TIMEOUT


def _headers() -> Dict[str, str]:
    """Build request headers, including auth when OMLX_API_KEY is set."""
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("OMLX_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


mcp = FastMCP("omlx_mcp")


# --------------------------------------------------------------------------- #
# Shared HTTP helpers
# --------------------------------------------------------------------------- #


def _handle_error(e: Exception) -> str:
    """Format an exception as an actionable error string."""
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401:
            return (
                "Error: Authentication failed (401). Set OMLX_API_KEY to match "
                "the server's --api-key, or disable key verification in the "
                "admin panel for localhost."
            )
        if code == 404:
            return (
                "Error: Not found (404). Check the model id is correct and the "
                "endpoint exists on this oMLX version."
            )
        if code == 422:
            return f"Error: Invalid request (422). Server response: {e.response.text}"
        return f"Error: Request failed with status {code}. Response: {e.response.text}"
    if isinstance(e, httpx.ConnectError):
        return (
            f"Error: Could not connect to oMLX at {_base_url()}. Confirm the "
            "server is running and OMLX_BASE_URL is correct."
        )
    if isinstance(e, httpx.TimeoutException):
        return (
            "Error: Request timed out. Inference or model loading may exceed "
            "OMLX_TIMEOUT; increase it for large models."
        )
    return f"Error: Unexpected {type(e).__name__}: {e}"


async def _request(method: str, path: str, json_body: Optional[dict] = None) -> str:
    """Perform an HTTP request against oMLX and return the response text.

    Args:
        method: HTTP method ("GET" or "POST").
        path: Full path beginning with "/" (e.g. "/v1/models").
        json_body: Optional JSON payload for POST requests.

    Returns:
        str: JSON-formatted response body, or an actionable error string.
    """
    url = f"{_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.request(
                method, url, headers=_headers(), json=json_body
            )
            response.raise_for_status()
            try:
                return json.dumps(response.json(), indent=2)
            except json.JSONDecodeError:
                return response.text
    except Exception as e:  # noqa: BLE001 - converted to actionable message
        return _handle_error(e)


# --------------------------------------------------------------------------- #
# Input models
# --------------------------------------------------------------------------- #


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    JSON = "json"
    MARKDOWN = "markdown"


class ListModelsInput(BaseModel):
    """Input for listing models via the OpenAI-compatible endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ModelStatusInput(BaseModel):
    """Input for querying detailed model status via the admin endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    model_id: Optional[str] = Field(
        default=None,
        description="Optional model id to filter to a single model "
        "(e.g. 'devstral'). When omitted, all models are returned.",
        max_length=200,
    )


class ChatMessage(BaseModel):
    """A single chat message."""

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")

    role: str = Field(
        ...,
        description="Message role: 'system', 'user', or 'assistant'.",
        min_length=1,
    )
    content: str = Field(..., description="Message text content.")


class ChatInput(BaseModel):
    """Input for a chat completion."""

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")

    model: str = Field(
        ...,
        description="Model id or alias as reported by omlx_list_models "
        "(e.g. 'devstral', 'magistral').",
        min_length=1,
        max_length=200,
    )
    messages: List[ChatMessage] = Field(
        ..., description="Conversation messages in order.", min_length=1
    )
    temperature: Optional[float] = Field(
        default=None, description="Sampling temperature.", ge=0.0, le=2.0
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate.", ge=1, le=131072
    )


class CompletionInput(BaseModel):
    """Input for a text completion."""

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")

    model: str = Field(
        ..., description="Model id or alias.", min_length=1, max_length=200
    )
    prompt: str = Field(..., description="Prompt text to complete.", min_length=1)
    temperature: Optional[float] = Field(
        default=None, description="Sampling temperature.", ge=0.0, le=2.0
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate.", ge=1, le=131072
    )


class EmbeddingsInput(BaseModel):
    """Input for generating embeddings."""

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")

    model: str = Field(
        ...,
        description="Embedding model id or alias (e.g. 'bge-m3').",
        min_length=1,
        max_length=200,
    )
    input: List[str] = Field(
        ..., description="One or more strings to embed.", min_length=1
    )


class ModelActionInput(BaseModel):
    """Input for load/unload model lifecycle actions."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    model_id: str = Field(
        ...,
        description="Model id to load or unload, as reported by "
        "omlx_model_status (e.g. 'devstral').",
        min_length=1,
        max_length=200,
    )


# --------------------------------------------------------------------------- #
# Tools: inference and inspection (OpenAI-compatible)
# --------------------------------------------------------------------------- #


@mcp.tool(
    name="omlx_list_models",
    annotations={
        "title": "List oMLX Models",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def omlx_list_models(params: ListModelsInput) -> str:
    """List models available to oMLX via the OpenAI-compatible endpoint.

    Calls GET /v1/models. Returns the models the server exposes, by id or
    alias. For load state, memory size, and context window, use
    omlx_model_status instead.

    Args:
        params (ListModelsInput): No fields.

    Returns:
        str: JSON object with a "data" array of model entries, or an error
            string.
    """
    return await _request("GET", f"{V1_PREFIX}/models")


@mcp.tool(
    name="omlx_model_status",
    annotations={
        "title": "Get oMLX Model Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def omlx_model_status(params: ModelStatusInput) -> str:
    """Report detailed model status via the oMLX admin endpoint.

    Calls GET /admin/api/models. Returns richer data than omlx_list_models,
    including load state (loaded, is_loading), estimated memory size, pinned
    state, engine and model type, and per-model settings such as the maximum
    context window.

    Args:
        params (ModelStatusInput): Optional fields:
            - model_id (Optional[str]): Filter to a single model id.

    Returns:
        str: JSON object with a "models" array. When model_id is given and
            present, only that entry is returned. Returns an error string on
            failure.
    """
    result = await _request("GET", f"{ADMIN_PREFIX}/models")
    if params.model_id is None or result.startswith("Error:"):
        return result
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return result
    models = data.get("models", []) if isinstance(data, dict) else []
    match = [m for m in models if m.get("id") == params.model_id]
    if not match:
        available = ", ".join(m.get("id", "?") for m in models) or "(none)"
        return (
            f"Error: Model '{params.model_id}' not found. "
            f"Available models: {available}."
        )
    return json.dumps({"models": match}, indent=2)


@mcp.tool(
    name="omlx_chat",
    annotations={
        "title": "oMLX Chat Completion",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def omlx_chat(params: ChatInput) -> str:
    """Generate a chat completion from a loaded oMLX model.

    Calls POST /v1/chat/completions (non-streaming). If the target model is
    not loaded, oMLX loads it on demand, which may take time for large models.

    Args:
        params (ChatInput): Fields:
            - model (str): Model id or alias.
            - messages (List[ChatMessage]): Ordered messages, each with
              'role' and 'content'.
            - temperature (Optional[float]): Sampling temperature.
            - max_tokens (Optional[int]): Maximum tokens to generate.

    Returns:
        str: JSON chat completion response with a "choices" array, or an
            error string.
    """
    body: Dict[str, Any] = {
        "model": params.model,
        "messages": [m.model_dump() for m in params.messages],
        "stream": False,
    }
    if params.temperature is not None:
        body["temperature"] = params.temperature
    if params.max_tokens is not None:
        body["max_tokens"] = params.max_tokens
    return await _request("POST", f"{V1_PREFIX}/chat/completions", body)


@mcp.tool(
    name="omlx_completion",
    annotations={
        "title": "oMLX Text Completion",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def omlx_completion(params: CompletionInput) -> str:
    """Generate a raw text completion from a loaded oMLX model.

    Calls POST /v1/completions (non-streaming). Use omlx_chat for chat-format
    models; this tool targets base or instruct models via a single prompt.

    Args:
        params (CompletionInput): Fields:
            - model (str): Model id or alias.
            - prompt (str): Prompt text.
            - temperature (Optional[float]): Sampling temperature.
            - max_tokens (Optional[int]): Maximum tokens to generate.

    Returns:
        str: JSON completion response with a "choices" array, or an error
            string.
    """
    body: Dict[str, Any] = {
        "model": params.model,
        "prompt": params.prompt,
        "stream": False,
    }
    if params.temperature is not None:
        body["temperature"] = params.temperature
    if params.max_tokens is not None:
        body["max_tokens"] = params.max_tokens
    return await _request("POST", f"{V1_PREFIX}/completions", body)


@mcp.tool(
    name="omlx_embeddings",
    annotations={
        "title": "oMLX Embeddings",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def omlx_embeddings(params: EmbeddingsInput) -> str:
    """Generate embeddings from a loaded oMLX embedding model.

    Calls POST /v1/embeddings. Requires an embedding-type model (e.g. bge-m3).

    Args:
        params (EmbeddingsInput): Fields:
            - model (str): Embedding model id or alias.
            - input (List[str]): Strings to embed.

    Returns:
        str: JSON embeddings response with a "data" array of vectors, or an
            error string.
    """
    body = {"model": params.model, "input": params.input}
    return await _request("POST", f"{V1_PREFIX}/embeddings", body)


# --------------------------------------------------------------------------- #
# Tools: model lifecycle (admin)
# --------------------------------------------------------------------------- #


@mcp.tool(
    name="omlx_load_model",
    annotations={
        "title": "Load oMLX Model",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def omlx_load_model(params: ModelActionInput) -> str:
    """Load a model into memory via the oMLX admin endpoint.

    Calls POST /admin/api/models/{id}/load. Loading a large model consumes
    memory and may evict least-recently-used models per the server's policy.

    Args:
        params (ModelActionInput): Fields:
            - model_id (str): Model id to load.

    Returns:
        str: JSON status acknowledgment, or an error string.
    """
    return await _request("POST", f"{ADMIN_PREFIX}/models/{params.model_id}/load")


@mcp.tool(
    name="omlx_unload_model",
    annotations={
        "title": "Unload oMLX Model",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def omlx_unload_model(params: ModelActionInput) -> str:
    """Unload a model from memory via the oMLX admin endpoint.

    Calls POST /admin/api/models/{id}/unload. This frees memory and makes the
    model unavailable for inference until it is loaded again. In-flight
    requests against the model may be affected.

    Args:
        params (ModelActionInput): Fields:
            - model_id (str): Model id to unload.

    Returns:
        str: JSON status acknowledgment, or an error string.
    """
    return await _request("POST", f"{ADMIN_PREFIX}/models/{params.model_id}/unload")


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
