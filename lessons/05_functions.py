# =============================================
# 5강. 함수(def) — 자주 쓰는 기능에 이름 붙이기
# 실행: python3 lessons/05_functions.py
# =============================================

# 3~4강에서 만든 코드를 "함수"로 묶으면, 필요할 때마다 이름만 불러서 쓸 수 있어요.

# --- 1. 매개변수를 받고 결과를 return 하는 함수 ---
def plugin_type(filename):
    """파일 이름을 보고 'master' / 'light' / 'plugin' / None 중 하나를 돌려줍니다."""
    ext = filename.lower()[-4:]
    if ext == ".esm":
        return "master"
    elif ext == ".esl":
        return "light"
    elif ext == ".esp":
        return "plugin"
    return None      # 플러그인이 아님


print(plugin_type("Skyrim.esm"))      # master
print(plugin_type("TinyTweaks.ESL"))  # light
print(plugin_type("readme.txt"))      # None

# --- 2. plugins.txt 한 줄을 해석하는 함수 (결과를 2개 돌려주기) ---
def parse_line(line):
    """'*CoolArmor.esp' → ('CoolArmor.esp', True)"""
    line = line.strip()
    active = line.startswith("*")
    return line.lstrip("*"), active


name, active = parse_line("*CoolArmor.esp")
print(name, active)

# --- 3. 함수 안에서 다른 함수 쓰기 ---
def print_load_order(plugins):
    full = 0     # 일반 플러그인 번호
    light = 0    # 라이트 플러그인 번호 (FE:000 부터 따로 매겨져요)
    for plugin in plugins:
        if plugin_type(plugin) == "light":
            print(f"[FE:{light:03X}] {plugin}")
            light += 1   # light = light + 1 의 줄임
        else:
            print(f"[    {full:02X}] {plugin}")
            full += 1


print_load_order(["Skyrim.esm", "Update.esm", "TinyTweaks.esl", "CoolArmor.esp"])

# ---------------------------------------------
# ✏️ 연습문제
# 1) 플러그인 리스트를 받아 .esp 개수를 돌려주는 함수 count_esp(plugins) 를 만들어 보세요.
# 2) 파일 이름을 받아 "패치 모드"인지 True/False 로 돌려주는 is_patch(filename) 를 만들어 보세요.
# 3) 두 이름을 대소문자 무시하고 비교하는 same_name(a, b) 를 만들어 보세요.
#    same_name("skyrim.ESM", "Skyrim.esm") → True
# ---------------------------------------------
