# 애니메이션을 60fps로 다시 만들기 — AI 인비트위닝 & MCP 자동화

> [폴아웃 4 애니메이션 → UE5 문서](./fallout4-animation-to-ue5.md)의 후속.
> 베데스다 원본은 **30fps**입니다. 이걸 60fps로 올리는 방법을 정리합니다. 2026-09 기준.

## 0. 먼저 — 이건 서로 다른 두 가지 문제입니다

| | 하는 일 | AI 필요? | 실제 효과 |
|---|---|---|---|
| **(a) 리샘플링** | 같은 곡선을 2배 촘촘히 다시 샘플링. 키 개수만 60/초 | ❌ | **거의 없음** (아래 설명) |
| **(b) 인비트위닝** | 원본에 **없던 중간 포즈를 새로 생성** | ✅ | **실제로 부드러워짐** |

대부분 "60fps로 만들고 싶다"고 할 때 기대하는 건 (b)인데, 실제로 하는 건 (a)라서 "바꿨는데 똑같다"가 됩니다.

### 왜 (a)는 효과가 거의 없나

UE5의 `AnimSequence`는 **시간 기준으로 샘플링되고 키 사이는 엔진이 보간**합니다.
30fps 애니메이션을 144Hz 모니터에서 돌려도 매 프레임 보간된 포즈가 나옵니다 — 뚝뚝 끊기지 않습니다.

그러니 30fps 데이터를 **선형 보간으로** 60fps로 다시 구우면, 엔진이 런타임에 하던 계산을
미리 해서 디스크에 저장한 것뿐입니다. 정보량은 1비트도 늘지 않고 애셋 용량만 2배가 됩니다.

의미 있는 차이가 생기는 경우는 셋뿐입니다:

1. **스플라인/베지어 보간으로 리샘플**할 때 — 30fps 키 사이(33ms)를 직선으로 잇던 걸 곡선으로 복원하므로,
   빠른 스윙·펀치처럼 **아크가 뭉개지던 구간**이 약간 살아납니다. 개선폭은 작지만 공짜입니다.
2. **AI 인비트위닝**으로 물리적으로 그럴듯한 중간 포즈를 **새로 생성**할 때 — 이게 진짜입니다.
3. 애니메이션 압축 설정이 키를 과하게 줄이고 있을 때 — 이건 압축 설정 문제지 fps 문제가 아닙니다.

### ⚠️ 쓰면 안 되는 것: 영상용 AI 프레임 보간

**RIFE / DAIN / FILM / Topaz Video AI 는 여기에 못 씁니다.**
이들은 **픽셀**을 보간하는 모델입니다. 스켈레탈 애니메이션은 픽셀이 아니라
**본별 위치·회전 트랙**이므로 입력 자체가 성립하지 않습니다.
(이미 렌더링을 끝낸 **영상 파일**을 60fps로 만들 때만 해당됩니다.)

---

## 1. 방법 A — 결정론적 리샘플 (Blender 리베이크)

Epic 포럼의 결론도 같습니다: **UE에 내장 변환 기능은 없고, 소스 툴에서 60fps로 리베이크해 재임포트하는 것이 정석**입니다.
(UE 임포트의 `Custom Frame Rate` 옵션은 원본이 최소 30fps일 때만 제대로 동작합니다.)

### 핵심 순서

1. **임포트 전에** 씬 FPS를 60으로 설정 (FBX는 시간을 초 단위로 저장하므로, 씬 fps에 맞춰 키가 배치됨)
2. FBX 임포트
3. `Bake Action`을 `step=1`로 실행 → 매 프레임 키 생성
4. FBX 익스포트

### 배치 스크립트 (Blender 4.x, `blender --background --python resample.py`)

```python
import bpy, os

DST_FPS = 60          # 원본은 30fps. 씬을 60으로 두고 매 프레임 베이크한다
IN_DIR  = "/path/to/fbx_30fps"
OUT_DIR = "/path/to/fbx_60fps"
os.makedirs(OUT_DIR, exist_ok=True)

for name in sorted(f for f in os.listdir(IN_DIR) if f.lower().endswith(".fbx")):
    bpy.ops.wm.read_homefile(use_empty=True)

    scene = bpy.context.scene
    scene.render.fps = DST_FPS          # ← 반드시 임포트 '전에'
    scene.render.fps_base = 1.0

    bpy.ops.import_scene.fbx(filepath=os.path.join(IN_DIR, name))

    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')

    start, end = (int(v) for v in arm.animation_data.action.frame_range)

    bpy.ops.nla.bake(
        frame_start=start, frame_end=end, step=1,
        only_selected=True, visual_keying=True,
        clear_constraints=False, clear_parents=False,
        use_current_action=True, bake_types={'POSE'},
    )
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT_DIR, name),
        object_types={'ARMATURE'},
        add_leaf_bones=False,           # UE 스켈레톤 불일치 방지
        bake_anim=True,
        bake_anim_use_nla_strips=False,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,  # 키 간소화 끄기
        apply_scale_options='FBX_SCALE_ALL',
    )
```

> **아크를 살리고 싶다면** 베이크 전에 F-Curve 보간을 `BEZIER`로 바꾸고
> 핸들을 `AUTO_CLAMPED`로 둔 뒤 베이크하세요. 위 (a)의 1번 케이스에 해당하는 소소한 개선입니다.

---

## 2. 방법 B — AI 인비트위닝 (Cascadeur, 가장 실용적)

**Cascadeur**는 2025.1에서 **AI Inbetweening**을 도입하고 2025.2에서 크게 확장했습니다.
키프레임 사이를 단순 보간하는 대신, **학습된 애니메이션 데이터를 근거로 중간 포즈를 "추측해서" 생성**합니다.
키 포즈·타이밍·키 개수·애니메이션 스타일을 보고 예측합니다. 무료 티어가 있고 FBX 왕복이 됩니다.

### 순서

1. **빈 씬의 FPS를 먼저 60으로 설정** — Cascadeur 기본이 30fps라, 모델을 임포트하기 전에 바꿔야 합니다
2. 30fps FBX 임포트
3. 원본의 촘촘한 키를 **핵심 포즈만 남기고 정리** (여기가 중요 — 키가 매 프레임 박혀 있으면 AI가 낄 틈이 없음)
4. **AI Inbetweening** 실행 → 60fps 구간을 생성
5. 물리 보정(AutoPhysics)·발 접지 확인
6. FBX 익스포트 → UE5

### ⚠️ 한계 (공식 문서 명시)

Inbetweening은 **곡선·궤적·환경 컨텍스트를 따르지 않습니다.**
따라서 다음은 **반드시 수동 확인**해야 합니다:

- 발이 바닥을 뚫거나 미끄러지는지 (접지)
- 무기·손의 궤적이 원래 노리던 라인을 지키는지
- 총기 재장전처럼 **손과 소품이 정확히 맞물려야 하는** 구간

폴아웃 4 애니메이션은 재장전·근접공격이 많아 이 부분이 실제로 자주 깨집니다.

---

## 3. 방법 C — 오픈소스 모션 디퓨전 (배치 / 연구용)

수백 개를 스크립트로 돌려야 하거나 파이프라인에 박아 넣어야 할 때.

| 프로젝트 | 내용 |
|---|---|
| **Kimodo** (NVIDIA Toronto AI Lab, 2026-03) | 키네마틱 모션 디퓨전 모델. **MotionBricks**로 실시간 모션 인비트위닝. SMPL-X 등 다중 스켈레톤 지원. <https://github.com/nv-tlabs/kimodo> |
| **Silk** (2025, CVPRW) | 모션 인비트위닝용 스무스 인터폴레이션 프레임워크 |
| **Flexible Motion In-betweening with Diffusion Models** (SIGGRAPH 2024) | 디퓨전 기반 인비트위닝의 기준 논문 |
| **Robust Motion In-betweening** (SIGGRAPH 2020) | 이 분야의 고전. 대부분의 후속 연구가 여기서 출발 |

대부분 **BVH / SMPL 기준**이라 실무에 쓰려면 `FBX ↔ BVH ↔ 모델 스켈레톤` 리타게팅 왕복이 필요합니다.
폴아웃 4 스켈레톤은 본 이름·비율이 표준과 다르므로 이 왕복에서 손실이 생길 수 있습니다.
**소수 정예 애니메이션만 골라서** 적용하는 편이 현실적입니다.

---

## 4. MCP로 파이프라인 자동화

### 4-1. Unreal MCP (Epic 공식, UE 5.8 Experimental)

UE 5.8부터 **에디터 프로세스 안에 MCP 서버가 내장**됩니다. Claude Code가 로컬 HTTP로 에디터를 직접 조작합니다.

```
1) Edit > Plugins  →  "Unreal MCP" + "All Toolsets" 활성화  (에디터 자동 재시작)
2) Edit > Editor Preferences > General > Model Context Protocol  →  Auto Start Server 켜기
3) 콘솔(` 키) 에서:
      ModelContextProtocol.GenerateClientConfig ClaudeCode
   →  프로젝트 루트에 .mcp.json 생성됨
4) 그 프로젝트 루트에서 Claude Code 실행  →  자동 연결
```

- 기본 주소: `http://127.0.0.1:8000/mcp` (Editor Preferences에서 포트/경로 변경 가능)
- **제약**: 루프백 전용(비-loopback 연결 거부), **인증 없음**, HTTP/SSE만 지원(WebSocket·stdio 불가), Experimental
- 액터 스폰, 블루프린트 편집, 머티리얼, Sequencer, Control Rig 등이 툴로 노출됩니다

> 서드파티 대안: [GenOrca/unreal-mcp](https://github.com/GenOrca/unreal-mcp), [ClaudeUnreal](https://echoulen.github.io/claude-unreal/docs/) (UE 5.7/5.8)

### 4-2. Blender MCP

```
1) blender-mcp 저장소에서 addon.py 다운로드
2) Blender: Edit > Preferences > Add-ons > Install…  →  addon.py 선택  →  "Interface: Blender MCP" 체크
3) 3D 뷰포트에서 N  →  BlenderMCP 탭  →  서버 시작
4) MCP 설정에 추가:   command: "uvx",  args: ["blender-mcp"]
```

<https://github.com/ahujasid/blender-mcp>

### 4-3. 조합 시나리오

```
Claude Code
  ├─ Blender MCP  →  30fps FBX 임포트 → 60fps 리베이크 → FBX 익스포트
  │                   (또는 Cascadeur에 넘길 키 정리 작업)
  └─ Unreal MCP   →  FBX 임포트, 스켈레톤 지정, 압축 설정 확인,
                      AnimSequence 프레임레이트 검증, 미리보기 스폰
```

**현실적인 조언**: 리베이크 자체는 위의 Blender 배치 스크립트가 MCP보다 빠르고 안정적입니다.
MCP가 진짜 값어치를 하는 건 **결과 검증**입니다 — 임포트된 AnimSequence를 열어서
프레임레이트·키 개수·압축 설정을 확인하고, 이상한 애셋을 골라내는 반복 작업.
"200개 구웠는데 그중 뭐가 깨졌는지" 찾는 일에 쓰세요.

---

## 5. UE5 임포트 쪽 체크리스트

- `Use Default Sample Rate` **해제** → `60` 입력
- `Animation Length`: `Exported Time`
- `Custom Frame Rate`는 **원본이 30fps 이상일 때만** 정상 동작 (Epic 포럼 확인 사항)
- **압축 설정 확인** — 60fps로 구워 넣어도 Anim Compression이 키를 다시 쳐낼 수 있습니다.
  프로젝트 세팅의 Animation Compression Settings와 해당 AnimSequence의 압축 스킴을 확인하세요.
  용량이 2배가 됐는데 압축이 원래대로 깎아버리면 **아무것도 안 한 것**이 됩니다.
- UE5 파이썬의 `AnimSequence.target_frame_rate` / `resampled_animation_track_data` 는 **읽기 전용**입니다.
  → 엔진 안에서 리샘플할 생각 말고 소스에서 처리하세요.

---

## 6. 폴아웃 4 맥락에서의 현실적 권장안

1. **전부 60fps로 굽지 마세요.** 원본 30fps를 그대로 넣고 UE 런타임 보간에 맡기는 게 기본값입니다.
   용량·빌드 시간만 늘고 화면상 차이는 대부분 없습니다.
2. **눈에 띄는 것만 고르세요.** 근접 공격, 재장전, 처형 모션처럼 **빠르고 카메라가 가까운** 것들.
   보통 전체의 5~10%입니다.
3. 고른 것만 **Cascadeur AI Inbetweening**으로 처리하고, 발 접지와 손-소품 정합을 손봅니다.
4. 나머지는 방법 A의 **베지어 리샘플**로 일괄 처리하거나, 아예 건드리지 않습니다.
5. 전체 순서:
   ```
   hkx → FBX (이전 문서)  →  ① 선별  →  ② 60fps 처리(A 또는 B)  →  UE5 임포트  →  IK Retarget
   ```

---

## 7. 자주 터지는 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| 60fps로 바꿨는데 차이가 없음 | 선형 리샘플이라 정보량이 동일 | 정상입니다. AI 인비트위닝(방법 B)으로 가거나 그냥 30fps 유지 |
| 애셋 용량만 2배 | 위와 같음 | 선별 적용으로 전환 |
| AI 인비트윈 후 발이 미끄러짐 | Inbetweening이 환경 컨텍스트를 안 봄 | 접지 키 수동 고정, IK 보정 |
| 재장전에서 손과 총이 어긋남 | 소품 정합을 AI가 보장 안 함 | 해당 구간은 원본 키 유지 |
| Cascadeur에서 타이밍이 2배 빨라짐 | 임포트 후에 씬 fps를 바꿈 | **임포트 전에** 빈 씬을 60fps로 설정 |
| UE에서 키가 도로 줄어듦 | 애니메이션 압축 | 압축 스킴 확인 및 조정 |
| 블렌더 베이크 후 UE 스켈레톤 거부 | `Add Leaf Bones` 켜짐 | 익스포트에서 끄기 |
| MCP 서버 연결 안 됨 | 루프백 전용 / 포트 충돌 / stdio 미지원 | `127.0.0.1:8000/mcp` 확인, Editor Preferences에서 포트 변경 |

---

## 8. 참고 링크

**AI 인비트위닝**
- Cascadeur 2025.1 AI Inbetweening — <https://cascadeur.com/blog/general/cascadeur-20251-released-faster-animation-workflows-with-ai-inbetweening>
- Cascadeur 2025.2 — <https://cascadeur.com/blog/view/cascadeur-2025-2-brings-massive-ai-inbetweening-workflow-upgrades>
- Cascadeur Inbetweening 문서 — <https://cascadeur.com/help/category/278>
- Kimodo (NVIDIA) — <https://github.com/nv-tlabs/kimodo>

**MCP**
- Unreal MCP 공식 문서 — <https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor>
- Unreal MCP 플러그인 인덱스 — <https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/ModelContextProtocol>
- blender-mcp — <https://github.com/ahujasid/blender-mcp>
- GenOrca/unreal-mcp — <https://github.com/GenOrca/unreal-mcp>
- ClaudeUnreal — <https://echoulen.github.io/claude-unreal/docs/>

**UE5 애니메이션**
- 30fps → 60fps 변환 논의 (Epic 포럼) — <https://forums.unrealengine.com/t/convert-player-animation-30-fps-into-60-fps/2448889>
- `unreal.AnimSequence` 파이썬 API — <https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AnimSequence>
- `unreal.AnimationLibrary` — <https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AnimationLibrary>
