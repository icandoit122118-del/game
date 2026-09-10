#pragma once

#include <cstdint>
#include <filesystem>

namespace plugin {
    struct Settings {
        bool enabled{true};
        bool arrows_only{true};
        bool preserve_player{true};
        std::uint32_t max_projectiles{200};
        std::uint32_t interval_ms{1000};
        bool log_culls{false};

        static Settings& get();
        void load();
        [[nodiscard]] std::filesystem::path iniPath() const;
    };
}  // namespace plugin
