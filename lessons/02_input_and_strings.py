# =============================================
# 2강. 입력(input)과 문자열 다루기 — 플러그인 파일 이름 분석
# 실행: python3 lessons/02_input_and_strings.py
# =============================================

# --- 1. input: 키보드로 입력 받기 (결과는 항상 문자열!) ---
filename = input("플러그인 파일 이름을 입력하세요 (예: CoolArmor.esp): ")

# --- 2. 문자열 메서드: 문자열 뒤에 .을 찍고 쓰는 기능들 ---
print("소문자로:", filename.lower())      # 윈도우는 대소문자를 구분하지 않아서 비교할 때 유용
print("대문자로:", filename.upper())
print("앞뒤 공백 제거:", filename.strip())
print("글자 수:", len(filename))

# --- 3. 자르기(슬라이싱): 문자열[시작:끝] ---
extension = filename[-4:]       # 뒤에서 4글자 → ".esp"
name_only = filename[:-4]       # 뒤 4글자를 뺀 나머지 → "CoolArmor"
print(f"이름: {name_only} / 확장자: {extension}")

# --- 4. 문자열 확인 ---
print("'.esp'로 끝나나요?", filename.lower().endswith(".esp"))
print("'Patch'가 들어있나요?", "patch" in filename.lower())

# --- 5. 숫자로 바꾸기 ---
# plugins.txt 속 활성화 표시는 맨 앞의 '*' 한 글자예요.
line = "*CoolArmor.esp"
print("활성화?", line[0] == "*", "/ 파일 이름:", line[1:])

count_text = input("설치한 모드 개수는? ")
count = int(count_text)        # 문자열 "180" → 숫자 180
print(f"한도까지 {254 - count}개 남았어요.")

# ---------------------------------------------
# ✏️ 연습문제
# 1) 입력받은 파일 이름에서 확장자만 소문자로 출력해 보세요.
# 2) "  *SkyUI_SE.esp  " 처럼 앞뒤 공백이 있는 줄에서 파일 이름만 꺼내 보세요. (strip, 슬라이싱)
# 3) int("abc") 를 실행하면 무슨 일이 생기는지 확인하고, 에러 메시지를 읽어 보세요.
# ---------------------------------------------
