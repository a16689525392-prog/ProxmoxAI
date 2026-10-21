# ProxmoxAI — 中文说明

[⬅ 返回项目主页](README.md) · [English](README_EN.md)

## 项目简介

**ProxmoxAI** 是一个面向 [Proxmox Virtual Environment](https://www.proxmox.com/en/products/proxmox-virtual-environment/overview)（PVE）的开源 AI 虚拟机管理助手。项目希望把常见的虚拟机运维任务转换为更加直观的 Web 操作和自然语言交互，同时通过服务端白名单、操作预览和一次性确认降低误操作风险。

当前版本是 **v0.1.0 实验性 MVP**，并非成熟的生产运维平台，也不是 Proxmox 官方产品。当前 CI 测试已在模拟环境通过，**真实 PVE 服务器上的端到端功能尚未验证**。

## 主要功能

- **虚拟机列表与状态查询：** 查看白名单内 VM 的基本信息、运行状态。
- **虚拟机开机：** 请求启动指定、已停止的 QEMU VM。
- **正常关机：** 请求对正在运行的 VM 执行 graceful shutdown；依赖客户机正确支持关机机制。
- **创建快照：** 对指定 VM 创建指定名称的快照；实际操作仍受 PVE 的存储、权限与 VM 配置限制。
- **自然语言计划：** 支持有限的中英文规则指令；可配置兼容 OpenAI Chat Completions 的模型 API 进行计划解析。**大模型不是操作执行者**。
- **操作确认：** 修改类操作先预览，用户确认后才提交给后端；预览凭证有效期有限且只能使用一次。
- **模拟模式：** 无需真实 PVE 环境即可体验基本闭环。

## 技术架构

```text
浏览器 Web UI
      │ X-API-Key
      ▼
FastAPI 后端
      ├── 自然语言计划（本地规则 / 可选 LLM）
      ├── VM ID 白名单与状态检查
      ├── 操作预览 + 一次性人工确认
      └── HTTPS Proxmox VE REST API
```

技术栈：Python、FastAPI、HTTPX、原生 HTML/JavaScript、Docker Compose。该版本主要针对 **QEMU 虚拟机**；LXC 管理尚未实现。

## 运行方式

### 方案一：Docker Compose（推荐体验模拟模式）

确保已安装 Docker 与 Compose 插件。

```bash
git clone https://github.com/a16689525392-prog/ProxmoxAI.git
cd ProxmoxAI
cp .env.example .env
```

编辑 `.env`，**把示例 APP_API_KEY 改成你自己生成的随机强密钥**，初次演示保留：

```dotenv
MOCK_MODE=true
ALLOWED_VMIDS=101,102,103
```

执行：

```bash
docker compose up --build -d
```

打开 http://127.0.0.1:8000 ，输入配置的 `APP_API_KEY`，加载模拟虚拟机列表。

Windows PowerShell 可以将 `cp .env.example .env` 换为 `Copy-Item .env.example .env`。

### 方案二：Python 本地启动

需要 Python 3.11+，在项目根目录运行：

```bash
cp .env.example .env
python -m pip install -e ".[dev]"
python -m uvicorn proxmoxai.main:app --host 127.0.0.1 --port 8000
```

注意：运行前同样需要编辑 `.env` 里的 API 密钥。

## 自然语言示例

| 中文指令 | 对应操作 |
| --- | --- |
| `列出所有虚拟机` | 查看 VM 列表 |
| `查询虚拟机 101 状态` | 状态计划 |
| `启动虚拟机 102` | 生成启动计划；需确认 |
| `关闭虚拟机 101` | 生成正常关机计划；需确认 |
| `给虚拟机 101 创建快照 名为 before_update` | 生成快照计划；需确认 |

目前本地规则解析只覆盖部分固定表达，不是任意中文命令都能识别。对于无法确认目标、涉及多个 VM ID 或包含否定词的命令，系统会拒绝或要求更明确的指令。

## 接入真实 PVE（尚未实机验证）

先在**隔离测试环境**使用可随时恢复的虚拟机，不要直接接入生产服务器。

编辑 `.env`：

```dotenv
MOCK_MODE=false
PVE_API_URL=https://YOUR_PVE_HOST:8006
PVE_TOKEN_ID=proxmoxai@pve!mvp
PVE_TOKEN_SECRET=REPLACE_WITH_REAL_TOKEN_SECRET
PVE_VERIFY_SSL=true
ALLOWED_VMIDS=101,102
```

在 PVE 中创建权限隔离的专用 API Token，并仅针对被允许的 VM 授予必需权限。当前操作预计涉及 `VM.Audit`、`VM.PowerMgmt`、`VM.Snapshot` 等权限；实际所需权限请以安装版本的 PVE API 文档和资源授权检查为准。服务端的 `ALLOWED_VMIDS` **不能代替** PVE 自身的访问控制。

建议配置可信的 HTTPS 证书，保持 `PVE_VERIFY_SSL=true`；切勿将 Token、`.env` 文件或生产日志上传到 GitHub。PVE API 操作通常会返回任务 ID，**收到任务 ID 不等于任务完成成功**。

## API 概览

| 接口 | 用途 |
| --- | --- |
| `GET /healthz` | 服务存活检查 |
| `GET /api/meta` | 模式与允许的 VM 信息 |
| `GET /api/vms` | 查询 VM 列表 |
| `POST /api/agent/plan` | 把指令解析为操作计划 |
| `POST /api/vms/{node}/{vmid}/preview` | 请求预览及临时确认令牌 |
| `POST /api/actions/execute` | 消费一次性令牌、提交操作 |

除 `/healthz` 外，`/api/*` 接口均需 `X-API-Key` 请求头。Web UI 不是多用户认证系统，暂不具备生产级审计或细粒度角色权限。

## 测试

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

GitHub Actions 也会运行自动化测试；请在 [Actions](https://github.com/a16689525392-prog/ProxmoxAI/actions) 页面查看最新状态。

## 已知限制与路线图

当前尚不具备多用户管理、数据库持久化审计、任务执行完成状态追踪、HA 协调、LXC 控制、迁移和资源智能调度。确认令牌存储于进程内存，重启将丢失，不适合多副本部署。

后续计划：真实 PVE 版本联调 → 异步任务完成状态跟踪 → 更完善的异常处理与日志 → 基于测试的安全加固 → 多语言界面优化。

欢迎通过 [Issues](https://github.com/a16689525392-prog/ProxmoxAI/issues) 反馈实际问题，并阅读 [安全说明](SECURITY.md) 与 [贡献指南](CONTRIBUTING.md)。

本项目遵循 [MIT 许可证](LICENSE)。
