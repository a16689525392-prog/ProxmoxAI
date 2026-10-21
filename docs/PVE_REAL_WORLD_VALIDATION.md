# Real PVE Validation / 真实 PVE 联调说明

**Current status: NOT TESTED on a real Proxmox VE host.**
**当前状态：尚未在真实 PVE 主机完成测试。**

## Safety / 安全前提

- Use a non-production lab and disposable QEMU test VMs. 在隔离环境和可丢弃的测试 VM 上执行。
- Create a dedicated privilege-separated API token restricted by Proxmox ACL to test VMs; application VM allowlists do NOT replace real ACLs. 请同时实施 PVE 权限控制和应用白名单。
- Keep TLS verification enabled and set your own strong APP_API_KEY. 必须验证 HTTPS 证书并使用强密钥。
- Never upload real secrets, .env, unredacted screenshots or logs. 切勿公开敏感信息。
- Before every mutating step, confirm the VM ID and node directly in PVE. 执行前人工核对目标机器。
- Have backups and console access; stop testing when unexpected behavior appears. 确保有备份和控制台访问。

## 1. Configure / 配置

Clone the repository. Copy .env.example to .env, then change:

~~~dotenv
MOCK_MODE=false
PVE_API_URL=https://pve.lab.example:8006
PVE_TOKEN_ID=proxmoxai@pve!mvp
PVE_TOKEN_SECRET=REPLACE_WITH_YOUR_PRIVATE_TOKEN
PVE_VERIFY_SSL=true
ALLOWED_VMIDS=101
APP_API_KEY=REPLACE_WITH_LONG_RANDOM_SECRET
~~~

These values are placeholders, not usable credentials. All selected VM IDs must be disposable test VMs.

## 2. Read-only validation / 只读校验

~~~bash
python -m pip install -e '.[dev]'
python scripts/pve_readonly_check.py
~~~

The script refuses mock mode or disabled TLS verification. It only calls the real provider's GET inventory and VM status endpoints. It must show PASS and at least one allowed VM before trying any action.

## 3. Action acceptance checklist / 操作验收

Run the web UI locally via docker compose up --build -d; open http://127.0.0.1:8000.
Use the real test VM only, and explicitly approve each action in the UI.

| Case | Operation | Pass criteria |
|---|---|---|
| PVE-01 | VM inventory / VM 列表 | Only allowlisted QEMU VMs returned |
| PVE-02 | VM status / 状态 | State matches native Proxmox UI |
| PVE-03 | Start / 开机 | From stopped -> running after a confirmed action |
| PVE-04 | Graceful shutdown / 关机 | From running -> stopped after a confirmed action |
| PVE-05 | Snapshot / 快照 | Named snapshot exists after task completes |
| PVE-06 | App allowlist / 白名单 | Non-allowlisted VM preview returns HTTP 403 |
| PVE-07 | Native PVE token ACL / 原生权限 | Forbidden VM access denied by PVE itself |
| PVE-08 | Approval replay / 确认令牌 | Reusing one approval returns HTTP 409 |
| PVE-09 | Failure behavior / 异常处理 | Failed request reported without implicit retry |

**Important:** Proxmox API often returns a UPID for asynchronous operations.
Receiving a UPID only means task submission, NOT completion. Confirm final task success in PVE and final VM state/snapshot before marking PASS.

## 4. Evidence / 证据

Complete docs/PVE_VALIDATION_REPORT_TEMPLATE.md and link redacted evidence in the validation Issue.
Do not mark the actual PVE integration verified until the entire relevant checklist is supported by test results.

## Known gaps / 已知限制

This version lacks task completion polling, persistent audit, multiuser authentication, high availability, migration and LXC control. Never expose the MVP directly to the public internet.

References: https://pve.proxmox.com/pve-docs/api-viewer/ and https://pve.proxmox.com/pve-docs/pveum-plain.html
