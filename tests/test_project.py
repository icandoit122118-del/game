import json
import zipfile

import pytest

from pe_factory import make_dll, version_data
from skbuild.builder import build_commands, find_output, preflight
from skbuild.cli import main
from skbuild.config import load_config
from skbuild.pe import ADDRESS_LIBRARY_POST_AE, STRUCTS_POST_629
from skbuild.scaffold import create_project, slugify

GOOD_VD = version_data(name="Demo", independence=ADDRESS_LIBRARY_POST_AE | STRUCTS_POST_629)
EXPORTS = ["SKSEPlugin_Load", "SKSEPlugin_Query", "SKSEPlugin_Version"]


@pytest.fixture
def project(tmp_path):
    dest = tmp_path / "Demo"
    create_project(dest, "Demo", author='A "quoted" author', description="desc",
                   resolve_baselines=False)
    return dest


def test_scaffold(project):
    for rel in ["CMakeLists.txt", "CMakePresets.json", "vcpkg.json", "vcpkg-configuration.json",
                "skbuild.toml", ".gitignore", "src/PCH.h", "src/main.cpp"]:
        assert (project / rel).is_file(), rel
    text = "".join(p.read_text(encoding="utf-8") for p in project.rglob("*") if p.is_file())
    assert "@@" not in text
    json.loads((project / "CMakePresets.json").read_text())
    assert json.loads((project / "vcpkg.json").read_text())["name"] == "demo"
    cfg = load_config(project)
    assert cfg.name == "Demo" and cfg.author == 'A "quoted" author'
    assert cfg.runtimes == ["1.7.104"]


def test_scaffold_rejects_bad_name(tmp_path):
    with pytest.raises(ValueError):
        create_project(tmp_path / "x", "Bad Name", resolve_baselines=False)


def test_scaffold_refuses_nonempty(project):
    with pytest.raises(FileExistsError):
        create_project(project, "Demo", resolve_baselines=False)


def test_slugify():
    assert slugify("MyCoolPlugin") == "my-cool-plugin"


def test_build_dry_run_and_preflight(project, capsys):
    cfg = load_config(project)
    assert build_commands(cfg) == [["cmake", "--preset", "release"], ["cmake", "--build", "--preset", "release"]]
    assert any("baseline" in p for p in preflight(cfg))
    assert main(["build", "--project", str(project), "--dry-run"]) == 0
    assert "cmake --build --preset release" in capsys.readouterr().out


def _fake_build(project, vd=GOOD_VD, exports=EXPORTS):
    out = project / "build" / "release"
    out.mkdir(parents=True)
    (out / "Demo.dll").write_bytes(make_dll(exports, vd))
    (out / "Demo.pdb").write_bytes(b"pdb")
    return out / "Demo.dll"


def test_package_plain(project, tmp_path):
    (project / "Demo.esp").write_bytes(b"TES4")
    toml = (project / "skbuild.toml").read_text()
    toml = toml.replace('# "data/Demo.esp" = "Demo.esp"', '"Demo.esp" = "Demo.esp"')
    (project / "skbuild.toml").write_text(toml)
    dll = _fake_build(project)
    assert find_output(load_config(project)) == dll
    out = tmp_path / "dist"
    assert main(["package", "--project", str(project), "-o", str(out)]) == 0
    with zipfile.ZipFile(out / "Demo-1.0.0.zip") as zf:
        assert sorted(zf.namelist()) == ["Demo.esp", "SKSE/Plugins/Demo.dll"]


def test_package_fomod(project, tmp_path):
    _fake_build(project)
    out = tmp_path / "dist"
    assert main(["package", "--project", str(project), "-o", str(out), "--fomod"]) == 0
    with zipfile.ZipFile(out / "Demo-1.0.0.zip") as zf:
        names = set(zf.namelist())
        assert {"Data/SKSE/Plugins/Demo.dll", "fomod/info.xml", "fomod/ModuleConfig.xml"} <= names
        assert b"Demo" in zf.read("fomod/info.xml")


def test_package_blocks_incompatible(project, tmp_path):
    _fake_build(project, vd=None, exports=["SKSEPlugin_Load", "SKSEPlugin_Query"])
    out = tmp_path / "dist"
    assert main(["package", "--project", str(project), "-o", str(out)]) == 1
    assert not (out / "Demo-1.0.0.zip").exists()
    assert main(["package", "--project", str(project), "-o", str(out), "--force"]) == 0


def test_check_cli(tmp_path, capsys):
    dll = tmp_path / "X.dll"
    dll.write_bytes(make_dll(EXPORTS, GOOD_VD))
    assert main(["check", str(dll)]) == 0
    out = capsys.readouterr().out
    assert "1.7.104" in out and "호환" in out
    assert main(["check", str(dll), "--game-dir", str(tmp_path)]) == 1


def test_runtimes_cli(capsys):
    assert main(["runtimes"]) == 0
    assert "* 1.7.104" in capsys.readouterr().out
