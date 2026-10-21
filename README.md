# ⚡ ProxmoxAI

**English** · An open-source, approval-first AI copilot for Proxmox VE. Manage virtual machines from a lightweight web dashboard or natural-language commands—without giving the language model unrestricted control of your hypervisor.

**简体中文** · ProxmoxAI 是一个面向 Proxmox VE 的开源 AI 虚拟机管理助手。通过 Web 控制台和自然语言指令，完成虚拟机状态查询、开机、正常关机与快照操作；所有会改变虚拟机状态的操作都需要用户明确确认。

**[English documentation](README_EN.md) | [中文完整说明](README_ZH.md)**

> **Status / 项目状态：v0.1.0 · Experimental MVP / 实验性最小可行产品。** Mock-mode CI tests have passed; real PVE hardware integration has **not** been verified. / 模拟环境的 CI 已通过；**尚未完成真实 PVE 服务器联调**。Not affiliated with Proxmox Server Solutions GmbH. / 非 Proxmox 官方项目。

## ✨ Features / 核心功能

| English | 中文 |
| --- | --- |
| Web dashboard and VM inventory | Web 仪表盘与虚拟机列表 |
| Natural-language command planning (offline rules, optional LLM) | 自然语言指令解析（本地规则，可选大模型） |
| Start VM, graceful shutdown, create snapshot | 虚拟机开机、正常关机、创建快照 |
| Explicit one-time approval for changes | 修改类操作需要一次性人工确认 |
| VM ID allowlist and token-based PVE API access | VM ID 白名单与 PVE API Token 接入 |
| Mock mode and Docker Compose | 模拟演示模式与 Docker Compose 部署 |

## 🚀 Quick start / 快速开始

**Prerequisites / 环境要求：** Docker + Docker Compose.

```bash
git clone https://github.com/a16689525392-prog/ProxmoxAI.git
cd ProxmoxAI
cp .env.example .env
# IMPORTANT: Replace APP_API_KEY in .env with your own strong secret.
docker compose up --build -d
```

Open / 打开 **http://127.0.0.1:8000** and enter the `APP_API_KEY` from `.env`.

Default `MOCK_MODE=true`: try VM IDs `101`, `102`, and `103` without connecting to a Proxmox server. / 默认启用模拟模式，不需要真实 PVE 服务器即可体验。

**Example commands / 指令示例：**
- `列出所有虚拟机` / `list vms`
- `启动虚拟机 102` / `start vm 102`
- `关闭虚拟机 101` / `shutdown vm 101`
- `给虚拟机 101 创建快照 名为 before_update` / `snapshot vm 101 named before_update`

## 🛡️ Safety / 安全设计

`Browser → FastAPI → Command planner → VM allowlist / state check → One-time approval → Proxmox VE API`

The planner only *proposes* an operation; it cannot perform it by itself. / AI 只生成操作计划，不能绕过后端权限检查与用户确认直接执行。

**Do not expose this experimental MVP to the public internet or use it on production VMs.** Set a strong `APP_API_KEY`, restrict network access, keep TLS verification enabled, and give PVE API tokens only minimal VM permissions. / **不要将实验版本直接暴露到公网或用于生产虚拟机。** 请使用强密钥、限制访问范围，并遵循最小权限原则。

## 📚 Documentation / 文档

- 🇨🇳 [中文：完整介绍、部署教程、PVE 接入、安全说明](README_ZH.md)
- 🇬🇧 [English: overview, setup, PVE configuration, security](README_EN.md)
- [Security Policy / 安全策略](SECURITY.md)
- [Contributing / 贡献指南](CONTRIBUTING.md)
- [Changelog / 更新日志](CHANGELOG.md)

## 🤝 Contribute / 参与贡献

Issues and pull requests are welcome. Please report reproducible bugs and propose improvements. / 欢迎提交 Issue、Pull Request、Bug 复现与功能建议。

**License / 开源许可证：** [MIT](LICENSE).
