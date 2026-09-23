import pytest

from pe_factory import make_dll, version_data
from skbuild.checker import check_game_dir, check_runtime, read_file_version
from skbuild.pe import (
    ADDRESS_LIBRARY_POST_AE, EX_NO_STRUCT_USE, MACHINE_I386, STRUCTS_POST_629, PEError, parse_bytes,
)
from skbuild.runtimes import get_runtime, pack_version

ALL = ["SKSEPlugin_Load", "SKSEPlugin_Query", "SKSEPlugin_Version"]
AL_FLAGS = ADDRESS_LIBRARY_POST_AE | STRUCTS_POST_629


def test_parse_exports_and_version_data():
    vd = version_data(name="MyPlugin", author="me", independence=AL_FLAGS,
                      compatible=[pack_version(1, 7, 104)])
    dll = parse_bytes(make_dll(ALL, vd))
    assert dll.is_x64 and dll.has_load and dll.has_query and dll.has_version
    assert dll.version_data.name == "MyPlugin"
    assert dll.version_data.author == "me"
    assert dll.version_data.uses_address_library
    assert dll.version_data.compatible_versions == [pack_version(1, 7, 104)]


def test_not_a_dll():
    with pytest.raises(PEError):
        parse_bytes(b"hello world" * 10)


def test_address_library_plugin_compatible_with_latest():
    dll = parse_bytes(make_dll(ALL, version_data(independence=AL_FLAGS)))
    rep = check_runtime(dll, get_runtime("1.7.104"))
    assert rep.compatible
    assert rep.needs_address_library
    assert any("versionlib-1-7-104-0.bin" in f.message for f in rep.findings)


def test_missing_struct_flag_rejected_post_629():
    dll = parse_bytes(make_dll(ALL, version_data(independence=ADDRESS_LIBRARY_POST_AE)))
    assert not check_runtime(dll, get_runtime("1.7.104")).compatible
    no_struct = parse_bytes(make_dll(ALL, version_data(independence=ADDRESS_LIBRARY_POST_AE,
                                                       independence_ex=EX_NO_STRUCT_USE)))
    assert check_runtime(no_struct, get_runtime("1.7.104")).compatible


def test_se_only_plugin_fails_on_ae():
    dll = parse_bytes(make_dll(["SKSEPlugin_Load", "SKSEPlugin_Query"]))
    assert not check_runtime(dll, get_runtime("1.7.104")).compatible
    assert check_runtime(dll, get_runtime("1.5.97")).compatible


def test_version_pinned_plugin():
    dll = parse_bytes(make_dll(ALL, version_data(compatible=[pack_version(1, 6, 1170)])))
    assert check_runtime(dll, get_runtime("1.6.1170")).compatible
    assert not check_runtime(dll, get_runtime("1.7.104")).compatible


def test_x86_rejected():
    dll = parse_bytes(make_dll(ALL, version_data(independence=AL_FLAGS), machine=MACHINE_I386))
    assert not check_runtime(dll, get_runtime("1.7.104")).compatible


def test_game_dir(tmp_path):
    rt = get_runtime("1.7.104")
    # VS_FIXEDFILEINFO: signature, struct version, FileVersionMS, FileVersionLS
    import struct
    exe = b"\0" * 32 + struct.pack("<IIII", 0xFEEF04BD, 0x10000, (1 << 16) | 7, (104 << 16) | 0)
    (tmp_path / "SkyrimSE.exe").write_bytes(exe)
    assert read_file_version(tmp_path / "SkyrimSE.exe") == "1.7.104.0"
    findings = check_game_dir(tmp_path, rt)
    assert [f.level for f in findings] == ["ok", "error", "error"]
    (tmp_path / "skse64_loader.exe").write_bytes(b"")
    plugins = tmp_path / "Data" / "SKSE" / "Plugins"
    plugins.mkdir(parents=True)
    (plugins / rt.address_library).write_bytes(b"")
    assert all(f.level == "ok" for f in check_game_dir(tmp_path, rt))
