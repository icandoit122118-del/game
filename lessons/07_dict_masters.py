# =============================================
# 7강. 딕셔너리(dict) — 마스터 파일 검사
# 실행: python3 lessons/07_dict_masters.py
# =============================================

# "마스터"란 어떤 모드가 동작하려면 꼭 있어야 하는 다른 플러그인이에요.
# 예) CoolArmor_Patch.esp 는 CoolArmor.esp 가 있어야 동작
#   - 마스터가 아예 없으면      → 게임이 시작하자마자 튕김 (CTD)
#   - 마스터보다 먼저 로드되면  → 문제 발생 가능

# --- 1. 딕셔너리: "키 → 값" 짝을 저장 (사전에서 단어로 뜻을 찾듯이) ---
mod = {"name": "CoolArmor", "author": "Smith", "version": 1.2}
print(mod["name"], mod["author"])
mod["version"] = 1.3                  # 값 바꾸기
mod["nexus_id"] = 12345               # 새 키 추가
print(mod)

# --- 2. 플러그인 → 마스터 목록 (8강에서는 이걸 파일에서 직접 읽어요!) ---
masters = {
    "Skyrim.esm": [],
    "Update.esm": ["Skyrim.esm"],
    "BetterCities.esm": ["Skyrim.esm"],
    "CoolArmor_Patch.esp": ["Skyrim.esm", "BetterCities.esm", "CoolArmor.esp"],
    "CoolArmor.esp": ["Skyrim.esm", "Update.esm"],
    "OldBrokenMod.esp": ["Skyrim.esm", "Missing.esm"],
}
load_order = list(masters)   # 딕셔너리의 키들을 리스트로 (넣은 순서 유지)

# --- 3. 이름 → 로드 위치 딕셔너리 만들기 ---
position = {}
for index, name in enumerate(load_order):
    position[name.lower()] = index         # 대소문자 무시하려고 소문자로 저장
print(position)

# --- 4. 검사! ---
problems = 0
for index, plugin in enumerate(load_order):
    for master in masters[plugin]:          # 반복 안에 반복 (중첩 반복)
        if master.lower() not in position:
            print(f"[오류] {plugin}: 마스터 {master} 가 없어요!")
            problems += 1
        elif position[master.lower()] > index:
            print(f"[오류] {plugin}: 마스터 {master} 보다 먼저 로드돼요!")
            problems += 1

print(f"\n문제 {problems}개 발견" if problems else "\n문제 없음!")

# ---------------------------------------------
# ✏️ 연습문제
# 1) load_order 에서 CoolArmor.esp 와 CoolArmor_Patch.esp 순서를 바꿔서 오류가 사라지는지 확인해 보세요.
#    (힌트: 딕셔너리에 넣는 순서를 바꾸면 돼요)
# 2) 각 플러그인이 "다른 플러그인의 마스터로 몇 번 쓰이는지" 세는 딕셔너리를 만들어 보세요.
#    Skyrim.esm 이 제일 많겠죠?
# 3) 어떤 플러그인도 마스터로 쓰지 않는 플러그인 목록을 출력해 보세요.
# ---------------------------------------------
