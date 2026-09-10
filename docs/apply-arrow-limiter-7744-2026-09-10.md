# Apply: Arrow Limiter SSE (Nexus 7744)

Date: 2026-09-10  
Profile: Plan only (`D:\MO2-Skyrim\profiles\Plan`)

## What

[Arrow Limiter SSE](https://www.nexusmods.com/skyrimspecialedition/mods/7744) v1.11 by Lofgren — limits total arrows/bolts carried (default 24/36), SkyUI MCM.

## Done on disk

| Item | Value |
|---|---|
| Archive | `D:\MO2-Skyrim\downloads\7744-96351.zip` (file id 96351) |
| Body folder | `mods\Arrow Limiter SSE` (`LFGAmmoLimiter.esp` + `.bsa`) |
| KR overlay | `mods\SST KR - Arrow Limiter SSE` (ESP strings, unmatched 0) |
| Left | `+SST KR - Arrow Limiter SSE` above `+Arrow Limiter SSE` (below Show Follower Carry Weight) |
| Right | `*LFGAmmoLimiter.esp` after `SkyUI_SE.esp` |
| loadorder.txt | `LFGAmmoLimiter.esp` after `SkyUI_SE.esp` |
| Runtime gate | arrange_ok (no SKSE DLL) |
| Requirements | SkyUI +, SKSE on game |
| 정본 | 빌드 0.46.0 추가 기록 (이후 0.46.1은 진단용 3모드 `-`, Arrow와 무관) |

## Not done

- In-game load / MCM click not verified (game not run this session)
- Gemini auto-fill was unavailable; KR strings filled via SST user glossary

## Usage

SkyUI MCM → Ammo Limiter (표시: 탄약 제한). Adjust arrow/bolt caps or pick Immersive / Hunting Quiver / War Quiver presets.
