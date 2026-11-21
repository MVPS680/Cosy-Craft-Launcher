# AGENTS.MD

## 项目名称与作者

- **项目名称：** Cosy Craft Launcher
- **作者 / 维护者：** MVPClub（[https://mvpclub.cc](https://mvpclub.cc)）
- **项目仓库：** [https://github.com/MVPS680/Cosy-Craft-Launcher](https://github.com/MVPS680/Cosy-Craft-Launcher)
- **上游基础：** PCL 2.99.0.0（[Meloong-Git/PCL](https://github.com/Meloong-Git/PCL)）

Cosy Craft Launcher 是面向 Windows 的 Minecraft: Java Edition 第三方启动器，基于 PCL 2.99.0.0 公开源码独立维护，提供游戏版本下载、模组加载器安装、整合包导入、账号登录、Java / 内存配置与启动等功能。非 PCL 官方、Mojang 或 Microsoft 产品。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 主程序 | VB.NET + WPF，.NET Framework 4.8 |
| 核心辅助库 | C# / .NET Framework 4.8（`PCLCS`），使用 C# 13 与 PolySharp |
| 公共基础库 | MeloongCore / MeloongCore.Wpf（Git 子模块，C#） |
| 构建 | MSBuild（Visual Studio 2022 / Build Tools），NuGet 还原 |
| 发布脚本 | Python 3（标准库），PowerShell 5.1 验证脚本 |
| CI | GitHub Actions（Windows runner） |

内部代码仍使用 `PCL` 命名空间、`PCL` 数据文件夹、`PCLDebug` 注册表键、`PCLCS` / `MeloongCore` 程序集名等上游技术标识，这些是为保持代码与既有配置兼容而保留的内部标识，不是面向用户的品牌名称。

## 目录结构

```text
.
├─ Cosy Craft Launcher/          # 主 WPF 启动器（VB.NET）
│  ├─ Application.xaml(.vb)      # 应用入口：核心初始化、单实例、文件结构、环境检查
│  ├─ FormMain.xaml(.vb)         # 主窗口：标题栏、页面导航、更新日志、全局交互
│  ├─ Controls/                  # 自定义 WPF 控件（按钮、卡片、提示、弹窗、滚动条等）
│  ├─ Modules/
│  │  ├─ ModMain.vb              # 提示、弹窗、帮助库、自定义事件、通用 UI 逻辑
│  │  ├─ ModSecret.vb            # 分支标记、OAuth / CurseForge 配置、主题色板
│  │  ├─ ModEvent.vb             # 自定义事件处理
│  │  ├─ ModMusic.vb             # 背景音乐
│  │  ├─ Base/                   # 路径、日志、网络、文件、进程、动画等基础模块
│  │  ├─ Minecraft/              # 版本安装、启动、Java、Mod、整合包、崩溃分析、窗口监听
│  │  └─ Resource/               # 资源搜索与本地资源加载
│  ├─ Pages/
│  │  ├─ PageLaunch/             # 启动页、账号登录、皮肤
│  │  ├─ PageDownload/           # 下载安装、资源搜索
│  │  ├─ PageInstance/           # 版本设置、Mod / 整合包导出
│  │  ├─ PageSetup/              # 启动器设置、个性化、联机设置
│  │  ├─ PageLink/               # EasyTier 联机
│  │  ├─ PageSelect/             # 游戏文件夹选择
│  │  ├─ PageOther/              # 帮助、关于、测试页
│  │  └─ PageSpeed/              # 下载任务速度页
│  ├─ My Project/                # 程序集信息、资源、设置、应用清单
│  ├─ Images/                    # 图标、方块图、头像等资源
│  ├─ Resources/                 # 字体、帮助包、第三方 DLL / JAR、Custom.xaml
│  └─ Cosy Craft Launcher.vbproj # 主项目文件
├─ PCLCS/                        # C# 辅助库：启动参数、MC 版本 / 安装清单、资源
├─ MeloongCore/                  # Git 子模块：公共基础库
├─ scripts/                      # 打包、发布、上游同步、UI / 主题验证脚本与 Python 测试
├─ docs/                         # 构建说明、发行说明、预览图、许可申请草稿
├─ patches/                      # 上游历史补丁（归档）
├─ .github/workflows/            # Build / Release / Fix Build 工作流
├─ release.json                  # 维护版本、标签与 Release 名称
├─ README.md / README.en.md      # 中文 / 英文说明
├─ PRIVACY.md / TERMS.md         # 隐私政策 / 使用条款
├─ LICENCE                       # 上游《PCL 分发有限许可》（保留）
└─ AGENTS.MD                     # 本文件
```

## 构建与运行

### 环境准备

- Windows 10 / 11
- Visual Studio 2022 或 Build Tools（.NET 桌面开发组件，含 MSBuild）
- .NET Framework 4.8 Developer Pack / Targeting Pack
- .NET SDK 9（用于 `PCLCS` 中的 C# 13 代码）
- Python 3（仅发布与测试脚本需要）
- Git（含子模块）

```powershell
git clone --recurse-submodules https://github.com/MVPS680/Cosy-Craft-Launcher.git
cd Cosy-Craft-Launcher
git submodule update --init --recursive
dotnet restore PCLCS/PCLCS.csproj
msbuild "Cosy Craft Launcher/Cosy Craft Launcher.vbproj" -p:Configuration=Release
```

构建产物：

```text
Cosy Craft Launcher/bin/Cosy Craft Launcher.exe
Cosy Craft Launcher/bin/Cosy Craft Launcher.exe.config
```

直接运行 `Cosy Craft Launcher.exe` 即可。首次运行会在程序目录创建 `PCL` 配置文件夹，并在 `HKCU\Software\PCLDebug` 保存部分设置与账号缓存（兼容上游的既有路径）。

### 常见构建问题

- **找不到 .NET Framework 4.8 引用程序集**：安装 .NET Framework 4.8 Developer Pack；或使用 NuGet 包 `Microsoft.NETFramework.ReferenceAssemblies.net48`，把 `TargetFrameworkRootPath` 指向该包解压后的 `build` 目录。
- **无法解析 `Microsoft.NET.Sdk`**：设置 `MSBuildSDKsPath` 指向已安装 .NET SDK 的 `Sdks` 目录，并设置 `MSBuildEnableWorkloadResolver=false`。
- **`BasicDesignGuidelineRules.ruleset` 警告**：属于既有代码分析规则集缺失警告，不影响生成；与编译错误应分别处理。

### 测试与验证

```powershell
python -m unittest discover -s scripts -p "test_*.py"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_ui.ps1 -Exe "Cosy Craft Launcher/bin/Cosy Craft Launcher.exe"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_scarlet_theme.ps1 -Exe "Cosy Craft Launcher/bin/Cosy Craft Launcher.exe"
```

### 本地打包

先提交已跟踪的源码改动，再执行：

```powershell
python scripts/package_release.py --build-dir "Cosy Craft Launcher/bin" --output-dir dist
python scripts/release_asset.py --zip "dist/Cosy-Craft-Launcher-2.99.0.0-r2-win.zip" --dry-run
```

`package_release.py` 会读取 `release.json`，生成 `Cosy-Craft-Launcher-<版本>-win.zip`、SHA-256 与 `BUILD.json`。

## 关键模块说明

### 启动流程

1. `Application.xaml.vb` 的 `Application_Startup` 调用 `MeloongCore.Main.Init("PCL")` 初始化公共库与数据目录。
2. 通过命名互斥量保证单实例；检查 .NET Framework、解压目录、32 位系统等运行环境。
3. 创建程序目录、缓存与日志目录，加载 `FormMain`。
4. `FormMain` 初始化首页、加载池、账号与下载服务，并处理版本升级 / 降级迁移。

### 核心模块

- **`Application.xaml.vb`**：入口、单实例、环境检查、命令行参数（`--update` / `--gpu` / `--memory`）。
- **`FormMain.xaml.vb`**：主窗口与页面切换、更新日志、错误报告、全局快捷键 / 拖拽。
- **`Modules/ModMain.vb`**：提示与弹窗系统、帮助库加载、自定义事件、通用 UI 辅助。
- **`Modules/ModSecret.vb`**：分支标记、`COSY_MS_CLIENT_ID` / `COSY_CURSEFORGE_API_KEY`（兼容 `PCL_*` 旧变量）、主题色板与主题刷新。
- **`Modules/Base/ModBase.vb`**：全局路径（`Paths.Base`、`PathTemp`、`PathImage`）、版本信息、文件 / 进程 / 权限工具。
- **`Modules/Base/ModNet.vb`**：下载引擎、镜像源、断点续传与多线程下载。
- **`Modules/Minecraft/ModMinecraft.vb`**：版本扫描、实例配置（`PCL\Setup.ini`、`PCL.ini`）、图标与缓存。
- **`Modules/Minecraft/ModLaunch.vb`**：启动参数构建、Java 选择、账号会话、离线皮肤、内存优化。
- **`Modules/Minecraft/ModModpack.vb`**：整合包识别、安装、导出与覆盖文件处理。
- **`Modules/Minecraft/ModCrash.vb`**：崩溃日志解析与原因分析。
- **`Pages/PageOther/PageOtherAbout.xaml`**：关于页、作者 / 特别鸣谢 / 支持与反馈 / 法律信息 / 第三方许可。
- **`PCLCS/`**：C# 侧启动与版本辅助逻辑；通过项目引用和嵌入资源供主程序使用。

### 配置与元数据

- 程序集名称：`Cosy Craft Launcher`
- 程序集作者 / 公司：`MVPClub`
- 版权：`Copyright © 2026 MVPClub (https://mvpclub.cc)`
- 官网：`https://mvpclub.cc`
- 仓库：`https://github.com/MVPS680/Cosy-Craft-Launcher`
- 维护版本：`release.json` 中的 `2.99.0.0-r2`
- 微软登录环境变量：`COSY_MS_CLIENT_ID`（兼容 `PCL_MS_CLIENT_ID`）
- CurseForge 环境变量：`COSY_CURSEFORGE_API_KEY`（兼容 `PCL_CURSEFORGE_API_KEY`）

## 品牌与上游许可

面向用户的标题、关于页、版权信息、README / 文档、程序集元数据、发行包与 CI 元数据均使用 **Cosy Craft Launcher / MVPClub（mvpclub.cc）**。

`LICENCE` 是上游《PCL 分发有限许可》，必须保留；README、关于页与文档中的 PCL / 龙腾猫跃 / MeloongCore 字样仅用于合法的上游署名与许可说明，不属于本项目品牌残留。请勿删除这些署名或替换 `LICENCE`。

> 注意：上游许可对重度使用有名称前缀与署名要求。本仓库按项目要求使用 Cosy Craft Launcher 品牌；对外发布前请自行确认名称与分发方式符合《PCL 分发有限许可》，必要时与上游作者沟通授权。
