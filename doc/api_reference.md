Created: 2026 June 03

# oMLX MCP Server: API Reference

Tool schemas, parameters, and response shapes for the oMLX MCP server.

## Table of Contents

1. [Conventions](<#1 conventions>)
2. [Inspection Tools](<#2 inspection tools>)
3. [Inference Tools](<#3 inference tools>)
4. [Lifecycle Tools](<#4 lifecycle tools>)
5. [Error Handling](<#5 error handling>)
6. [References](<#6 references>)
7. [Version History](<#7 version history>)

---

## 1 Conventions

All tools return a JSON-formatted string on success, or a string beginning with `Error:` on failure. Model ids and aliases are those reported by `omlx_list_models` and `omlx_model_status`.

[Return to Table of Contents](<#table of contents>)

---

## 2 Inspection Tools

### 2.1 omlx_list_models

Calls `GET /v1/models`. Lists models the server exposes, by id or alias.

Parameters: none.

Returns: a JSON object with a `data` array of model entries.

### 2.2 omlx_model_status

Calls `GET /admin/api/models`. Reports richer data than `omlx_list_models`, including load state (`loaded`, `isLoading`), estimated memory size, pinned state, engine and model type, and per-model settings such as the maximum context window.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model_id` | string | No | Filter to a single model id. When omitted, all models are returned. |

Returns: a JSON object with a `models` array. When `model_id` is supplied and present, only that entry is returned; if absent, an error string lists the available ids.

[Return to Table of Contents](<#table of contents>)

---

## 3 Inference Tools

### 3.1 omlx_chat

Calls `POST /v1/chat/completions` with `stream` set to false. If the target model is not loaded, oMLX loads it on demand.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model` | string | Yes | Model id or alias. |
| `messages` | array | Yes | Ordered messages, each with `role` and `content`. |
| `temperature` | number | No | Sampling temperature, 0.0 to 2.0. |
| `max_tokens` | integer | No | Maximum tokens to generate. |

Returns: a JSON chat completion response with a `choices` array.

### 3.2 omlx_completion

Calls `POST /v1/completions` with `stream` set to false. Targets base or instruct models via a single prompt.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model` | string | Yes | Model id or alias. |
| `prompt` | string | Yes | Prompt text to complete. |
| `temperature` | number | No | Sampling temperature, 0.0 to 2.0. |
| `max_tokens` | integer | No | Maximum tokens to generate. |

Returns: a JSON completion response with a `choices` array.

### 3.3 omlx_embeddings

Calls `POST /v1/embeddings`. Requires an embedding-type model.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model` | string | Yes | Embedding model id or alias. |
| `input` | array | Yes | One or more strings to embed. |

Returns: a JSON embeddings response with a `data` array of vectors.

[Return to Table of Contents](<#table of contents>)

---

## 4 Lifecycle Tools

### 4.1 omlx_load_model

Calls `POST /admin/api/models/{id}/load`. Loading a large model consumes memory and may evict least-recently-used models per the server's policy.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model_id` | string | Yes | Model id to load. |

Returns: a JSON status acknowledgment.

### 4.2 omlx_unload_model

Calls `POST /admin/api/models/{id}/unload`. Frees memory and makes the model unavailable for inference until loaded again.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model_id` | string | Yes | Model id to unload. |

Returns: a JSON status acknowledgment.

[Return to Table of Contents](<#table of contents>)

---

## 5 Error Handling

Tools convert exceptions to actionable strings. Recognized cases include authentication failure (401), not found (404), invalid request (422), connection failure, and timeout. All other cases return a generic message naming the exception type.

[Return to Table of Contents](<#table of contents>)

---

## 6 References

JUNDOT, 2026. *oMLX: LLM inference server with continuous batching and SSD caching for Apple Silicon* [online]. GitHub. Available from: https://github.com/jundot/omlx [Accessed 3 June 2026].

MODEL CONTEXT PROTOCOL, 2026. *Model Context Protocol specification* [online]. Available from: https://modelcontextprotocol.io [Accessed 3 June 2026].

[Return to Table of Contents](<#table of contents>)

---

## 7 Version History

| Version | Date | Description |
|---|---|---|
| 0.1.0 | 2026 June 03 | Initial API reference. |

[Return to Table of Contents](<#table of contents>)

---

Copyright (c) 2026 William Watson. MIT License.
