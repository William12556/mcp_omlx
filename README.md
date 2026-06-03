Created: 2026 June 03

# oMLX MCP Server

A Model Context Protocol (MCP) server providing access to a local oMLX inference server. Exposes seven tools covering inference, inspection, and model lifecycle management.

## Table of Contents

1. [Overview](<#1 overview>)
2. [Requirements](<#2 requirements>)
3. [Installation](<#3 installation>)
4. [Configuration](<#4 configuration>)
5. [Tools](<#5 tools>)
6. [Client Registration](<#6 client registration>)
7. [Documentation](<#7 documentation>)
8. [License](<#8 license>)
9. [Version History](<#9 version history>)

---

## 1 Overview

oMLX is a local LLM inference server for Apple Silicon that provides OpenAI-compatible and Anthropic-compatible API endpoints, plus an admin API for model management. This MCP server wraps a subset of those endpoints as MCP tools, enabling an MCP client to list models, inspect load state, run inference, and load or unload models.

The server communicates with oMLX over HTTP and runs as a local stdio subprocess of the MCP client.

[Return to Table of Contents](<#table of contents>)

---

## 2 Requirements

- Python 3.10 or later
- A running oMLX server reachable over HTTP
- The `mcp`, `httpx`, and `pydantic` packages (installed automatically)

[Return to Table of Contents](<#table of contents>)

---

## 3 Installation

From the repository root:

```bash
pip install -e .
```

This installs the package and the `omlx-mcp` console entry point.

[Return to Table of Contents](<#table of contents>)

---

## 4 Configuration

Configuration is provided through environment variables.

| Variable | Default | Description |
|---|---|---|
| `OMLX_BASE_URL` | `http://127.0.0.1:8000` | oMLX server root. A trailing `/v1` is accepted and normalized. |
| `OMLX_API_KEY` | (unset) | Optional. Sent as a Bearer token on every request when set. |
| `OMLX_TIMEOUT` | `300` | Request timeout in seconds. |

[Return to Table of Contents](<#table of contents>)

---

## 5 Tools

| Tool | Method and Path | Purpose |
|---|---|---|
| `omlx_list_models` | `GET /v1/models` | List available models by id or alias. |
| `omlx_model_status` | `GET /admin/api/models` | Report load state, memory size, and context window. |
| `omlx_chat` | `POST /v1/chat/completions` | Generate a chat completion. |
| `omlx_completion` | `POST /v1/completions` | Generate a text completion. |
| `omlx_embeddings` | `POST /v1/embeddings` | Generate embeddings. |
| `omlx_load_model` | `POST /admin/api/models/{id}/load` | Load a model into memory. |
| `omlx_unload_model` | `POST /admin/api/models/{id}/unload` | Unload a model from memory. |

Detailed tool schemas are in the API reference. See [Documentation](<#7 documentation>).

[Return to Table of Contents](<#table of contents>)

---

## 6 Client Registration

Register the server with an MCP client by adding an entry to the client configuration. An example is provided in `mcp.example.json`:

```json
{
  "mcpServers": {
    "omlx": {
      "command": "omlx-mcp",
      "env": {
        "OMLX_BASE_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

[Return to Table of Contents](<#table of contents>)

---

## 7 Documentation

Additional documentation is in the `doc/` directory:

- API Reference: tool schemas, parameters, and response shapes.
- Deployment Guide: registration, authentication, and troubleshooting.

[Return to Table of Contents](<#table of contents>)

---

## 8 License

MIT License. See `LICENSE`.

[Return to Table of Contents](<#table of contents>)

---

## 9 Version History

| Version | Date | Description |
|---|---|---|
| 0.1.0 | 2026 June 03 | Initial release. Seven tools: inference, inspection, lifecycle. |

[Return to Table of Contents](<#table of contents>)

---

Copyright (c) 2026 William Watson. MIT License.
