# VFX 테스트 환경 (VFX Test Environment)

VFX를 만들 때 필요한 것은 "예쁜 맵"이 아니라 **효과를 정직하게 판단할 수 있는 중립적인 무대**입니다.
아래는 그 무대를 마련하는 세 가지 경로입니다. 위에서부터 순서대로 보시면 됩니다.

---

## 1순위 — Unity 공식 VFX Graph Learning Templates (무료, 즉시)

가장 빠르고, 가장 정확하게 목적에 맞는 선택지입니다. **URP·HDRP 씬이 모두 들어 있는 VFX 전용 테스트 씬**과
25개 이상의 VFX Graph 에셋이 함께 제공됩니다. 각 그래프에 해설 노트가 붙어 있어 레퍼런스로도 좋습니다.

설치:

1. `Window > Package Manager`
2. 목록에서 **Visual Effect Graph** 선택
3. `Samples` 탭 → **Learning Templates** → `Import`
4. `Assets/Samples/.../` 안에서 렌더 파이프라인에 맞는 씬(URP 또는 HDRP)을 엽니다

> Unity 6 이상 / VFX Graph 16.0 이상에서 지원됩니다. VFX Graph 자체는 **URP 또는 HDRP가 필요**하며,
> Built-in 파이프라인에서는 동작하지 않습니다.

추가로 Unity 공식 GitHub 샘플 프로젝트(`Unity-Technologies/VisualEffectGraph-Samples`)에는
`Bonfire`(불·연기 + 커스텀 Shader Graph 렌더링), `Ribbon Pack`(파티클 스트립) 같은 완성형 씬이 들어 있습니다.

## 2순위 — 이 저장소의 자체 테스트베드 (외부 에셋 0개)

`Assets/VFXTestbed/` 에 넣어두었습니다. 메뉴에서 **`Tools > VFX Testbed > Build Test Stage`** 한 번이면
씬이 통째로 생성됩니다. 다운로드도, 라이선스 확인도 필요 없습니다.

- 1m 격자 바닥 + 스케일 기준물(1m 큐브 / 1.8m 인체 / 0.5m 구)
- 배경값 4단계 전환 — 중간 회색 / 검정 / 흰색 / 황혼
- 라이팅 프리셋 4종 — 스튜디오 / **암실(Black box)** / 야간+안개 / 주광
- HDR 켜진 턴테이블 카메라, 블룸 볼륨 on/off, 슬로모션·일시정지·리스타트

자세한 조작법은 [`Assets/VFXTestbed/README.md`](../Assets/VFXTestbed/README.md) 참고.

## 3순위 — 실제 환경 에셋 (룩을 최종 확인할 때)

중립 무대에서 통과한 효과는 반드시 **실제 게임과 비슷한 환경**에서 한 번 더 봐야 합니다.

| 용도 | 추천 | 라이선스 |
|---|---|---|
| **라이팅/반사 검증** | [Poly Haven](https://polyhaven.com) HDRI | CC0 |
| PBR 바닥·벽 텍스처 | [ambientCG](https://ambientcg.com) | CC0 |
| 저폴리 던전/실내 | [KayKit](https://kaylousberg.itch.io) | CC0 |
| 저폴리 야외/캐릭터 | [Quaternius](https://quaternius.com) | CC0 |
| 프로토타입 전반 | [Kenney](https://kenney.nl) | CC0 |
| 사실적 환경 | [Fab](https://fab.com) — Quixel Megascans | Fab Standard License (Unity 사용 가능) |

> ⚠️ Unity Asset Store · Synty · Fab 유료 에셋은 **재배포 금지**입니다.
> public 저장소에 커밋하지 마세요. `.gitignore`에 `Assets/ThirdParty/` 를 이미 넣어 두었습니다.

---

## VFX 검수 체크리스트

무대가 갖춰졌다면, 아래를 순서대로 확인하는 것이 실무 흐름입니다.

**읽힘 (Readability)**
- [ ] 검정 배경과 흰색 배경 **양쪽**에서 형태가 읽히는가
- [ ] **블룸을 껐을 때도** 효과가 성립하는가 (블룸에 의존하면 다른 씬에서 무너집니다)
- [ ] 암실 프리셋에서 효과의 자체 발광만으로 실루엣이 나오는가

**스케일 · 타이밍**
- [ ] 1m 큐브 / 1.8m 인체 기준으로 크기가 의도대로인가
- [ ] 슬로모션(0.25x)에서 시작·피크·소멸이 명확히 구분되는가
- [ ] 루프 효과의 이음새가 튀지 않는가

**카메라**
- [ ] 턴테이블로 360° 돌렸을 때 빌보드/평면이 납작하게 드러나지 않는가
- [ ] 근거리·원거리 모두에서 성립하는가

**성능**
- [ ] Overdraw 뷰(Scene view 좌상단 드롭다운)에서 과도하게 붉지 않은가
- [ ] 파티클 수와 GPU 시간이 예산 안에 있는가 (`Window > Analysis > Profiler`)

**프로젝트 설정**
- [ ] Color Space = **Linear** (`Project Settings > Player`) — Gamma면 HDR·블룸이 어긋납니다
- [ ] 카메라 **HDR 활성화** — 꺼져 있으면 밝은 값이 흰색으로 잘려 블룸이 안 먹습니다

---

## 참고 링크

- [Learning Templates Sample Content — Visual Effect Graph 매뉴얼](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.2/manual/sample-learningTemplates.html)
- [Visual Effect Graph Sample Content](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.0/manual/sample-content.html)
- [Unity-Technologies/VisualEffectGraph-Samples (GitHub)](https://github.com/Unity-Technologies/VisualEffectGraph-Samples)
- [Unity 6 E-Book: Get the Most Out of VFX Graph](https://unity.com/blog/unity-6-vfx-graph-ebook)
- [무료 Unity VFX 에셋 (itch.io)](https://itch.io/game-assets/free/tag-unity/tag-vfx)
- [Unity Asset Store — VFX 카테고리](https://assetstore.unity.com/vfx)
