# =============================================
# 8강. 바이너리 파일 읽기 — .esp 파일 안의 마스터 목록 꺼내기
# 실행: python3 lessons/08_read_esp_header.py
# =============================================

# .esp/.esm 파일은 텍스트가 아니라 "바이너리(바이트 덩어리)" 파일이에요.
# 맨 앞에는 항상 TES4 라는 "헤더 레코드"가 있고, 그 안에 제작자·설명·마스터 목록이 들어 있어요.
#
#  [TES4 헤더 24바이트]
#   "TES4" (4) | 데이터 크기 (4) | 플래그 (4) | FormID (4) | 버전 관리 (4) | 형식 버전 (2) | ? (2)
#  [서브레코드들] — 각각: 종류 이름 (4) | 크기 (2) | 데이터 (크기만큼)
#   HEDR = 헤더 정보, CNAM = 제작자, SNAM = 설명, MAST = 마스터 파일 이름, DATA = (MAST 뒤 따라오는 값)
#
# 이것이 xEdit, 모드 매니저 같은 실제 모딩 툴이 하는 일의 첫 단계예요!

import struct               # 바이트 ↔ 숫자 변환 도구
from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent / "sample_data" / "Data"
path = data_dir / "CoolArmor_Patch.esp"

# --- 1. 바이트 그대로 보기 ("rb" = read binary) ---
with open(path, "rb") as f:     # with 블록이 끝나면 파일이 자동으로 닫혀요
    raw = f.read()
print("앞부분 32바이트:", raw[:32])

# --- 2. 헤더 해석 ---
record_type = raw[0:4]                                   # b'TES4'
# "<II" = 리틀 엔디언(<) 부호 없는 4바이트 정수(I) 2개
data_size, flags = struct.unpack("<II", raw[4:12])
print(f"레코드 종류: {record_type}, 데이터 크기: {data_size}, 플래그: {flags:#x}")

# 플래그의 비트 확인 (& = 비트 AND)
print("ESM 플래그?", bool(flags & 0x1))
print("ESL 플래그?", bool(flags & 0x200))

# --- 3. 서브레코드를 하나씩 읽기 ---
data = raw[24:24 + data_size]
pos = 0
found_masters = []
while pos < len(data):
    kind = data[pos:pos + 4].decode("ascii")
    size = struct.unpack("<H", data[pos + 4:pos + 6])[0]   # H = 2바이트 정수
    value = data[pos + 6:pos + 6 + size]
    pos += 6 + size                                        # 다음 서브레코드로 이동

    if kind == "MAST":
        # 문자열 끝의 \0 (널 문자)을 떼고 글자로 바꾸기
        found_masters.append(value.rstrip(b"\0").decode("cp1252"))
    elif kind == "CNAM":
        print("제작자:", value.rstrip(b"\0").decode("cp1252"))
    elif kind == "SNAM":
        print("설명:", value.rstrip(b"\0").decode("cp1252"))

print("마스터:", found_masters)

# ---------------------------------------------
# ✏️ 연습문제
# 1) path 를 다른 파일(TinyTweaks.esl, OldBrokenMod.esp)로 바꿔서 실행해 보세요.
# 2) 위 코드를 read_masters(path) 함수로 만들고, Data 폴더의 모든 파일에 대해 실행해 보세요.
#    (힌트: for p in data_dir.iterdir(): )
# 3) 다 만들었다면 skyrim_tool/load_order_checker.py 를 열어 보세요.
#    1~8강에서 배운 것들이 어떻게 합쳐졌는지 찾아볼 수 있어요!
# ---------------------------------------------
