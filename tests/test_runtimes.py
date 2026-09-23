from skbuild.runtimes import all_runtimes, default_version, get_runtime, pack_version, unpack_version


def test_default_is_latest():
    assert default_version() == "1.7.104"
    assert get_runtime().address_library == "versionlib-1-7-104-0.bin"


def test_pack_roundtrip():
    assert unpack_version(pack_version(1, 7, 104)) == "1.7.104"
    assert unpack_version(pack_version(1, 6, 1170)) == "1.6.1170"


def test_unknown_runtime_is_inferred():
    assert get_runtime("1.7.200").address_library == "versionlib-1-7-200-0.bin"
    assert get_runtime("1.5.80").address_library == "version-1-5-80-0.bin"


def test_editions():
    by_ver = {r.version: r for r in all_runtimes()}
    assert by_ver["1.7.104"].post_629 and by_ver["1.7.104"].is_ae
    assert not by_ver["1.5.97"].is_ae
