# ProxmoxAI v0.1.0 — Experimental MVP / 实验性版本

**Pre-release — NOT production-ready / 预发布：尚不适合生产部署。**

ProxmoxAI is an open-source, approval-first AI copilot for Proxmox Virtual Environment.

ProxmoxAI 是开源 PVE AI 虚拟机管理助手，提供轻量级 Web 界面和可选自然语言指令解析，所有修改操作需经用户确认。

## Included / 已包含
- FastAPI backend and browser Web dashboard / FastAPI 与 Web 控制台
- QEMU VM inventory, status, start, graceful shutdown and snapshot API / QEMU 虚拟机列表、状态、开机、关机和快照
- One-time approval for mutating actions / 修改类操作的一次性确认
- VM ID allowlist and HTTPS PVE API token adapter / VM 白名单、HTTPS PVE Token 适配
- English/Chinese documentation and Docker Compose / 中英文文档、Docker Compose
- Read-only validation probe and test checklist / 只读联调脚本和验收清单

## Verified / 已验证
- GitHub Actions mock/API smoke tests / 模拟环境的 CI 测试

## Not verified / 尚未验证
- Operations on a real Proxmox VE host / 真实 PVE 主机上的操作
- Production security or reliability / 生产环境安全与可靠性

## Known limitations / 已知限制
No task completion polling, persistent audit logs, RBAC, multiuser support, LXC management or HA. A returned task UPID is NOT proof of task completion.

## Getting started / 快速开始
~~~bash
git clone https://github.com/a16689525392-prog/ProxmoxAI.git
cd ProxmoxAI
cp .env.example .env
# Replace APP_API_KEY with a strong unique secret in .env
docker compose up --build -d
~~~
Open http://127.0.0.1:8000. MOCK_MODE defaults to true.

For real PVE validation, follow [docs/PVE_REAL_WORLD_VALIDATION.md](docs/PVE_REAL_WORLD_VALIDATION.md) first.

MIT licensed. Not affiliated with Proxmox Server Solutions GmbH.
