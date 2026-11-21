# Cosy Craft Launcher

**面向 Windows 的 Minecraft: Java Edition 第三方启动器，基于 PCL 2.99.0.0 公开源码独立维护，提供游戏下载、版本 / 模组 / 整合包管理与启动功能。**

- **项目名称：** Cosy Craft Launcher
- **作者 / 维护者：** MVPClub（[mvpclub.cc](https://mvpclub.cc)）
- **项目仓库：** [MVPS680/Cosy-Craft-Launcher](https://github.com/MVPS680/Cosy-Craft-Launcher)
- **上游基础：** [PCL 2.99.0.0](https://github.com/Meloong-Git/PCL)

本项目是非官方第三方发行版，与 PCL 官方团队、Mojang 和 Microsoft 均无隶属关系。

[![最新正式版](https://img.shields.io/github/v/release/MVPS680/Cosy-Craft-Launcher?label=Release&color=5865a8)](https://github.com/MVPS680/Cosy-Craft-Launcher/releases/latest)
[![累计下载](https://img.shields.io/github/downloads/MVPS680/Cosy-Craft-Launcher/total?label=Downloads&color=438870)](https://github.com/MVPS680/Cosy-Craft-Launcher/releases)
[![平台](https://img.shields.io/badge/Platform-Windows-507aa0)](https://github.com/MVPS680/Cosy-Craft-Launcher/releases/latest)

[下载正式版](https://github.com/MVPS680/Cosy-Craft-Launcher/releases/latest) · [报告问题](https://github.com/MVPS680/Cosy-Craft-Launcher/issues/new/choose) · [构建说明](docs/BUILD.md) · [English](README.en.md)

## 快速开始

1. 打开 [最新 Release](https://github.com/MVPS680/Cosy-Craft-Launcher/releases/latest)，下载 Assets 中的 **`Cosy-Craft-Launcher-…-win.zip`**。`Source code` 是源码，不是可运行的启动器。
2. 将压缩包完整解压到有写入权限的独立目录，运行 **`Cosy Craft Launcher.exe`**，并保留同目录下的 `.exe.config` 文件。
3. 在「下载」中选择 Minecraft 版本，按需选择兼容的模组加载器；也可以导入支持的整合包。
4. 安装完成后选择版本、配置账号和 Java，再启动游戏。微软登录的前置条件见下文。

**运行环境：** Windows 桌面环境、.NET Framework 4.8，以及与所选游戏版本相匹配的 Java。可用组件与资源以实际列表为准。

> 发行包未进行代码签名。遇到系统提示时，请先核对下载来源及 Release 提供的 SHA-256；不要运行来源不明的替换文件。

## 功能概览

| 使用场景 | 提供的能力 | 说明 |
| --- | --- | --- |
| 安装游戏 | Minecraft 正式版、快照及历史版本下载 | 依赖下载源可用性 |
| 配置模组环境 | Forge、NeoForge、Fabric 等组件安装 | 可选组件由游戏版本与兼容性决定 |
| 使用整合包 | 支持的 `.zip`、`.mrpack` 整合包导入与安装 | 可将整合包拖入启动器；普通 ZIP 不一定是整合包 |
| 管理版本 | 版本目录、Java、内存与启动参数配置 | 建议为不同整合包启用版本隔离 |
| 查找资源 | Modrinth、CurseForge 资源入口 | Modrinth 无需自备 Key；CurseForge 需要配置 API Key |
| 账号登录 | 微软账号、第三方认证与离线模式入口 | 离线模式不提供正版会话，不能替代正版授权 |
| 维护更新 | 从 GitHub Releases 手动更新 | 当前没有内置自动更新服务 |

功能列表说明项目能力，不代表所有游戏版本、整合包与网络环境都已逐一验证。具体构建信息和已知限制以对应 Release 为准。

## 更新、存档与共存

- **更新前先退出启动器，备份重要存档和配置。** 将新版解压到独立目录确认可运行后，再迁移需要的配置。
- 游戏文件保存在你选择的游戏目录；启动器目录内也有 `PCL` 配置与日志文件夹，部分数据使用 `HKCU\Software\PCLDebug`。这些是兼容既有配置保留的内部路径。
- 可以与其他启动器分别安装，并按需选择已有游戏目录。不同启动器的账号缓存不通用，不能据此共享正版登录状态。
- 不要让多个启动器并行安装或修改同一游戏版本，以免发生文件冲突。

## 微软账号登录

**当前公开构建未内置可直接使用的、已获批准的 Microsoft OAuth Client ID。** 提交应用申请不等于获得批准；本次发布不改变这一限制。

如果你维护自己的应用，需要使用获得所需 Minecraft 服务访问批准的应用 ID，并在启动程序前设置：

```powershell
$env:COSY_MS_CLIENT_ID = "你的应用程序客户端 ID"
& ".\Cosy Craft Launcher.exe"
```

旧版环境变量 `PCL_MS_CLIENT_ID` 仍可作为兼容回退使用。设置只影响当前 PowerShell 及它启动的程序。Client ID 是应用标识，**不是客户端密码**；桌面公共客户端不应内置 client secret。不要使用其他启动器的应用 ID，也不要分享登录令牌。

- `client_id` 缺失：检查环境变量是否传给了启动器进程。
- `Invalid app registration`：检查应用注册和 Minecraft 服务访问批准状态。
- 其他 `403`、超时或连接失败：保留具体接口及错误文本后排查；不能仅凭状态码断定是账号、应用或网络问题。

如果当前配置无法完成微软登录，可继续使用能够正常登录的启动器启动已有游戏；本项目可以独立用于版本下载与管理。Minecraft 授权需由用户自行合法取得。

## Modrinth 与 CurseForge

Modrinth 资源搜索无需额外配置 API Key。CurseForge 相关服务需自行取得适用的 API 访问凭据，再在启动前设置：

```powershell
$env:COSY_CURSEFORGE_API_KEY = "你的 API Key"
& ".\Cosy Craft Launcher.exe"
```

旧版环境变量 `PCL_CURSEFORGE_API_KEY` 仍可作为兼容回退使用。本仓库与发行包不附带 CurseForge API Key。使用条件以服务提供方的要求为准；不要把 Key 写入公开源码、日志截图或 Issue。某些整合包还受作者下载权限、文件可用性和第三方服务状态影响。

## 常见问题

<details>
<summary><strong>下载失败、列表为空或安装卡住怎么办？</strong></summary>

记录游戏版本、加载器、下载源、失败文件和完整错误文本。先确认对应服务可以访问，再尝试重新加载或切换可用下载源。CurseForge 请求失败还需要检查 API Key 和内容访问权限；单个 HTTP 状态码不足以确定原因。

</details>

<details>
<summary><strong>已经下载了游戏，为什么仍然无法启动？</strong></summary>

下载完成与启动成功是两个阶段。请检查 Java 版本、内存设置、模组兼容性和账号状态。第三方认证服务器的可用性由其运营方负责；离线模式不能用于需要正版会话的服务器。

</details>

<details>
<summary><strong>为什么程序中仍显示 2.99.0.0？</strong></summary>

2.99.0.0 是本项目采用的上游基础版本。Release 名称中的 `r2` 等后缀区分本仓库的维护批次，不代表上游的新版本。压缩包中的 `BUILD.json` 记录对应源码提交和构建配置。

</details>

<details>
<summary><strong>怎样核对下载文件？</strong></summary>

从同一 Release 下载 ZIP 与 `.sha256` 文件，在 PowerShell 中执行：

```powershell
Get-FileHash ".\Cosy-Craft-Launcher-2.99.0.0-r2-win.zip" -Algorithm SHA256
```

将输出与校验文件比较。校验值用于发现文件损坏或不一致，不代替代码签名或可信下载来源。

</details>

## 反馈与贡献

请在[本仓库 Issues](https://github.com/MVPS680/Cosy-Craft-Launcher/issues/new/choose)反馈问题，附上：Release 版本、Windows 与 Java 版本、复现步骤、预期结果和实际错误。

日志中可能包含用户名、本地路径、服务器地址或凭据。提交前请隐藏令牌、密码、API Key 等敏感内容。不要上传整个账号缓存或注册表导出文件。

源码构建、依赖与发布方式见 [构建说明](docs/BUILD.md)。欢迎提交可复现的问题与范围明确的改进。

## 来源与许可

Cosy Craft Launcher 由 **MVPClub**（[mvpclub.cc](https://mvpclub.cc)）维护。感谢龙腾猫跃（LTCat）及 [PCL](https://github.com/Meloong-Git/PCL)、[MeloongCore](https://github.com/Meloong-Git/MeloongCore) 的贡献者。本项目保留上游 [LICENCE](LICENCE)，具体使用与分发条件请阅读原文。

本项目为第三方独立修改版，不是 PCL、Minecraft、Mojang 或 Microsoft 的官方产品。Minecraft 及第三方资源的权利归各自权利人所有。

[隐私政策](PRIVACY.md) · [使用条款](TERMS.md) · [上游 PCL 仓库](https://github.com/Meloong-Git/PCL)
