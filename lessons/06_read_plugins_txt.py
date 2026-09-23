# =============================================
# 6강. 파일 읽기 — 진짜 plugins.txt 읽기
# 실행: python3 lessons/06_read_plugins_txt.py
# =============================================

# 스카이림 SE/AE 는 켜 둔 모드 목록을 plugins.txt 라는 텍스트 파일에 저장해요.
#   윈도우 위치: C:\Users\<사용자>\AppData\Local\Skyrim Special Edition\plugins.txt
#   (모드 매니저 MO2 를 쓰면 MO2 의 profiles\<프로필> 폴더 안에 있어요)
#
# 형식:
#   # 으로 시작하는 줄   → 주석
#   *CoolArmor.esp       → 켜진(활성화된) 플러그인
#   MyFirstMod.esp       → 꺼진 플러그인

from pathlib import Path   # 파일 경로를 편하게 다루는 파이썬 기본 도구

# 이 파일(__file__)이 있는 폴더의 부모 폴더 → 저장소 폴더
repo = Path(__file__).resolve().parent.parent
plugins_txt = repo / "sample_data" / "plugins.txt"     # / 로 경로 이어 붙이기

# 진짜 게임 파일을 읽어 보고 싶다면 위 줄 대신 이렇게 (r"..." 은 \ 를 그대로 쓰게 해 줘요):
# plugins_txt = Path(r"C:\Users\내이름\AppData\Local\Skyrim Special Edition\plugins.txt")

print("읽는 파일:", plugins_txt)
print("존재하나요?", plugins_txt.exists())

# --- 1. 파일 내용을 통째로 읽기 ---
text = plugins_txt.read_text(encoding="utf-8")
print("\n--- 원본 ---")
print(text)

# --- 2. 줄 단위로 나눠서 해석하기 ---
active = []
inactive = []
for line in text.splitlines():
    line = line.strip()
    if line == "" or line.startswith("#"):
        continue                         # 빈 줄/주석은 건너뛰고 다음 줄로
    if line.startswith("*"):
        active.append(line[1:])
    else:
        inactive.append(line)

print("켜진 플러그인:", active)
print("꺼진 플러그인:", inactive)

# --- 3. 파일 쓰기: 결과를 새 파일로 저장 ---
report = repo / "sample_data" / "active_list.txt"
report.write_text("\n".join(active), encoding="utf-8")   # 리스트를 줄바꿈으로 이어 붙여 저장
print(f"\n{report.name} 에 저장했어요.")

# ⚠️ 진짜 게임의 plugins.txt 는 절대 바로 덮어쓰지 마세요!
#    수정하는 연습을 할 땐 항상 복사본을 만들어서 하세요.

# ---------------------------------------------
# ✏️ 연습문제
# 1) 켜진 플러그인 중 .esm 이 몇 개인지 세어 보세요.
# 2) 파일이 없을 때(exists() 가 False) "plugins.txt 를 찾을 수 없어요"를 출력하고 끝내 보세요.
# 3) 꺼진 플러그인을 모두 켠 새 plugins_all_on.txt 를 만들어 보세요. (각 줄 앞에 * 붙이기)
# ---------------------------------------------
