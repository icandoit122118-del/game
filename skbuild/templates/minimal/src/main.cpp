// 외부 라이브러리 없이 작성한 최소 SKSE 플러그인.
// SE(SKSEPlugin_Query) 와 AE/1.7(SKSEPlugin_Version) 로더를 모두 지원하고,
// 주소는 Address Library ID 로 찾는다.

#include "AddressLibrary.h"
#include "SKSE.h"

#include <windows.h>
#include <knownfolders.h>
#include <shlobj.h>

#include <filesystem>
#include <format>
#include <fstream>
#include <string_view>

namespace
{
    constexpr std::uint32_t kPluginVersion = skse::MakeVersion(PLUGIN_VERSION_MAJOR, PLUGIN_VERSION_MINOR, PLUGIN_VERSION_PATCH);

    skse::PluginHandle g_handle = 0;
    addrlib::Database g_addresses;
    std::ofstream g_log;

    void OpenLog()
    {
        PWSTR documents = nullptr;
        if (FAILED(SHGetKnownFolderPath(FOLDERID_Documents, KF_FLAG_DEFAULT, nullptr, &documents))) {
            return;
        }
        std::filesystem::path path(documents);
        CoTaskMemFree(documents);
        path /= L"My Games\\Skyrim Special Edition\\SKSE";
        std::error_code ec;
        std::filesystem::create_directories(path, ec);
        g_log.open(path / (PLUGIN_NAME ".log"), std::ios::trunc);
    }

    void Log(std::string_view a_msg)
    {
        if (g_log) {
            g_log << a_msg << std::endl;
        }
    }

    // Address Library ID -> 실행 중인 게임의 실제 주소 (없으면 0)
    [[maybe_unused]] std::uintptr_t Resolve(std::uint64_t a_id)
    {
        const auto offset = g_addresses.Offset(a_id);
        if (!offset) {
            return 0;
        }
        return reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)) + static_cast<std::uintptr_t>(*offset);
    }

    bool LoadAddressLibrary(std::uint32_t a_runtime)
    {
        const auto file = addrlib::Database::FileName(
            static_cast<int>(skse::VersionMajor(a_runtime)), static_cast<int>(skse::VersionMinor(a_runtime)),
            static_cast<int>(skse::VersionBuild(a_runtime)), static_cast<int>(skse::VersionSub(a_runtime)));
        // 게임은 설치 폴더를 작업 디렉터리로 실행된다.
        const auto path = "Data\\SKSE\\Plugins\\" + file;
        if (!g_addresses.Load(path)) {
            Log(std::format("Address Library 로드 실패 ({}): {}", path, g_addresses.Error()));
            return false;
        }
        Log(std::format("Address Library 로드: {} ({}개 항목)", file, g_addresses.Size()));
        return true;
    }

    void OnMessage(skse::MessagingInterface::Message* a_msg)
    {
        if (a_msg->type == skse::MessagingInterface::kDataLoaded) {
            Log("데이터 로드 완료");
            // 예시: const auto addr = Resolve(ID);  // ID 는 Address Library 데이터베이스에서 확인
        }
    }

    constexpr void CopyString(char* a_dst, std::size_t a_size, std::string_view a_src)
    {
        for (std::size_t i = 0; i + 1 < a_size && i < a_src.size(); ++i) {
            a_dst[i] = a_src[i];
        }
    }

    constexpr skse::PluginVersionData MakeVersionData()
    {
        skse::PluginVersionData data{};
        data.dataVersion = skse::PluginVersionData::kVersion;
        data.pluginVersion = kPluginVersion;
        CopyString(data.name, sizeof(data.name), PLUGIN_NAME);
        CopyString(data.author, sizeof(data.author), PLUGIN_AUTHOR);
        // Address Library 로 주소를 찾고 게임 구조체는 직접 쓰지 않으므로 모든 AE/1.7 런타임과 호환.
        // 게임 구조체를 직접 다루게 되면 NoStructUse 대신 StructsPost629 를 사용할 것.
        data.versionIndependence = skse::PluginVersionData::kVersionIndependent_AddressLibraryPostAE;
        data.versionIndependenceEx = skse::PluginVersionData::kVersionIndependentEx_NoStructUse;
        return data;
    }
}

extern "C" {

__declspec(dllexport) constinit skse::PluginVersionData SKSEPlugin_Version = MakeVersionData();

__declspec(dllexport) bool SKSEPlugin_Query(const skse::Interface* a_skse, skse::PluginInfo* a_info)
{
    a_info->infoVersion = skse::PluginInfo::kInfoVersion;
    a_info->name = PLUGIN_NAME;
    a_info->version = kPluginVersion;
    return a_skse->isEditor == 0;
}

__declspec(dllexport) bool SKSEPlugin_Load(const skse::Interface* a_skse)
{
    OpenLog();
    const auto rt = a_skse->runtimeVersion;
    Log(std::format("{} 로드 중 (런타임 {}.{}.{})", PLUGIN_NAME, skse::VersionMajor(rt), skse::VersionMinor(rt),
        skse::VersionBuild(rt)));

    g_handle = a_skse->GetPluginHandle();
    if (!LoadAddressLibrary(rt)) {
        return false;
    }

    auto* messaging = static_cast<skse::MessagingInterface*>(a_skse->QueryInterface(skse::kInterface_Messaging));
    if (!messaging || !messaging->RegisterListener(g_handle, "SKSE", OnMessage)) {
        Log("메시징 인터페이스 등록 실패");
        return false;
    }
    return true;
}

}
