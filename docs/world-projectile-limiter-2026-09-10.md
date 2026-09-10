# World Projectile Limiter — SE SKSE 성능 선행 1호

날짜: 2026-09-10  
런타임: Skyrim SE 1.7.104.0 / SKSE 2.3.1 / Address Library format 5  
CommonLib: local alandtse CommonLibSSE-NG v7.4.0

## 왜

OpenSkyrim식 엔진 재구현보다, SE에서 SKSE로 성능을 먼저 깎는다.  
1호는 월드에 쌓인 화살·볼트·미사일 투사체 상한.

## Arrow Limiter SSE 와 구분

| 모드 | 대상 |
|---|---|
| Arrow Limiter SSE (`LFGAmmoLimiter.esp`) | 인벤 탄약 **소지 개수** |
| World Projectile Limiter (이 DLL) | 월드에 떠 있는/박힌 **투사체 객체** |

## 소스

`D:\MO2-Skyrim\_unpack\build\WorldProjectileLimiter`

- 템플릿: `epinter/skse-clibng-template`
- `extern\CommonLibSSE-NG` → 로컬 CommonLib junction
- 핵심: `Projectile::Manager` limited+unlimited 순회 후 `Kill()`

## 빌드

```bat
python -X utf8 D:\MO2-Skyrim\_tools\latest-build\latest_build.py skse --src D:\MO2-Skyrim\_unpack\build\WorldProjectileLimiter --apply
```

산출물: `C:\Users\icand\OneDrive\Desktop\스카이림_빌드산출물\skse\WorldProjectileLimiter\`  
`mods\` 자동 복사 없음. Plan 배치는 별도 확인 후.

## INI

`Data\SKSE\Plugins\WorldProjectileLimiter.ini`

- `iMaxProjectiles=200`
- `bArrowsOnly=true`
- `bPreservePlayer=true`
- `iIntervalMs=1000`

## 상태

- [x] 스켈레톤 init + 로컬 CommonLib 연결
- [x] enforce 경로 구현
- [x] Release DLL 빌드 성공 (2026-09-10)
- [ ] Plan 배치
- [ ] 인게임 `skse64.log` 로드 확인

## 빌드 산출물 (디스크)

`C:\Users\icand\OneDrive\Desktop\스카이림_빌드산출물\skse\WorldProjectileLimiter\`

- `WorldProjectileLimiter.dll`
- `WorldProjectileLimiter.pdb`
- `WorldProjectileLimiter.ini`
- `spdlog.dll`, `fmt.dll` (현재 vcpkg 동적 링크 — Plugins 폴더에 같이)

소스 미러: `D:\game\skse-plugins\WorldProjectileLimiter`  
작업 트리: `D:\MO2-Skyrim\_unpack\build\WorldProjectileLimiter`
