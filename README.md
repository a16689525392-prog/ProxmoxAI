# ProxmoxAI ⚡

**Safety-first, open-source AI copilot for Proxmox VE.**

> v0.1.0 experimental MVP. Mock mode verified; real-hypervisor integration requires testing. Not affiliated with Proxmox Server Solutions GmbH.

## Features

- VM inventory and state query
- Explicitly approved start, graceful shutdown, snapshot
- Chinese/English command planning (offline rules)
- Optional OpenAI-compatible LLM interpretation
- VM ID allowlist, API-token-based PVE access, no shell
- Lightweight Web UI, Docker Compose deployment

## Quick start

```sh
cp .env.example .env
# Set a unique APP_API_KEY before running outside a private local test.
docker compose up --build -d
```

Visit http://127.0.0.1:8000 and enter the key from `.env`. Use mock VMs 101, 102 and 103. Demo commands: `列出所有虚拟机`, `启动虚拟机 102`, `关闭虚拟机 101`, `给虚拟机 101 创建快照 名为 before_update`.

Without Docker: `pip install -e . && uvicorn proxmoxai.main:app --host 127.0.0.1 --port 8000` after copying the example environment.

## Real Proxmox VE

In `.env`, set `MOCK_MODE=false`, `PVE_API_URL=https://YOUR_PVE:8006`, `PVE_TOKEN_ID`, `PVE_TOKEN_SECRET`, and the approved comma-separated `ALLOWED_VMIDS`. Use privilege-separated token with least privileges: `VM.Audit`, `VM.PowerMgmt`, `VM.Snapshot` for the selected VM paths. Keep TLS verification enabled. **Only test with disposable VMs first.** No production use or internet exposure is recommended at this stage.

## Architecture

Browser → FastAPI → rule/LLM command planner → server-side allowlist + VM state check → **explicit one-time approval** → Proxmox REST API. Planning alone never executes.

## API

- `GET /healthz` — liveness
- `GET /api/meta` — configuration
- `GET /api/vms` — allowed inventory
- `POST /api/agent/plan` — request `{"text":"启动虚拟机 102"}`
- `POST /api/vms/{node}/{vmid}/preview` — `{"action":"start"}`
- `POST /api/actions/execute` — `{"approval_id":"..."}`

All `/api/*` endpoints require `X-API-Key`.

## Security

- Credentials stay server-side. Never commit `.env` or tokens.
- Default Compose binding is loopback only.
- Single-user, in-memory approval ledger: not high availability, not production hardened.
- No arbitrary shell access, forced stops, deletes, or rollbacks.
- Contributions and security disclosures are welcome through GitHub Issues (avoid publishing exploits or credentials).

## License

MIT. Copyright (c) 2026 ProxmoxAI contributors.
