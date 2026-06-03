Created: 2026 June 03

# oMLX MCP Server: Deployment Guide

Registration, authentication, and troubleshooting for the oMLX MCP server.

## Table of Contents

1. [Prerequisites](<#1 prerequisites>)
2. [Installation](<#2 installation>)
3. [Registration](<#3 registration>)
4. [Authentication](<#4 authentication>)
5. [Verification](<#5 verification>)
6. [Troubleshooting](<#6 troubleshooting>)
7. [Version History](<#7 version history>)

---

## 1 Prerequisites

- A running oMLX server. Confirm the base URL and port, typically `http://127.0.0.1:8000`.
- Python 3.10 or later available to the MCP client.

[Return to Table of Contents](<#table of contents>)

---

## 2 Installation

From the repository root:

```bash
pip install -e .
```

To verify the entry point resolves:

```bash
omlx-mcp --help
```

A stdio MCP server has no interactive output of its own; the client launches it as a subprocess.

[Return to Table of Contents](<#table of contents>)

---

## 3 Registration

Add an entry to the MCP client configuration. The example below matches `mcp.example.json`:

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

If `omlx-mcp` is not on the client's `PATH`, use an absolute path to the entry point, or invoke the module:

```json
{
  "command": "python",
  "args": ["-m", "omlx_mcp"]
}
```

[Return to Table of Contents](<#table of contents>)

---

## 4 Authentication

If oMLX was started with `--api-key`, set `OMLX_API_KEY` in the server environment block. The value is sent as a Bearer token on every request.

```json
"env": {
  "OMLX_BASE_URL": "http://127.0.0.1:8000",
  "OMLX_API_KEY": "your-secret-key"
}
```

For localhost-only deployments, key verification can be disabled in the oMLX admin panel, in which case `OMLX_API_KEY` may be omitted.

[Return to Table of Contents](<#table of contents>)

---

## 5 Verification

After registration, restart the MCP client and confirm the seven tools are listed. A first call to `omlx_list_models` confirms connectivity. A call to `omlx_model_status` confirms access to the admin API.

[Return to Table of Contents](<#table of contents>)

---

## 6 Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| `Could not connect` | Server not running or wrong URL | Confirm oMLX is running and `OMLX_BASE_URL` is correct. |
| `Authentication failed (401)` | Missing or wrong key | Set `OMLX_API_KEY` to match the server's `--api-key`. |
| `Not found (404)` | Wrong model id or endpoint absent | Check the id via `omlx_model_status`; confirm the oMLX version. |
| `Request timed out` | Large model load exceeds timeout | Increase `OMLX_TIMEOUT`. |

[Return to Table of Contents](<#table of contents>)

---

## 7 Version History

| Version | Date | Description |
|---|---|---|
| 0.1.0 | 2026 June 03 | Initial deployment guide. |

[Return to Table of Contents](<#table of contents>)

---

Copyright (c) 2026 William Watson. MIT License.
