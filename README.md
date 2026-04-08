# OpenClaw 本地部署指南（Windows）

本文档记录了在 Windows 10 + Git Bash (MINGW64) 环境下安装和部署 [OpenClaw](https://github.com/openclaw/openclaw) 个人 AI 助手的完整过程。

## 环境信息

| 项目 | 版本 |
|------|------|
| 操作系统 | Windows 10 (10.0.26200) |
| Shell | Git Bash (MINGW64) |
| Node.js | v25.9.0 |
| npm | 11.12.1 |
| OpenClaw | 2026.4.8 |

## 前置条件

- Windows 10/11
- Git Bash（随 Git for Windows 安装）
- winget 包管理器（Windows 11 自带，Windows 10 需手动安装）

## 安装步骤

### 1. 安装 Node.js

OpenClaw 需要 **Node 24（推荐）或 Node 22.16+** 运行时。

```bash
winget.exe install OpenJS.NodeJS --accept-package-agreements --accept-source-agreements
```

安装完成后，确认 Node.js 安装路径（本例中为 `D:\`），验证安装：

```bash
node --version   # 期望输出: v25.x.x
npm --version    # 期望输出: 11.x.x
```

### 2. 配置 PATH 环境变量

如果终端提示 `node: not found`，需要将 Node.js 所在路径添加到 PATH。

编辑 `~/.bashrc`，添加以下内容：

```bash
export PATH="/d:/c/Users/<你的用户名>/AppData/Roaming/npm:$PATH"
```

> **说明**：
> - `/d` 是 Node.js 的安装目录（Git Bash 中 `D:\` 对应 `/d`）
> - `AppData/Roaming/npm` 是 npm 全局包的安装目录（openclaw CLI 在这里）

使配置生效：

```bash
source ~/.bashrc
```

### 3. 全局安装 OpenClaw

```bash
npm install -g openclaw@latest
```

验证安装：

```bash
openclaw --version
# 期望输出: OpenClaw 2026.4.8 (或更新版本)
```

### 4. 运行引导式配置

```bash
openclaw onboard --install-daemon
```

交互式向导会引导你完成以下配置：

1. **选择 AI 模型提供商** — OpenAI / Anthropic / Google 等
2. **配置 API 密钥** — 输入你的模型 API Key
3. **设置消息渠道** — WhatsApp / Telegram / Discord / 微信 / 飞书等（可选）
4. **安装后台守护进程** — 让 Gateway 保持运行

### 5. 启动 Gateway

```bash
openclaw gateway --port 18789 --verbose
```

### 6. 与 AI 助手对话

```bash
openclaw agent --message "你好" --thinking high
```

## 常见问题

### `node: not found`

Node.js 未加入 PATH。解决方法：

```bash
# 查找 node.exe 的实际位置
powershell.exe -NoProfile -Command "Get-ChildItem -Path 'C:\','D:\' -Filter 'node.exe' -Depth 3 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName"

# 将找到的路径添加到 ~/.bashrc 中的 PATH
```

### npm 安装时 `sharp` 模块编译失败 (EPERM)

如果出现权限错误，确保 cmd.exe 子进程也能找到 `node`：

```bash
# 先将 Node.js 路径加入 Windows 用户环境变量
powershell.exe -NoProfile -Command "[Environment]::SetEnvironmentVariable('Path', 'D:\;' + [Environment]::GetEnvironmentVariable('Path', 'User'), 'User')"

# 清理失败的安装
rm -rf "$APPDATA/npm/node_modules/openclaw"

# 重新安装
npm install -g openclaw@latest
```

### 推荐使用 WSL2

OpenClaw 官方**强烈建议在 WSL2 中运行**。如果遇到 Windows 原生环境兼容性问题：

```bash
# 安装 WSL2
wsl --install

# 在 WSL2 中安装 Node.js 和 OpenClaw
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

## 架构概览

```
WhatsApp / Telegram / Slack / Discord / 微信 / 飞书 / WebChat ...
               │
               ▼
┌───────────────────────────────┐
│            Gateway            │
│         (控制平面)             │
│     ws://127.0.0.1:18789      │
└──────────────┬────────────────┘
               │
               ├─ Pi Agent (RPC)
               ├─ CLI (openclaw …)
               ├─ WebChat UI
               ├─ macOS App
               └─ iOS / Android Nodes
```

## 配置文件

配置文件路径：`~/.openclaw/openclaw.json`

最小配置示例：

```json
{
  "agent": {
    "model": "<provider>/<model-id>"
  }
}
```

消息渠道配置示例（Telegram）：

```json
{
  "channels": {
    "telegram": {
      "botToken": "你的Bot Token"
    }
  }
}
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `openclaw onboard` | 引导式安装配置 |
| `openclaw gateway` | 启动网关 |
| `openclaw doctor` | 诊断配置问题 |
| `openclaw update --channel stable` | 更新到稳定版 |
| `openclaw channels login` | 登录消息渠道 |
| `openclaw agent --message "..."` | 与 AI 助手对话 |
| `openclaw --version` | 查看版本 |

## 参考链接

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [官方文档](https://docs.openclaw.ai)
- [快速开始](https://docs.openclaw.ai/start/getting-started)
- [完整配置参考](https://docs.openclaw.ai/gateway/configuration)
- [安全指南](https://docs.openclaw.ai/gateway/security)
- [Docker 部署](https://docs.openclaw.ai/install/docker)
- [Windows (WSL2) 指南](https://docs.openclaw.ai/platforms/windows)
