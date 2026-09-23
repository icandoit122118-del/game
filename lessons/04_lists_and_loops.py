# =============================================
# 4강. 리스트와 반복문 — 로드 오더 출력하기
# 실행: python3 lessons/04_lists_and_loops.py
# =============================================

# --- 1. 리스트: 여러 값을 순서대로 담기 ---
load_order = ["Skyrim.esm", "Update.esm", "BetterCities.esm", "CoolArmor.esp"]
print(load_order[0])     # 인덱스는 0부터! → Skyrim.esm
print(load_order[-1])    # 맨 마지막 → CoolArmor.esp
print("개수:", len(load_order))

# --- 2. 추가 / 끼워 넣기 / 삭제 ---
load_order.append("CoolArmor_Patch.esp")         # 맨 뒤에 추가
load_order.insert(2, "Dawnguard.esm")            # 2번 자리에 끼워 넣기
load_order.remove("Update.esm")                  # 값으로 삭제
print(load_order)

# --- 3. for 반복: 리스트를 하나씩 꺼내기 ---
for plugin in load_order:
    print(" -", plugin)

# --- 4. enumerate: 번호도 같이 받기 → 게임 콘솔처럼 16진수 로드 번호 출력 ---
print("\n=== 로드 오더 ===")
for index, plugin in enumerate(load_order):
    print(f"[{index:02X}] {plugin}")

# --- 5. 반복 + 조건: 원하는 것만 골라내기 ---
esp_count = 0
for plugin in load_order:
    if plugin.lower().endswith(".esp"):
        esp_count = esp_count + 1
print(f"\n.esp 파일 {esp_count}개")

# --- 6. in: 들어 있는지 확인 ---
if "Dawnguard.esm" in load_order:
    print("던가드 DLC가 켜져 있어요.")

# --- 7. while: 조건이 참인 동안 반복 ---
while True:
    name = input("\n추가할 플러그인 이름 (그만하려면 엔터): ").strip()
    if name == "":
        break                      # 반복 탈출
    load_order.append(name)
    print(f"{name} 추가! 현재 {len(load_order)}개")

print(load_order)

# ---------------------------------------------
# ✏️ 연습문제
# 1) .esm 파일만 골라 새 리스트에 담아 출력해 보세요.
# 2) 이름에 "Patch" 가 들어간 플러그인만 출력해 보세요.
# 3) load_order 에서 "CoolArmor.esp" 가 몇 번째인지 찾아 보세요. (힌트: load_order.index(...))
# ---------------------------------------------
