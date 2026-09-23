#include "PCH.h"

namespace
{
    void InitializeLogging()
    {
        auto path = logger::log_directory();
        if (!path) {
            SKSE::stl::report_and_fail("SKSE 로그 폴더를 찾을 수 없습니다"sv);
        }
        *path /= std::format("{}.log", SKSE::PluginDeclaration::GetSingleton()->GetName());

        auto sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(path->string(), true);
        auto log = std::make_shared<spdlog::logger>("global", std::move(sink));
        log->set_level(spdlog::level::info);
        log->flush_on(spdlog::level::info);
        spdlog::set_default_logger(std::move(log));
        spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] %v"s);
    }

    // Address Library 사용 예시: SE ID / AE ID 를 함께 주면 런타임에 맞는 주소로 해석된다.
    // REL::Relocation<std::uintptr_t> target{ REL::RelocationID(SE_ID, AE_ID) };

    void OnMessage(SKSE::MessagingInterface::Message* a_msg)
    {
        if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
            if (auto console = RE::ConsoleLog::GetSingleton()) {
                console->Print("@@NAME@@ loaded");
            }
            logger::info("데이터 로드 완료");
        }
    }
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
    InitializeLogging();
    const auto* plugin = SKSE::PluginDeclaration::GetSingleton();
    logger::info("{} v{} 로드 중 (런타임 {})", plugin->GetName(), plugin->GetVersion().string(),
        a_skse->RuntimeVersion().string());

    SKSE::Init(a_skse);
    SKSE::GetMessagingInterface()->RegisterListener(OnMessage);
    return true;
}
