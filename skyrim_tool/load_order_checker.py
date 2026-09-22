# =============================================
# 스카이림 로드 오더 검사기 (Skyrim Load Order Checker)
#
# plugins.txt 와 Data 폴더의 플러그인 헤더를 읽어서
#   - 활성화됐지만 Data 폴더에 없는 플러그인
#   - 필요한 마스터 파일이 없는 플러그인 (게임이 켜지자마자 튕기는 주원인!)
#   - 마스터보다 먼저 로드되는 플러그인
#   - 일반 플러그인 개수 제한(254개) 초과
# 를 찾아 알려 줍니다.
#
# 사용법:
#   python3 skyrim_tool/load_order_checker.py                       (예제 데이터로 실행)
#   python3 skyrim_tool/load_order_checker.py <plugins.txt> <Data 폴더>
# =============================================

import struct
import sys
from pathlib import Path

# 게임이 plugins.txt 와 상관없이 항상 제일 먼저 불러오는 기본 파일들
BASE_PLUGINS = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
FLAG_MASTER = 0x1
FLAG_LIGHT = 0x200
MAX_FULL_PLUGINS = 254  # 00 ~ FD (FE는 라이트 플러그인, FF는 게임 실행 중 생성 오브젝트용)


def read_plugin_header(path):
    """플러그인 파일의 맨 앞(TES4 레코드)을 읽어 마스터 목록과 플래그를 돌려줍니다."""
    with open(path, "rb") as f:
        header = f.read(24)
        if len(header) < 24 or header[:4] != b"TES4":
            raise ValueError(f"{path.name}: 스카이림 플러그인 파일이 아닙니다")
        data_size, flags = struct.unpack("<II", header[4:12])
        data = f.read(data_size)

    info = {"flags": flags, "masters": [], "author": "", "description": ""}
    pos = 0
    big_size = None  # XXXX 서브레코드: 다음 서브레코드 크기가 65535를 넘을 때 사용
    while pos + 6 <= len(data):
        kind = data[pos:pos + 4]
        size = struct.unpack("<H", data[pos + 4:pos + 6])[0]
        pos += 6
        if kind == b"XXXX":
            big_size = struct.unpack("<I", data[pos:pos + 4])[0]
            pos += size
            continue
        if big_size is not None:
            size, big_size = big_size, None
        value = data[pos:pos + size].rstrip(b"\0").decode("cp1252", errors="replace")
        pos += size

        if kind == b"MAST":
            info["masters"].append(value)
        elif kind == b"CNAM":
            info["author"] = value
        elif kind == b"SNAM":
            info["description"] = value
    return info


def is_light(name, flags):
    return name.lower().endswith(".esl") or bool(flags & FLAG_LIGHT)


def is_master(name, flags):
    return name.lower().endswith((".esm", ".esl")) or bool(flags & FLAG_MASTER)


def read_plugins_txt(path):
    """plugins.txt 를 읽어 (이름, 활성화 여부) 목록을 돌려줍니다."""
    plugins = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        active = line.startswith("*")
        plugins.append((line.lstrip("*"), active))
    return plugins


def find_file(data_dir, name):
    """윈도우처럼 대소문자를 무시하고 Data 폴더에서 파일을 찾습니다."""
    exact = data_dir / name
    if exact.exists():
        return exact
    for candidate in data_dir.iterdir():
        if candidate.name.lower() == name.lower():
            return candidate
    return None


def check(plugins_txt, data_dir):
    data_dir = Path(data_dir)
    errors, warnings = [], []

    # 1) 실제 로드 순서 만들기: 기본 파일 + plugins.txt 에서 활성화된 것
    listed = read_plugins_txt(plugins_txt)
    load_order = [name for name in BASE_PLUGINS if find_file(data_dir, name)]
    base_lower = [name.lower() for name in BASE_PLUGINS]
    load_order += [name for name, active in listed if active and name.lower() not in base_lower]

    # 2) 각 플러그인 헤더 읽기
    headers = {}
    for name in load_order:
        path = find_file(data_dir, name)
        if path is None:
            errors.append(f"{name}: 활성화돼 있지만 Data 폴더에 파일이 없습니다")
            continue
        try:
            headers[name] = read_plugin_header(path)
        except ValueError as e:
            errors.append(str(e))

    # 게임은 마스터(.esm/.esl, ESM 플래그) 파일을 항상 일반 .esp 보다 먼저 불러옵니다
    loaded = [name for name in load_order if name in headers]
    loaded.sort(key=lambda name: not is_master(name, headers[name]["flags"]))  # 안정 정렬: 순서 유지

    # 3) 마스터 검사
    position = {name.lower(): i for i, name in enumerate(loaded)}
    for i, name in enumerate(loaded):
        for master in headers[name]["masters"]:
            master_pos = position.get(master.lower())
            if master_pos is None:
                errors.append(f"{name}: 필요한 마스터 '{master}' 가 없거나 비활성화돼 있습니다")
            elif master_pos > i:
                errors.append(f"{name}: 마스터 '{master}' 보다 먼저 로드됩니다 (순서를 뒤로 옮기세요)")

    # 4) 로드 오더 번호 매기기 (게임 안 콘솔에서 보이는 FormID 앞자리)
    rows = []
    full_count = light_count = 0
    for name in loaded:
        if is_light(name, headers[name]["flags"]):
            rows.append((f"FE:{light_count:03X}", name))
            light_count += 1
        else:
            rows.append((f"{full_count:02X}", name))
            full_count += 1

    if full_count > MAX_FULL_PLUGINS:
        errors.append(f"일반 플러그인이 {full_count}개입니다. 최대 {MAX_FULL_PLUGINS}개까지만 가능합니다")
    elif full_count > MAX_FULL_PLUGINS - 10:
        warnings.append(f"일반 플러그인이 {full_count}개로 한도({MAX_FULL_PLUGINS})에 가깝습니다")

    inactive = [name for name, active in listed if not active]
    return rows, errors, warnings, inactive


def main():
    if len(sys.argv) == 3:
        plugins_txt, data_dir = sys.argv[1], sys.argv[2]
    else:
        sample = Path(__file__).resolve().parent.parent / "sample_data"
        plugins_txt, data_dir = sample / "plugins.txt", sample / "Data"
        print(f"(예제 데이터로 실행합니다: {sample})\n")

    rows, errors, warnings, inactive = check(plugins_txt, data_dir)

    print("=== 로드 오더 ===")
    for index, name in rows:
        print(f"  [{index:>6}] {name}")
    if inactive:
        print(f"\n비활성화된 플러그인 {len(inactive)}개: {', '.join(inactive)}")

    print()
    for message in errors:
        print(f"[오류] {message}")
    for message in warnings:
        print(f"[경고] {message}")
    if not errors and not warnings:
        print("[OK] 문제를 찾지 못했습니다. 즐거운 모험 되세요!")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
