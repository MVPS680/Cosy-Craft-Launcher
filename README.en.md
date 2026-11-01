# Plain Craft Launcher (PCL) · MY-PCL Restored

**A community-maintained Windows launcher for Minecraft: Java Edition, restoring game downloads and installation with version, mod and modpack management.**

Independently maintained from the public [PCL 2.99.0.0](https://github.com/Meloong-Git/PCL) source. This is an unofficial distribution, not affiliated with the PCL team, Mojang or Microsoft.

[![Release](https://img.shields.io/github/v/release/FLandreyu/MY-PCL?color=5865a8)](https://github.com/FLandreyu/MY-PCL/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/FLandreyu/MY-PCL/total?color=438870)](https://github.com/FLandreyu/MY-PCL/releases)
[![Windows](https://img.shields.io/badge/Platform-Windows-507aa0)](https://github.com/FLandreyu/MY-PCL/releases/latest)

[Download](https://github.com/FLandreyu/MY-PCL/releases/latest) · [Report an issue](https://github.com/FLandreyu/MY-PCL/issues/new/choose) · [Build instructions](docs/BUILD.md) · [中文](README.md)

## Get started

1. Download **`MY-PCL-…-win.zip`** from the latest Release's Assets. The automatically generated `Source code` archives are not runnable builds.
2. Extract the entire ZIP into a separate, writable folder. Run **`Plain Craft Launcher 2.exe`**, keeping its `.exe.config` alongside it.
3. Open **下载 (Download)**, select a game version and compatible loaders, or import a supported modpack.
4. Select the installed version and configure Java and your account before launching. See the Microsoft login requirements below.

Requires a Windows desktop environment, .NET Framework 4.8, and Java suitable for your selected Minecraft version. Available components depend on game version and upstream services.

The executable is unsigned. Verify the download source and published SHA-256 before running it; do not run replacement files from unknown sources.

## Features and requirements

| Use case | Capability | Notes |
| --- | --- | --- |
| Game installation | Releases, snapshots and historical versions | Restored download entries; requires available download sources |
| Mod loaders | Forge, NeoForge, Fabric and other supported components | Options depend on game version and compatibility |
| Modpacks | Supported `.zip` and `.mrpack` imports, including drag and drop | Not every ZIP is a modpack; individual downloads may have restrictions |
| Instance management | Directories, Java, memory and launch arguments | Instance isolation is recommended for separate modpacks |
| Resource discovery | Modrinth and CurseForge entries | Modrinth needs no user-provided key; CurseForge requires an API key |
| Accounts | Microsoft, third-party authentication and offline-mode entries | Offline mode does not provide an authenticated Minecraft session |
| Updates | Manual downloads from Releases | No built-in automatic update service |

This describes project capabilities, not a guarantee that every version, modpack and network combination has been tested. Read each release's limitations and build information.

## Updating and existing installations

Exit the launcher and back up important saves and configuration before updating. Extract the new build into a separate folder and check it before moving configuration.

Game files live in your chosen game directory. Launcher data also uses the local `PCL` folder and, for some settings and account caches, `HKCU\Software\PCLDebug`. Other launchers can use an existing game directory, but account caches are not interchangeable. Avoid simultaneous installation or modification of the same instance by multiple launchers.

## Microsoft login

**Public builds currently do not include an approved Microsoft OAuth Client ID ready for general use.** Submitting an application is not approval; this release does not change that requirement.

If you maintain an application with the necessary Minecraft service access approval, set its ID before starting the launcher:

```powershell
$env:PCL_MS_CLIENT_ID = "your-application-client-id"
& ".\Plain Craft Launcher 2.exe"
```

This affects the current PowerShell session and processes it starts. A Client ID identifies an application; it is not a client secret. Public desktop clients must not embed a client secret. Do not borrow another launcher's ID or share account tokens.

- Missing `client_id`: check that the environment variable reaches the launcher process.
- `Invalid app registration`: check application registration and Minecraft service access approval.
- Other HTTP 403 errors, timeouts or connection failures require the actual endpoint and error text; a status code alone does not identify the cause.

You may continue launching existing games with a launcher whose account login works, while using this project for installation and management. A valid Minecraft license must be obtained separately.

## Resource services

Modrinth search needs no user-provided API key. To use CurseForge services, obtain suitable API access from the provider and set:

```powershell
$env:PCL_CURSEFORGE_API_KEY = "your-api-key"
& ".\Plain Craft Launcher 2.exe"
```

No CurseForge API key is bundled. Follow the provider's applicable terms and never publish keys in source, screenshots or issues. Modpack installation also depends on author permissions, file availability and service status.

## Troubleshooting

- **Empty lists or stalled downloads:** record the game version, loader, source, failed file and complete error. Check service availability and, where applicable, API access.
- **Downloaded but cannot launch:** check Java, memory, mod compatibility and account status. Download completion does not prove launch readiness.
- **Version still says 2.99.0.0:** that is the upstream base. Release suffixes such as `r2` identify this repository's maintenance revisions. `BUILD.json` in the ZIP records the source commit and configuration.
- **Verify a ZIP:** download its `.sha256` from the same Release and compare it with `Get-FileHash .\MY-PCL-2.99.0.0-r2-win.zip -Algorithm SHA256`. A checksum detects differences; it does not replace a signature or trusted source.

## Feedback and development

Use [this repository's issue tracker](https://github.com/FLandreyu/MY-PCL/issues/new/choose), including the release, Windows/Java versions, steps to reproduce and actual error. Redact tokens, passwords, API keys and personal information from logs. Do not upload account caches or registry exports.

See [docs/BUILD.md](docs/BUILD.md) for dependencies, compilation and release packaging.

## Credits and license

Thanks to LTCat (龙腾猫跃), [PCL](https://github.com/Meloong-Git/PCL), [MeloongCore](https://github.com/Meloong-Git/MeloongCore) and their contributors. The original [LICENCE](LICENCE) is retained; consult it for usage and distribution conditions.

This independent derivative is not an official PCL or Minecraft product. Minecraft and third-party content belong to their respective rights holders.

[Privacy policy](PRIVACY.md) · [Terms](TERMS.md) · [Upstream repository](https://github.com/Meloong-Git/PCL) · [PCL help](https://github.com/LTCatt/PCL2Help)
