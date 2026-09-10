# World Projectile Limiter

SKSE performance plugin for Skyrim SE **1.7.104** / SKSE **2.3.1**.

Caps live world projectiles via `RE::Projectile::Manager` (`limited` + `unlimited`).  
Separate from **Arrow Limiter SSE** (inventory ammo count).

## Build

```bat
python -X utf8 D:\MO2-Skyrim\_tools\latest-build\latest_build.py skse --src D:\MO2-Skyrim\_unpack\build\WorldProjectileLimiter --apply
```

- CommonLib: junction `extern\CommonLibSSE-NG` → local `alandtse` v7.4.0
- DLL out: `C:\Users\icand\OneDrive\Desktop\스카이림_빌드산출물\skse\WorldProjectileLimiter\`
- Does **not** auto-copy into `mods\`

## Config

`Data\SKSE\Plugins\WorldProjectileLimiter.ini`

| Key | Default | Meaning |
|---|---|---|
| bEnabled | true | Master switch |
| bArrowsOnly | true | Ammo/missile only |
| bPreservePlayer | true | Cull NPC/world first |
| iMaxProjectiles | 200 | Soft cap |
| iIntervalMs | 1000 | Poll interval |
| bLogCulls | false | Log cull counts |

## Status

Skeleton + enforce path implemented. In-game load not verified yet (`skse64.log`).
