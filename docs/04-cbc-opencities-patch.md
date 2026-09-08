# 4차 기획서 — City Bag Checks × Open Cities Skyrim 호환 패치

| 항목 | 내용 |
|---|---|
| 문서 번호 | 4차 기획서 |
| 상태 | 설계안 — **미검증 전제 포함. 2장 통과 전 제작 착수 금지** |
| 대상 | `City Bag Checks` (SSE 112212, v1.0.4) ↔ `Open Cities Skyrim` (SSE 87707, v3.2.4) |
| 선행 문서 | 「Open Cities Skyrim 도입 검토」 |
| 비고 | 1~3차 기획서는 본 리포지토리 및 원격 브랜치에 존재하지 않음. 지시에 따라 4차로 번호 부여 |

---

## 1. 문제 정의

City Bag Checks(이하 **CBC**)는 검문 발동 조건을 다음과 같이 구현한다. Readme 원문:

> "The game checks for guards standing near the gate with the following Ref Type: **CWMainGateExterior**."
>
> "Added a condition to the forcegreet package and guard dialogue to only trigger if the player is in the **Tamriel worldspace**."
>
> "**Bag checks are not meant to occur in the city world spaces.**"
>
> "Bag check events only end when you walk into a **wilderness cell** to help prevent multiple events"

### 핵심 명제

> **CBC는 "플레이어가 Tamriel 월드스페이스에 있다"를 "플레이어가 도시 밖에 있다"의 대용(proxy)으로 사용한다.**
> **Open Cities Skyrim(이하 OCS)은 도시를 Tamriel 안으로 이식하므로, 그 대용 관계를 무너뜨린다.**

바닐라에서는 도시가 별도 월드스페이스이므로 대용이 성립한다. OCS 적용 시 도시 내부에서도 조건이 참이 되어, 제작자가 명시적으로 차단하려 한 동작이 열린다.

### 예상 증상

| ID | 증상 | 근거 |
|---|---|---|
| S1 | 성문 검문은 정상 작동 | `CWMainGateExterior` 마커와 성문 구조물이 OCS에서도 Tamriel에 잔존할 것으로 추정 |
| S2 | **도시 내부에서 경비병 forcegreet 발생** | 월드스페이스 가드가 무력화됨 |
| S3 | **검문 이벤트 미종료 / 반복 발동** | 종료 조건("야생 셀 진입")이 성립하지 않음 |

**S1~S3은 Readme의 트리거 로직에서 도출한 추론이며, 확인된 버그 보고가 아니다.** 검색 범위 내에서 CBC↔OCS 전용 패치는 발견되지 않았고 CBC Readme에도 OCS 언급이 없다.

---

## 2. 검증 단계 (P0) — 설계 확정의 선행 조건

전제가 추론이므로 **제작보다 검증이 먼저다.** V2가 음성이면 이 패치는 불필요하며, 그 결론 자체를 산출물로 삼는다.

| ID | 검증 항목 | 방법 | 이 결과가 바꾸는 것 |
|---|---|---|---|
| **V1** | OCS에서 성문 검문이 발동하는가 | xEdit으로 OCS 플러그인이 `CWMainGateExterior` RefType 레퍼런스를 삭제/이동했는지 확인 → MCM 빈도 100%로 5개 도시 성문 진입 | 음성이면 문제가 "오발동"이 아니라 "무발동"이며, 설계 방향이 전면 반전 |
| **V2** | 도시 내부에서 오발동하는가 | 마약류 소지 상태로 도시 안 경비병 근처 배회 | **음성이면 패치 불요** → 결론 문서화하고 종료 |
| **V3** | 이벤트가 종료되는가 | 검문 1회 후 도시 진입, 재발동/중복 관찰 | 양성이면 종료 조건 보정(3.4)이 범위에 포함 |
| **V4** | Location 경계는 어디인가 | 성문 밖→안 이동하며 콘솔 `player.getcurrentlocation` 반복 출력 | **설계 파라미터.** 경계가 성문 바깥이면 안 A 무효 → 안 B |

V4가 이 기획서에서 가장 중요한 미지수다. 경계가 성벽선과 일치해야 안 A가 성립하고, 성문 바깥 접근로까지 도시 Location으로 잡히면 안 A는 검문을 통째로 죽인다.

---

## 3. 설계안

### 3.1 안 A (권장) — 조건식 교체, 무스크립트

CBC의 forcegreet 패키지 및 경비병 dialogue topic 조건을 교체한다.

```
현재:  GetInWorldspace(Tamriel) == 1
변경:  GetInWorldspace(Tamriel) == 1
       AND  GetInCurrentLoc(WhiterunLocation)  == 0
       AND  GetInCurrentLoc(SolitudeLocation)  == 0
       AND  GetInCurrentLoc(WindhelmLocation)  == 0
       AND  GetInCurrentLoc(MarkarthLocation)  == 0
       AND  GetInCurrentLoc(RiftenLocation)    == 0
```

즉 **"월드스페이스로 도시 내부를 판별"하던 것을 "Location으로 판별"하도록 바꾼다.** OCS가 옮기는 것은 월드스페이스이지 Location 소속이 아니므로, Location 기준은 두 환경 모두에서 의미가 보존된다.

**이 설계의 결정적 이점 — OCS를 마스터로 요구하지 않는다.**

City Location 레코드는 전부 바닐라 `Skyrim.esm` 소속이다. 따라서:

- 마스터: `Skyrim.esm` + `CityBagChecks.esp` **(OCS 불필요)**
- OCS를 안 쓰는 사용자에게도 무해 — 조건이 바닐라 동작과 동일하게 평가됨
- **OCS 버전이 올라가도 패치가 깨지지 않음** (버전 커플링 없음)
- 성격상 "OCS 패치"가 아니라 "CBC 조건 강화 패치"에 가까움

부수 이점: 스크립트 미개입 → 세이브 잔재 없음, 스크립트 부하 없음, ESL 플래그 적용 시 로드 오더 슬롯 0.

### 3.2 안 B (V4 실패 시) — 하위 Location 또는 거리 기반

도시 Location 경계가 성문 바깥까지 확장되어 안 A가 검문 자체를 억제한다면:

- **B-1**: 도시 *내부*에만 존재하는 하위 Location(각 도시의 구역 단위 child location)을 조건으로 사용. 상위 도시 Location보다 경계가 안쪽에 있음
- **B-2**: `CWMainGateExterior` 레퍼런스로부터의 거리 조건으로 대체. 도시마다 개별 레퍼런스를 지정해야 하므로 조건 수가 늘고 유지보수 비용이 높음 → B-1 실패 시에만

### 3.3 안 C (최후) — 스크립트 개입

CBC 스크립트에 가드를 추가한다.

```papyrus
Location loc = Game.GetPlayer().GetCurrentLocation()
if loc && loc.HasKeyword(LocTypeCity)
    return  ; 검문 중단
endif
```

- 장점: 키워드 기반이므로 **모드가 추가한 도시까지 포괄**
- 단점: CBC 소스 필요, 재컴파일, 세이브 베이크, CBC 업데이트마다 재작업
- **CBC 원작자의 명시적 허가 없이는 진행 불가**

### 3.4 종료 조건 보정 (안 A/B와 병행)

S3(이벤트 미종료)이 V3에서 양성인 경우:

- 종료 로직이 **조건 기반**이면 → "`LocTypeCity` 진입"을 종료 트리거로 추가. 안 A 범위 내에서 처리 가능
- 종료 로직이 **스크립트 기반**이면 → 안 C 범위로 승격. 난이도와 권한 요구가 급등하므로 별도 판단

CBC 종료 로직의 구현 방식은 현재 미확인이며, V3 수행 시 xEdit/스크립트 디컴파일로 함께 확인한다.

---

## 4. 범위

**대상** — OCS가 개방하는 5개 성벽 도시 중 CBC 검문 지점이 존재하는 곳: 화이트런, 솔리튜드, 윈드헬름, 마카스, 리프튼.

**비대상 (이 패치가 고칠 문제가 아님)**

- 보조 성문에서 검문 미발동 — CBC 원래의 설계 한계
- 패스트 트래블 직행 시 검문 우회 — CBC 원래의 설계 한계
- OCS 자체의 네비메시/지형 충돌 — 별건

---

## 5. 착수 관문

| ID | 관문 | 현황 |
|---|---|---|
| **G1** | CBC 원작자의 패치 배포 권한 확인 (Nexus permissions) | **미확인 — 최우선.** Nexus 접근이 차단되어 확인 불가. "no patches without permission"이면 배포 불가, 개인 사용 한정 |
| **G2** | V1~V4 전항 완료 | 미착수 |
| **G3** | 기준 버전 고정 — OCS 3.2.4 / CBC 1.0.4 | OCS 버전은 AFK Mods 기준이며 Nexus 최신과 다를 수 있음 |

G1이 불허로 판명되면 3장 전체가 무의미해진다. **검증(2장)보다 G1을 먼저 확인할 것.**

---

## 6. 산출물

- `CBC_OpenCities_Patch.esp` — ESL 플래그 적용
- 로드 오더: CBC 및 OCS **이후**
- 동봉 README: 검증 결과 요약, 적용 전제, 미해결 항목, 안 A가 OCS를 마스터로 요구하지 않는다는 점 명시

---

## 7. 테스트 계획

| 구분 | 시나리오 | 기대 |
|---|---|---|
| 회귀 | OCS 미설치 + CBC + 패치 | 바닐라 CBC 동작과 동일. **안 A의 무해성 증명** |
| 주 시나리오 | 5개 도시 × 성문 진입 | 검문 정상 발동 |
| 주 시나리오 | 5개 도시 × 도시 내부 배회 | 검문 미발동 |
| 주 시나리오 | 검문 1회 후 도시 진입 → 재외출 | 이벤트 정상 종료, 중복 없음 |
| 경계 | 성문 바로 앞 왕복 | 검문이 억제되지 않음 (V4 파라미터 검증) |
| 부하 | Contraband 병용, 장물 다량 소지 | 검문 처리 지연/스크립트 렉 없음 |

---

## 8. 리스크

| 리스크 | 영향 | 대응 |
|---|---|---|
| **전제 자체가 오류** (V2 음성) | 패치 불요 | 결론을 문서화하고 종료. 손실은 검증 시간뿐 |
| OCS의 Location 구조가 예상과 다름 | 안 A 무효 | 안 B로 전환 |
| V4 경계가 성문 바깥 | 안 A가 검문을 억제 | 안 B-1(하위 Location) |
| G1 권한 불허 | 배포 불가 | 개인 사용 한정 |
| CBC 업데이트로 조건 레코드 변경 | 패치 재작업 | 기준 버전 고정, 변경 시 재검증 |
| OCS가 `CWMainGateExterior`를 제거 (V1 음성) | 문제의 성격이 반전 | 설계 재수립 |

---

## 9. 미확인 사항

정직하게 기록한다. 아래는 **추정이 아니라 확인이 필요한 항목**이다.

- CBC Nexus 본문 및 배포 권한 — HTTP 403으로 접근 불가
- OCS의 `CWMainGateExterior` 레퍼런스 처리 방식
- CBC 이벤트 종료 로직의 구현 방식 (조건 기반인지 스크립트 기반인지)
- CK 조건 함수 `GetInCurrentLoc`의 정확한 시그니처 및 하위 Location 매칭 동작 — Creation Kit에서 직접 확인 요
- CBC가 검문을 거는 도시의 정확한 목록 (Readme에 미명시)
- CBC 대사가 AI 음성(Tortoise TTS / RVC)으로 생성되었다는 항목 — 본 조사 범위에서 확인되지 않음. 패치 설계에는 영향 없음

---

## 부록 — 출처

| # | 출처 |
|---|---|
| 1 | [City Bag Checks Readme (Pastebin)](https://pastebin.com/KzV8ALK4) — 트리거 로직 원문 |
| 2 | [City Bag Checks — SSE Nexus 112212](https://www.nexusmods.com/skyrimspecialedition/mods/112212) *(직접 접근 차단)* |
| 3 | [Open Cities Skyrim — SSE Nexus 87707](https://www.nexusmods.com/skyrimspecialedition/mods/87707) *(직접 접근 차단)* |
| 4 | [Open Cities Skyrim — AFK Mods (제작자 공식)](https://www.afkmods.com/index.php?/files/file/1905-open-cities-skyrim/) |
