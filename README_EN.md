# ProxmoxAI — English Documentation

[⬅ Project homepage](README.md) · [简体中文](README_ZH.md)

## Overview

**ProxmoxAI** is an open-source, safety-conscious AI copilot for [Proxmox Virtual Environment](https://www.proxmox.com/en/products/proxmox-virtual-environment/overview). It aims to make common virtual-machine operations approachable through a small web dashboard and natural-language commands, while retaining server-side policy checks and explicit human confirmation.

This is the **v0.1.0 experimental MVP**, not a production-ready infrastructure control plane and not an official Proxmox project. Mock-mode CI checks have passed, but **end-to-end operation against a real Proxmox VE server has not yet been verified**.

## Features

- **VM inventory and status:** view basic information for allowlisted QEMU virtual machines.
- **Start VM:** request startup for a stopped VM.
- **Graceful shutdown:** request guest shutdown for a running VM; guest support is required.
- **Create snapshot:** name and request a VM snapshot, subject to PVE storage, permissions and VM settings.
- **Natural-language planning:** a limited Chinese/English rule parser and optional OpenAI-compatible Chat Completions API. **The LLM cannot execute actions directly**.
- **Explicit approval:** mutating operations are previewed and require a time-limited, single-use approval token.
- **Mock mode:** explore the workflow without an existing PVE deployment.

## Architecture

```text
Browser Web UI
      │ X-API-Key
      ▼
FastAPI backend
      ├── Command planner (offline rules / optional LLM)
      ├── Server-side VM ID allowlist + state validation
      ├── Action preview + single-use human approval
      └── Proxmox VE REST API over HTTPS
```

Stack: Python, FastAPI, HTTPX, vanilla HTML/JavaScript and Docker Compose. The MVP targets **QEMU virtual machines**; LXC operations are not implemented.

## Quick start: Docker Compose

You need Docker and the Docker Compose plugin.

```bash
git clone https://github.com/a16689525392-prog/ProxmoxAI.git
cd ProxmoxAI
cp .env.example .env
```

Edit `.env`: **replace the sample `APP_API_KEY` with your own strong, randomly generated secret**. For the first run, keep:

```dotenv
MOCK_MODE=true
ALLOWED_VMIDS=101,102,103
```

Then run:

```bash
docker compose up --build -d
```

Open http://127.0.0.1:8000 and enter your `APP_API_KEY` to load the demo VM inventory.

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp` if needed.

### Local Python alternative

Requires Python 3.11+:

```bash
cp .env.example .env
python -m pip install -e ".[dev]"
python -m uvicorn proxmoxai.main:app --host 127.0.0.1 --port 8000
```

Edit `.env` before starting the server.

## Example commands

| Command | Result |
| --- | --- |
| `list vms` | Show VM inventory |
| `status vm 101` | Plan a status check |
| `start vm 102` | Plan start; approval required |
| `shutdown vm 101` | Plan graceful shutdown; approval required |
| `snapshot vm 101 named before_update` | Plan snapshot; approval required |

The offline parser currently recognizes only a limited set of phrases. Ambiguous target IDs, multiple VM IDs or negative instructions are rejected rather than guessed.

## Connecting a real PVE server — unverified

Start with disposable virtual machines in an isolated lab. **Do not connect production workloads** at this stage.

Set the following in `.env`:

```dotenv
MOCK_MODE=false
PVE_API_URL=https://YOUR_PVE_HOST:8006
PVE_TOKEN_ID=proxmoxai@pve!mvp
PVE_TOKEN_SECRET=REPLACE_WITH_REAL_TOKEN_SECRET
PVE_VERIFY_SSL=true
ALLOWED_VMIDS=101,102
```

Create a dedicated, least-privilege, privilege-separated PVE API token with only the needed permissions on the selected VM resources. Expected privileges include `VM.Audit`, `VM.PowerMgmt` and `VM.Snapshot` as applicable; verify actual requirements against your PVE version and resource configuration. An application-level `ALLOWED_VMIDS` list **does not replace PVE's own ACLs**.

Use a trusted HTTPS certificate and keep `PVE_VERIFY_SSL=true`. Never commit real tokens or `.env` to GitHub. Many PVE operations return an asynchronous task ID: **a submitted task does not mean that the requested operation completed successfully**.

## API reference (summary)

| Endpoint | Purpose |
| --- | --- |
| `GET /healthz` | Liveness probe |
| `GET /api/meta` | Mode and allowlist metadata |
| `GET /api/vms` | VM inventory |
| `POST /api/agent/plan` | Plan an operation from text |
| `POST /api/vms/{node}/{vmid}/preview` | Request preview and temporary approval token |
| `POST /api/actions/execute` | Consume one-time approval and submit an action |

Every `/api/*` endpoint requires the `X-API-Key` header. The UI is a single-admin demo; it is not a multi-user identity or role-management system.

## Tests

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The [GitHub Actions page](https://github.com/a16689525392-prog/ProxmoxAI/actions) shows the latest CI state.

## Limitations and roadmap

Not implemented: multi-user identity, durable audit history, asynchronous task completion tracking, multi-instance coordination, LXC management, migration or resource scheduling. Approval tokens currently live in process memory; they are lost on restart and unsuitable for horizontal scaling.

Planned next steps: verify against a real PVE lab → track asynchronous tasks to completion → improve error handling and logging → strengthen security and automated tests → improve the multilingual UI.

Please open an [Issue](https://github.com/a16689525392-prog/ProxmoxAI/issues) with reproducible feedback, and see [Security](SECURITY.md), [Contributing](CONTRIBUTING.md), and the [MIT License](LICENSE).
