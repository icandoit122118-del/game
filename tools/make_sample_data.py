# 연습용 가짜 스카이림 플러그인(.esm/.esp/.esl)과 plugins.txt를 만드는 스크립트.
# 실제 게임 파일과 같은 형식의 "헤더(TES4 레코드)"만 들어 있어서 크기가 아주 작습니다.
# 실행 방법: python3 tools/make_sample_data.py

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "sample_data"
DATA = ROOT / "Data"

FLAG_MASTER = 0x1    # .esm 처럼 동작하는 플러그인
FLAG_LIGHT = 0x200   # .esl (라이트 플러그인)


def subrecord(kind, data):
    return kind.encode("ascii") + struct.pack("<H", len(data)) + data


def zstring(text):
    # 플러그인 파일 속 글자는 cp1252(서유럽 문자) 인코딩이라 한글은 넣을 수 없어요.
    return text.encode("cp1252") + b"\0"


def make_plugin(name, flags=0, masters=(), author="", description=""):
    body = subrecord("HEDR", struct.pack("<fII", 1.71, 0, 0x800))
    if author:
        body += subrecord("CNAM", zstring(author))
    if description:
        body += subrecord("SNAM", zstring(description))
    for master in masters:
        body += subrecord("MAST", zstring(master))
        body += subrecord("DATA", struct.pack("<Q", 0))
    # TES4 레코드 헤더: 종류, 데이터 크기, 플래그, FormID, 버전 관리 정보, 형식 버전, 알 수 없음
    header = b"TES4" + struct.pack("<IIIIHH", len(body), flags, 0, 0, 44, 0)
    (DATA / name).write_bytes(header + body)


BASE = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]

DATA.mkdir(parents=True, exist_ok=True)
make_plugin("Skyrim.esm", FLAG_MASTER, author="Bethesda")
for i, name in enumerate(BASE[1:], start=1):
    make_plugin(name, FLAG_MASTER, masters=BASE[:1] if i == 1 else BASE[:2], author="Bethesda")

make_plugin("BetterCities.esm", FLAG_MASTER, ["Skyrim.esm"], "Jarl", "Bigger cities")
make_plugin("TinyTweaks.esl", FLAG_MASTER | FLAG_LIGHT, ["Skyrim.esm"], "Nord", "Small fixes")
make_plugin("CoolArmor.esp", 0, ["Skyrim.esm", "Update.esm"], "Smith", "30 new armors")
make_plugin("CoolArmor_Patch.esp", 0, ["Skyrim.esm", "BetterCities.esm", "CoolArmor.esp"],
            "Smith", "CoolArmor + BetterCities compatibility patch")
make_plugin("OldBrokenMod.esp", 0, ["Skyrim.esm", "Missing.esm"], "Unknown", "Needs a file you do not have")
make_plugin("MyFirstMod.esp", 0, ["Skyrim.esm"], "Me", "My first mod")

(ROOT / "plugins.txt").write_text(
    "# This file is used by Skyrim to keep track of your downloaded content.\n"
    "# Please do not modify this file.\n"
    "*BetterCities.esm\n"
    "*TinyTweaks.esl\n"
    "*CoolArmor_Patch.esp\n"
    "*CoolArmor.esp\n"
    "*OldBrokenMod.esp\n"
    "MyFirstMod.esp\n"
    "*GhostMod.esp\n",
    encoding="utf-8",
)
print(f"예제 파일을 만들었습니다: {ROOT}")
