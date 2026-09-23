import shutil
import subprocess

import pytest

from addrlib_factory import encode, sample_pairs
from skbuild.builder import preflight
from skbuild.cli import main
from skbuild.config import load_config
from skbuild.scaffold import create_project

CXX = shutil.which("g++") or shutil.which("clang++")


@pytest.fixture
def minimal(tmp_path):
    dest = tmp_path / "Mini"
    create_project(dest, "Mini", author="me", template="minimal", resolve_baselines=False)
    return dest


def test_minimal_files(minimal):
    files = sorted(str(p.relative_to(minimal)) for p in minimal.rglob("*") if p.is_file())
    assert files == [".gitignore", "CMakeLists.txt", "CMakePresets.json", "skbuild.toml",
                     "src/AddressLibrary.h", "src/SKSE.h", "src/main.cpp"]
    text = "".join((minimal / f).read_text(encoding="utf-8") for f in files)
    assert "@@" not in text
    assert "vcpkg" not in (minimal / "CMakePresets.json").read_text()
    assert load_config(minimal).name == "Mini"


def test_minimal_does_not_need_vcpkg(minimal, monkeypatch):
    monkeypatch.delenv("VCPKG_ROOT", raising=False)
    problems = preflight(load_config(minimal))
    assert not any("VCPKG_ROOT" in p or "baseline" in p for p in problems)


def test_cli_template_option(tmp_path, capsys):
    assert main(["init", "Mini", "--path", str(tmp_path / "m"), "--template", "minimal", "--offline"]) == 0
    assert "minimal" in capsys.readouterr().out
    assert (tmp_path / "m" / "src" / "AddressLibrary.h").is_file()


def test_unknown_template(tmp_path):
    with pytest.raises(ValueError):
        create_project(tmp_path / "x", "X", template="nope", resolve_baselines=False)


DRIVER = r"""
#include "AddressLibrary.h"
#include "SKSE.h"
#include <cstdio>

static_assert(skse::MakeVersion(1, 7, 104) == 0x01070680);
static_assert(sizeof(skse::MessagingInterface::Message) == 24);

int main(int argc, char** argv) {
    addrlib::Database db;
    if (!db.Load(std::string(argv[1]))) { std::printf("ERR %s\n", db.Error().c_str()); return 1; }
    auto v = db.Version();
    std::printf("%d %d.%d.%d.%d %s %zu\n", db.Format(), v[0], v[1], v[2], v[3], db.Module().c_str(), db.Size());
    for (int i = 2; i < argc; ++i) {
        auto id = std::strtoull(argv[i], nullptr, 10);
        auto off = db.Offset(id);
        if (off) std::printf("%llu %llu\n", (unsigned long long)id, (unsigned long long)*off);
        else std::printf("%llu none\n", (unsigned long long)id);
    }
    std::printf("%s\n", addrlib::Database::FileName(1, 7, 104).c_str());
    std::printf("%s\n", addrlib::Database::FileName(1, 5, 97).c_str());
}
"""


@pytest.mark.skipif(CXX is None, reason="C++ 컴파일러 없음")
def test_address_library_loader_cpp(minimal, tmp_path):
    driver = tmp_path / "driver.cpp"
    driver.write_text(DRIVER.replace("#include <cstdio>", "#include <cstdio>\n#include <cstdlib>"))
    exe = tmp_path / "driver"
    subprocess.run([CXX, "-std=c++20", "-Wall", "-Wextra", "-Werror", "-I", str(minimal / "src"),
                    str(driver), "-o", str(exe)], check=True)

    pairs = sample_pairs()
    bin_path = tmp_path / "versionlib-1-7-104-0.bin"
    bin_path.write_bytes(encode(pairs))
    ids = [str(i) for i, _ in pairs] + ["1"]
    out = subprocess.run([str(exe), str(bin_path), *ids], capture_output=True, text=True, check=True).stdout
    lines = out.splitlines()
    assert lines[0] == f"2 1.7.104.0 SkyrimSE.exe {len(set(i for i, _ in pairs))}"
    expected = dict(pairs)
    for line in lines[1:-3]:
        id_, off = line.split()
        assert int(off) == expected[int(id_)]
    assert lines[-3] == "1 none"
    assert lines[-2:] == ["versionlib-1-7-104-0.bin", "version-1-5-97-0.bin"]

    # SE 형식(format 1)과 손상된 파일
    se = tmp_path / "version-1-5-97-0.bin"
    se.write_bytes(encode(pairs[:50], version=(1, 5, 97, 0), fmt=1))
    assert subprocess.run([str(exe), str(se)], capture_output=True, text=True).stdout.startswith("1 1.5.97.0")
    bad = tmp_path / "bad.bin"
    bad.write_bytes(encode(pairs)[:-5])
    res = subprocess.run([str(exe), str(bad)], capture_output=True, text=True)
    assert res.returncode == 1 and res.stdout.startswith("ERR")
