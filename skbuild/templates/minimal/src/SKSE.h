#pragma once

// SKSE64 PluginAPI.h 에서 플러그인 로드에 필요한 최소 ABI 만 옮겨 온 정의.
// 레이아웃은 SKSE 와 정확히 같아야 하므로 static_assert 로 크기를 고정한다.

#include <cstddef>
#include <cstdint>

namespace skse
{
    using PluginHandle = std::uint32_t;

    constexpr std::uint32_t MakeVersion(std::uint32_t a_major, std::uint32_t a_minor, std::uint32_t a_build, std::uint32_t a_sub = 0)
    {
        return ((a_major & 0xFF) << 24) | ((a_minor & 0xFF) << 16) | ((a_build & 0xFFF) << 4) | (a_sub & 0xF);
    }

    constexpr std::uint32_t VersionMajor(std::uint32_t a_v) { return (a_v >> 24) & 0xFF; }
    constexpr std::uint32_t VersionMinor(std::uint32_t a_v) { return (a_v >> 16) & 0xFF; }
    constexpr std::uint32_t VersionBuild(std::uint32_t a_v) { return (a_v >> 4) & 0xFFF; }
    constexpr std::uint32_t VersionSub(std::uint32_t a_v) { return a_v & 0xF; }

    // AE(1.6+) SKSE 가 읽는 export: SKSEPlugin_Version
    struct PluginVersionData
    {
        enum : std::uint32_t
        {
            kVersion = 1,
        };

        enum : std::uint32_t
        {
            kVersionIndependent_AddressLibraryPostAE = 1 << 0,
            kVersionIndependent_Signatures = 1 << 1,
            kVersionIndependent_StructsPost629 = 1 << 2,
        };

        enum : std::uint32_t
        {
            kVersionIndependentEx_NoStructUse = 1 << 0,
        };

        std::uint32_t dataVersion;
        std::uint32_t pluginVersion;
        char name[256];
        char author[256];
        char supportEmail[252];
        std::uint32_t versionIndependenceEx;
        std::uint32_t versionIndependence;
        std::uint32_t compatibleVersions[16];
        std::uint32_t seVersionRequired;
    };
    static_assert(offsetof(PluginVersionData, versionIndependenceEx) == 772);
    static_assert(offsetof(PluginVersionData, compatibleVersions) == 780);
    static_assert(sizeof(PluginVersionData) == 848);

    // SE(1.5.97) SKSE 가 SKSEPlugin_Query 로 채우게 하는 정보
    struct PluginInfo
    {
        enum : std::uint32_t
        {
            kInfoVersion = 1,
        };

        std::uint32_t infoVersion;
        const char* name;
        std::uint32_t version;
    };

    enum InterfaceID : std::uint32_t
    {
        kInterface_Invalid = 0,
        kInterface_Scaleform,
        kInterface_Papyrus,
        kInterface_Serialization,
        kInterface_Task,
        kInterface_Messaging,
        kInterface_Object,
        kInterface_Trampoline,
    };

    struct Interface
    {
        std::uint32_t skseVersion;
        std::uint32_t runtimeVersion;
        std::uint32_t editorVersion;
        std::uint32_t isEditor;
        void* (*QueryInterface)(std::uint32_t a_id);
        PluginHandle (*GetPluginHandle)();
        std::uint32_t (*GetReleaseIndex)();
        const void* (*GetPluginInfo)(const char* a_name);
    };

    struct MessagingInterface
    {
        struct Message
        {
            const char* sender;
            std::uint32_t type;
            std::uint32_t dataLen;
            void* data;
        };

        using EventCallback = void (*)(Message* a_msg);

        enum : std::uint32_t
        {
            kPostLoad,
            kPostPostLoad,
            kPreLoadGame,
            kPostLoadGame,
            kSaveGame,
            kDeleteGame,
            kInputLoaded,
            kNewGame,
            kDataLoaded,
        };

        std::uint32_t interfaceVersion;
        bool (*RegisterListener)(PluginHandle a_listener, const char* a_sender, EventCallback a_handler);
        bool (*Dispatch)(PluginHandle a_sender, std::uint32_t a_type, void* a_data, std::uint32_t a_len, const char* a_receiver);
        void* (*GetEventDispatcher)(std::uint32_t a_id);
    };
}
