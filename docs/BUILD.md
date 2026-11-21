# 构建与发布

> 项目：Cosy Craft Launcher · 作者：MVPClub（https://mvpclub.cc）

## 环境

- Windows、Git、Visual Studio 2022 / Build Tools 的 .NET 桌面开发组件。
- .NET Framework 4.8 Developer Pack；.NET SDK 9 用于项目中的 C# 13 代码。
- Python 3，用于发行包检查与打包脚本。

在 Developer PowerShell 中执行：

```powershell
git clone --recurse-submodules https://github.com/MVPS680/Cosy-Craft-Launcher.git
cd Cosy-Craft-Launcher
git submodule update --init --recursive
dotnet restore PCLCS/PCLCS.csproj
msbuild "Cosy Craft Launcher/Cosy Craft Launcher.vbproj" -p:Configuration=Release
```

可执行文件位于 `Cosy Craft Launcher/bin/Cosy Craft Launcher.exe`。`Release` 与 `Debug` 是不同构建配置，正式发行应使用前者。

如果 MSBuild 无法解析 SDK，请将 `MSBuildSDKsPath` 指向已安装 .NET SDK 的 `Sdks` 目录，并设置 `MSBuildEnableWorkloadResolver=false` 后重试。若本机未安装 .NET Framework 4.8 Targeting Pack，可通过 `Microsoft.NETFramework.ReferenceAssemblies.net48` NuGet 包提供引用程序集，并把 `TargetFrameworkRootPath` 指向该包的 `build` 目录。已有 `BasicDesignGuidelineRules.ruleset` 缺失警告与编译错误应分别处理。

## 本地打包

先确保源码已提交，再运行：

```powershell
python scripts/package_release.py --build-dir "Cosy Craft Launcher/bin" --output-dir dist
python scripts/release_asset.py --zip "dist/Cosy-Craft-Launcher-2.99.0.0-r2-win.zip" --dry-run
```

`package_release.py` 从 `release.json` 读取维护版本，生成 ZIP、SHA-256 和构建信息。普通打包不会访问 GitHub，也不会读取 GitHub 凭据。

## 正式发布流程

`.github/workflows/release.yml` 在 `main` 分支的 `release.json` 更新时运行，也可手动触发：

1. 检出对应提交及子模块，恢复依赖并编译 Release。
2. 执行自动化检查，再生成发行包与校验文件。
3. 创建草稿 Release，上传附件并回下载校验。
4. 校验成功后发布为正式版并设为 Latest。

发布脚本只接受明确的 `--execute`，使用 Actions 提供的 `GITHUB_TOKEN`。它不会覆盖已发布的同名版本，也不会移动已有标签到其他提交。相同版本重跑时，已存在的文件必须通过内容校验。

旧版 `fix-build.yml` 仍服务于 `v*-fix` 标签；新的维护版本使用 `v<基础版本>-r<批次>`，不要重复使用旧标签发布不同源码。

## 凭据与验证范围

运行时可通过 `COSY_MS_CLIENT_ID` 和 `COSY_CURSEFORGE_API_KEY` 提供自己的服务配置；旧变量名 `PCL_MS_CLIENT_ID`、`PCL_CURSEFORGE_API_KEY` 仍可作为兼容回退。发行脚本不把这些值写入源码或压缩包。不要将 token、client secret 或 API Key 提交到 Git。

自动化检查不等于完整的账号、下载与游戏运行测试。发布说明应区分已验证行为和仍需实际环境验证的流程。
