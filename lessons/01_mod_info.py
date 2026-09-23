# =============================================
# 1강. 출력(print)과 변수 — 모드 정보 카드 만들기
# 실행: python3 lessons/01_mod_info.py
# =============================================

# '#' 뒤는 "주석". 컴퓨터는 무시하고 사람만 읽어요.

# --- 1. 변수: 값에 이름표를 붙여 담아 두는 상자 ---
mod_name = "CoolArmor"      # 문자열(str): 따옴표로 감싼 글자
author = "Smith"
version = 1.2               # 실수(float): 소수점 있는 숫자
armor_count = 30            # 정수(int)
requires_skse = False       # 불리언(bool): True(참) / False(거짓)

# --- 2. print: 화면에 출력 ---
print("모드 이름:", mod_name)
print("제작자:", author)

# --- 3. f-string: 문장 안에 변수 끼워 넣기 (따옴표 앞에 f) ---
print(f"{mod_name} v{version} by {author}")
print(f"새 갑옷 {armor_count}종 추가 / SKSE 필요: {requires_skse}")

# --- 4. 계산하기 ---
file_size_bytes = 5_242_880            # 숫자 사이의 _ 는 읽기 쉽게 하는 구분자
file_size_mb = file_size_bytes / 1024 / 1024
print(f"파일 크기: {file_size_mb} MB")

# 스카이림 일반 플러그인은 최대 254개까지 켤 수 있어요.
max_plugins = 254
my_plugins = 180
print(f"앞으로 {max_plugins - my_plugins}개 더 설치할 수 있어요.")

# 게임 콘솔에서는 로드 순서를 16진수로 보여 줘요 (10 → 0A, 255 → FF)
print(f"로드 순서 10번은 16진수로 {10:02X}")

# ---------------------------------------------
# ✏️ 연습문제
# 1) 내가 좋아하는 모드(또는 만들고 싶은 모드)의 이름, 제작자, 버전을 변수에 담아 출력해 보세요.
# 2) 모드 50개가 각각 평균 120MB라면 총 몇 GB인지 계산해 보세요. (1GB = 1024MB)
# 3) 로드 순서 5, 16, 253 을 16진수로 출력해 보세요.
# ---------------------------------------------
