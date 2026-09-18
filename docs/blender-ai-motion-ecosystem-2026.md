# 블렌더 AI 모션 생성 · 리타겟 생태계 (2026)

텍스트→모션(Text-to-Motion) 결과를 블렌더 리그에 바로 올리거나, 서로 다른 뼈대 사이 리타겟·블렌딩을 줄이는 오픈소스/플러그인 흐름을 정리한다.  
아래 프로젝트는 2026-09 기준 GitHub·논문·공식 README로 존재 여부를 확인했다.

---

## 한 줄 결론 — 목적별 추천

| 목적 | 1순위 | 대안 |
|------|--------|------|
| **커스텀 휴머노이드 리그에 AI 모션 입히기** (Mixamo / VRoid / MMD / 자체 본) | [atticus-lv/kimodo_motion](https://github.com/atticus-lv/kimodo_motion) (로컬 GPU) 또는 [Animatica Blender Plugin](https://github.com/animatica-ai/animatica-blender-plugin) (클라우드/셀프호스트 MMCP) | MDM 애드온은 SMPL 전용 → 별도 리타겟 필요 |
| **텍스트만으로 키프레임/액션 뽑기** | 위 Kimodo 계열 (Action 데이터블록 생성) | [UuuNyaa/blender_motion_generate_tools](https://github.com/UuuNyaa/blender_motion_generate_tools) (MDM, SMPL 고정) |
| **뼈 구조가 다른 캐릭터끼리 블렌드·리타겟** (동물↔동물 등) | [mmlab-cv/BlendAnything](https://github.com/mmlab-cv/BlendAnything) (SIGGRAPH Posters 2026) | 휴머노이드 전용 Kimodo와 역할이 겹치지 않음 |
| **단일 비디오 → 4D 메시 모션** (리그 애니 아님) | [Inception3D/Motion324](https://github.com/Inception3D/Motion324) (CVPR 2026) | 렌더/시각화에 Blender 4.0 사용 |
| **LLM 에이전트 + BPY/비전 실험 파이프라인** | [ahmedsayed1911/Blender-AI-Agent](https://github.com/ahmedsayed1911/Blender-AI-Agent) | 프로덕션 애니 도구라기보다 실험 스택 |

**최근 실무 팁:** AI로 100% 무에서 유를 만들기보다, 블렌더에서 동선·카메라만 블로킹 렌더한 뒤 디퓨전 비디오 모델의 레퍼런스로 넣는 방식이 카메라 제어에 유리하다. 캐릭터 스켈레탈 모션은 위 표의 Textto-Motion / BlendAnything** 축이 담당한다.

---

## 1. BlendAnything — 크로스 토폴로지 모션 블렌딩 (SIGGRAPH Posters 2026)

- **저장소:** https://github.com/mmlab-cv/BlendAnything  
- **프로젝트 페이지:** https://mmlab-cv.github.io/BlendAnything/  
- **논문:** ACM SIGGRAPH Posters 2026, doi [10.1145/3799825.3818769](https://doi.org/10.1145/3799825.3818769)

### 무엇을 하나

블렌더 **NLA 에디터** 위에서 레퍼런스 스트립 + 타깃 스트립을 고르면, 로컬(또는 원격) **FastAPI/Uvicorn** 서버가 neural motion blending으로:

- 동일 스켈레톤 내 부드러운 블렌드  
- **뼈 대응이 없는** 크로스 스켈레톤 블렌드  
- 레퍼런스 influence를 0에 가깝게 두면 **리타겟**으로도 동작  

결과를 다시 NLA 스트립으로 가져온다. Truebones / Mixamo 계열 샘플 BVH가 `samples/`에 있다.

### 요구 사항 (공식 README)

| 구분 | 내용 |
|------|------|
| Blender 클라이언트 | **4.5.4 LTS** |
| 서버 | Linux x86-64 권장, **NVIDIA CUDA**, PyTorch 2.4.1 / CUDA 12.1 참고 환경 |
| 서버 Python | **3.8.15** (`neural_motion_blending` conda env) |
| 기본 엔드포인트 | `http://localhost:8000` |

Windows/macOS **서버**는 공식 검증되지 않았다. 클라이언트만 다른 OS에서 돌리고 서버는 Linux GPU 머신에 두는 구성이 현실적이다.

### 설치 요약

```bash
git clone --recursive https://github.com/mmlab-cv/BlendAnything.git
cd BlendAnything

# 모델: Drive의 blendany_model_weights.zip →
#   neural_motion_blending/save/<model_name>/args.json + model*.pt

conda env create --file neural_motion_blending/environment.yml
conda activate neural_motion_blending
pip install -r blendanything_server/requirements.txt
pip install --no-build-isolation git+https://github.com/inbar-2344/Motion.git

uvicorn blendanything_server.app:app --reload
```

클라이언트: `blendanything_client/` 디렉터리를 zip → Blender Add-ons Install.  
필요 시 Blender 내장 Python에 `requests` 설치. N-panel **Neural Blend**에서 Server URL 확인 후 **Import BVH** → 스트립 배치 → **Run Neural Blend**.

상세: 저장소 `docs/usage.md`, `docs/skeletons.md`, `docs/api.md`.

### 커스텀 리그와의 관계

휴머노이드 “바닐라 본”에 텍스트 모션을 바로 얹는 도구가 아니라, **이미 BVH/NLA로 올린 클립**을 서로 다른 토폴로지 사이에서 섞거나 옮기는 쪽에 강하다. 자체 리그를 쓰려면 스켈레톤/페이스 조인트 등록을 `docs/skeletons.md` 절차로 맞춰야 한다.

---

## 2. 블렌더 내 Text-to-Motion 애드온

### 2-A. Blender Kimodo Motion (`atticus-lv/kimodo_motion`)

- **저장소:** https://github.com/atticus-lv/kimodo_motion  
- **기반:** NVIDIA Kimodo (SOMA 77-joint), Xingxun 원본 애드온을 macOS Metal/MPS·인-블렌더 리타겟·Extension 패키징으로 확장  
- **Blender:** **5.0+**  
- **가속:** Windows/Linux CUDA, macOS Apple Silicon MPS

흐름:

1. Mixamo / VRoid / MMD / 커스텀 휴머노이드 아마추어 선택  
2. 영문(또는 중문·번역 모드) 프롬프트 입력  
3. 로컬 Kimodo 서버가 SOMA 모션 생성  
4. **FBX 왕복 없이** `bpy` 리타겟 → Action `Kimodo_*_sNN`

Windows/macOS는 N-panel **One-click install runtime**. Linux는 `INSTALL_EN.md` 수동 venv.  
텍스트 인코더용 **Meta-Llama-3-8B-Instruct** (~16 GB, Meta gated 또는 ungated mirror), 디스크 약 25–50 GB, VRAM 16 GB+ 권장.

> “공식 NVIDIA 확장팩”은 아니다. NVIDIA는 모델/코드를 공개하고, 블렌더 포팅은 커뮤니티(Atticus / Xingxun)다. MMCP 쪽 공식에 가까운 클라이언트는 아래 Animatica다.

### 2-B. Animatica (구 Proscenium) + `motionmcp-kimodo`

- **Blender 플러그인:** https://github.com/animatica-ai/animatica-blender-plugin (Blender **5+**, GPL)  
- **로컬 MMCP 서버:** https://github.com/animatica-ai/motionmcp-kimodo  
- **프로토콜:** [MotionMCP](https://animatica.ai/mmcp/docs/get-started/implementations)

클라우드(Animatica 계정)가 기본이고, 로컬 GPU면:

```bash
pip install "motionmcp-kimodo @ git+https://github.com/animatica-ai/motionmcp-kimodo.git"
motionmcp-kimodo --port 8000
```

애드온 Preferences에서 Server를 `http://localhost:8000`으로 지정.  
프롬프트뿐 아니라 타임라인 키포즈·경로·손/발 핀 등 **제약 기반** 생성이 강점이다.

### 2-C. MDM 애드온 (`UuuNyaa/blender_motion_generate_tools`)

- **저장소:** https://github.com/UuuNyaa/blender_motion_generate_tools  
- **모델:** [MDM (Human Motion Diffusion Model)](https://github.com/GuyTevet/motion-diffusion-model)  
- **Blender:** 3.3 LTS+  
- **한계:** **SMPL 아마추어만**. 마지막 활발한 업데이트가 오래되어(2023) 최신 Blender/CUDA와 맞물림을 직접 확인해야 한다.

설치 개요: Release zip 설치 → Preferences에서 Python 모듈(CUDA 옵션) 업데이트 → CLIP 다운로드 → 재시작 → 제공 `smpl_model_*.blend`의 `SMPLX-neutral` 선택 → Sidebar **Motion Generator**.

커스텀 리그에 쓰려면 MDM 결과를 BVH/FBX로 뽑은 뒤 **별도 리타겟**(Rokoko, Blender Retarget, BlendAnything 등)이 필요하다. “바로 입히기”에는 Kimodo/Animatica가 맞다.

---

## 3. 비디오 기반 4D · 에이전트 워크플로

### 3-A. Motion324 / Motion 3-to-4 (CVPR 2026)

- **저장소:** https://github.com/Inception3D/Motion324  
- **페이지:** https://motion3-to-4.github.io/  
- **역할:** 단안 비디오(+선택적 참조 메시)에서 **4D 동적 오브젝트(정점 궤적)** 를 feed-forward로 복원

블렌더는 **리그 연동 애드온이 아니라** 결과 렌더/시각화 컴포넌트다. 공식은 Blender **4.0.0** Linux 빌드 + `scripts/render_results.py`(bpy-renderer 계열).

```bash
conda create -n Motion324 python=3.11
conda activate Motion324
pip install -r requirements.txt
# 체크포인트: Hugging Face River-Chen/Motion324 → experiments/checkpoints/

./scripts/4D_from_existing.sh ./examples/chili.glb ./examples/chili.mp4 ./examples/chili
python scripts/render_results.py -- --output_dir ./examples/chili
```

휴머노이드 본 애니메이션 파이프라인과는 목적 공간이 다르다(메시 4D vs 스켈레탈 Action).

### 3-B. Blender-AI-Agent

- **저장소:** https://github.com/ahmedsayed1911/Blender-AI-Agent  
- LLM 플래닝 → MCP 경계의 검증된 Blender 도구 → 비전 리뷰 → semantic motion → GLB/MP4, FastAPI + Three.js 스튜디오

캐릭터 모션 “생성기” 하나로 쓰기보다, 에이전트·안전 경계·스튜디오 UI를 묶은 **실험 플랫폼**으로 보는 것이 맞다.

---

## 4. 목적별 로컬 설치 · 연동 가이드

### 경로 A — 커스텀 휴머노이드에 AI 모션 입히기

**권장:** Kimodo Motion (완전 로컬) 또는 Animatica (빠른 시작).

1. Blender 5.0+에서 캐릭터 아마추어가 **휴머노이드 계층**(골반→척추→머리, 좌우 팔다리)인지 확인. Mixamo 네이밍이면 프리셋 매칭이 쉽다.  
2. Kimodo: Extension zip 설치 → Runtime one-click(또는 Linux 수동) → Llama-3 가중치.  
3. 아마추어 선택 → 프롬프트(예: `A person walks forward and waves the right hand.`) → Generate.  
4. NLA에서 Action을 클립으로 쌓고, 손 접지·발 미끄러짐은 Graph/수동 보정 또는 Kimodo post_processing(옵션)으로 다듬기.

**Animatica 셀프호스트 시** 서버 URL만 `localhost:8000`으로 맞추면 동일하게 타깃 아마추어에 Action이 쌓인다.

최소 확인용 bpy 스케치 (생성 후 Action 목록 점검):

```python
import bpy

arm = bpy.context.object
assert arm and arm.type == "ARMATURE", "Select an armature"

for act in bpy.data.actions:
    if act.name.startswith("Kimodo_") or "animatica" in act.name.lower():
        print(act.name, "fcurves=", len(act.fcurves))
```

### 경로 B — 텍스트 → 키프레임/액션 데이터만 필요

1. **Kimodo / Animatica:** 결과물 자체가 Blender Action(키프레임). FBX/BVH로보내면 엔진·다른 DCC로 넘길 수 있다.  
2. **MDM 애드온:** SMPL 전용. 학습·연구·HumanML3D 스타일 프롬프트 실험에 적합. 게임 캐릭터 직결은 비추.

Action → BVH 내보내기 예시:

```python
import bpy

arm = bpy.context.object
# arm에 원하는 Action이 active/NLA에 연결되어 있다고 가정
bpy.ops.export_anim.bvh(
    filepath="/tmp/ai_motion.bvh",
    frame_start=bpy.context.scene.frame_start,
    frame_end=bpy.context.scene.frame_end,
    root_transform_only=False,
)
```

(Blender 버전에 따라 BVH 연산자 옵션 이름이 다를 수 있으니 Preferences의 Export 패널과 맞춰 조정.)

### 경로 C — 토폴로지가 다른 클립끼리 섞기

BlendAnything 서버를 띄운 뒤, NLA에서 BVH 임포트 → Neural Blend.  
휴머노이드 Text-to-Motion 결과(Kimodo BVH)를 동물 리그에 옮기는 식의 **2단 파이프라인**도 가능하다: Kimodo로 인간 모션 생성 → BlendAnything로 타깃 스켈레톤 리타겟.

---

## 5. 비교 한눈에

| 프로젝트 | 입력 | 출력 | 블렌더 역할 | GPU | 성숙도(체감) |
|----------|------|------|-------------|-----|----------------|
| BlendAnything | NLA/BVH 클립 | 블렌드·리타겟 클립 | 애드온 클라이언트 | 서버 CUDA 필수 | 연구 릴리스 1.0 (2026-06) |
| kimodo_motion | 텍스트 | Action on rig | 애드온+로컬 서버 | CUDA/MPS | 실사용에 가까움, Linux 수동 |
| Animatica + MMCP | 텍스트·제약 | Action on rig | 공식 MMCP 클라이언트 | 클라우드 또는 로컬 CUDA | 제품/프로토콜 축 |
| motion_generate_tools | 텍스트 | SMPL 키프레임 | 애드온 내장 추론 | CUDA 권장 | 구형·SMPL 전용 |
| Motion324 | 비디오(+메시) | 4D 메시 시퀀스 | 렌더 백엔드 | CUDA compute > 8.0 | CVPR 연구 코드 |
| Blender-AI-Agent | LLM/비전 | 씬·모션·GLB/MP4 | MCP+애드온 | 구성에 따름 | 초기 실험 |

---

## 6. 자주 하는 오해

1. **Motion324 ≠ 캐릭터 리깅 애니 플러그인.** 비디오→4D 메시이고, 블렌더는 렌더용이다.  
2. **Kimodo “공식 블렌더 확장”은 NVIDIA 스토어 제품이 아님.** atticus-lv / Animatica가 각각 로컬·MMCP 경로.  
3. **MDM 애드온으로 커스텀 본에 바로 붙지 않음.** SMPL → 리타겟 추가 공정.  
4. **BlendAnything 서버는 Linux+CUDA 전제.** 맥북만으로는 서버 쪽을 공식 지원하지 않는다.  
5. **스타 수 ≠ 적합도.** Motion324가 스타가 많아도 스켈레탈 파이프라인 대체재는 아니다.

---

## 참고 링크

- BlendAnything: https://github.com/mmlab-cv/BlendAnything  
- Neural Motion Blending (백본): https://mmlab-cv.github.io/neural_motion_blending/  
- Kimodo Motion (Blender): https://github.com/atticus-lv/kimodo_motion  
- NVIDIA Kimodo: https://github.com/nv-tlabs/kimodo  
- Animatica Blender Plugin: https://github.com/animatica-ai/animatica-blender-plugin  
- motionmcp-kimodo: https://github.com/animatica-ai/motionmcp-kimodo  
- MDM Blender tools: https://github.com/UuuNyaa/blender_motion_generate_tools  
- Motion324: https://github.com/Inception3D/Motion324  
- Blender-AI-Agent: https://github.com/ahmedsayed1911/Blender-AI-Agent  

관련 저장소 문서: `docs/animation-60fps-ai-mcp.md` (Kimodo·MCP·UE5 60fps 맥락).
