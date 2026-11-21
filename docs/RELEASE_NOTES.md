## Cosy Craft Launcher 2.99.0.0-r2

由 **MVPClub**（[mvpclub.cc](https://mvpclub.cc)）维护的第三方 Minecraft 启动器，基于 PCL 2.99.0.0 的公开源码构建，提供游戏下载、版本、模组加载器和整合包管理功能。不是 PCL 官方发行版。

### 本次维护

- 统一项目名称为 **Cosy Craft Launcher**，作者信息为 **MVPClub（mvpclub.cc）**。
- 更新界面标题、关于页、版权信息、包元数据、README 与文档链接。
- 汇总当前维护分支的使用细节与可靠性改进，使用 **Release** 配置构建。
- 发行包包含运行配置、原许可文件、构建信息与使用说明，并提供 SHA-256 校验文件。
- 保留历史 Release，方便对照版本与回退。

### 下载与安装

1. 下载 **`Cosy-Craft-Launcher-2.99.0.0-r2-win.zip`**，不要把 `Source code` 当作启动器安装包。
2. 退出旧版并备份存档；将 ZIP 完整解压到独立目录。
3. 运行 `Cosy Craft Launcher.exe`，保留同目录的 `.exe.config`。
4. 在「下载」中安装游戏版本或导入整合包，按需配置 Java 与账号。

运行环境：Windows 桌面、.NET Framework 4.8，以及适用于所选游戏版本的 Java。程序未进行代码签名，请核对下载来源和校验文件。

### 已知限制

- **微软登录尚非开箱即用**：本包未内置已获批准的应用 ID；需要自行配置具备所需访问批准的 `COSY_MS_CLIENT_ID`（兼容旧变量 `PCL_MS_CLIENT_ID`）。提交申请不等于审核通过。
- Modrinth 资源搜索无需用户提供 Key；CurseForge 相关功能需配置 `COSY_CURSEFORGE_API_KEY`（兼容旧变量 `PCL_CURSEFORGE_API_KEY`），并受服务与资源访问条件影响。
- 无内置自动更新，请从 Releases 获取新版本。
- 已完成 Release 编译和自动化检查；本次没有完成微软账号登录、真实游戏下载到游戏启动的完整端到端验证。不保证每个整合包或网络环境都可用。

### 校验与反馈

下载同页的 `.sha256`，与以下命令的结果比较：

```powershell
Get-FileHash ".\Cosy-Craft-Launcher-2.99.0.0-r2-win.zip" -Algorithm SHA256
```

包内 `BUILD.json` 记录源码提交、构建配置和可执行文件校验值。

[使用说明](https://github.com/MVPS680/Cosy-Craft-Launcher#readme) · [问题反馈](https://github.com/MVPS680/Cosy-Craft-Launcher/issues/new/choose) · [隐私政策](https://github.com/MVPS680/Cosy-Craft-Launcher/blob/main/PRIVACY.md) · [使用条款](https://github.com/MVPS680/Cosy-Craft-Launcher/blob/main/TERMS.md) · [上游与许可](https://github.com/MVPS680/Cosy-Craft-Launcher/blob/main/LICENCE)
