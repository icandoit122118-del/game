#include "Settings.h"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <string>

namespace plugin {
    namespace {
        [[nodiscard]] std::string trim(std::string value) {
            while (!value.empty() && std::isspace(static_cast<unsigned char>(value.front()))) {
                value.erase(value.begin());
            }
            while (!value.empty() && std::isspace(static_cast<unsigned char>(value.back()))) {
                value.pop_back();
            }
            return value;
        }

        [[nodiscard]] bool parseBool(std::string_view value, bool fallback) {
            if (value == "1" || value == "true" || value == "True" || value == "TRUE") {
                return true;
            }
            if (value == "0" || value == "false" || value == "False" || value == "FALSE") {
                return false;
            }
            return fallback;
        }
    }  // namespace

    Settings& Settings::get() {
        static Settings instance;
        return instance;
    }

    std::filesystem::path Settings::iniPath() const {
        return std::filesystem::current_path() / "Data" / "SKSE" / "Plugins" /
               "WorldProjectileLimiter.ini";
    }

    void Settings::load() {
        const auto path = iniPath();
        std::ifstream in(path);
        if (!in) {
            logger::info("No INI at {}, using defaults (max={})", path.string(), max_projectiles);
            return;
        }

        std::string section;
        std::string line;
        while (std::getline(in, line)) {
            line = trim(line);
            if (line.empty() || line.starts_with(';') || line.starts_with('#')) {
                continue;
            }
            if (line.front() == '[' && line.back() == ']') {
                section = line.substr(1, line.size() - 2);
                continue;
            }
            const auto eq = line.find('=');
            if (eq == std::string::npos) {
                continue;
            }
            const auto key = trim(line.substr(0, eq));
            const auto value = trim(line.substr(eq + 1));

            if (section == "General") {
                if (key == "bEnabled") {
                    enabled = parseBool(value, enabled);
                } else if (key == "bArrowsOnly") {
                    arrows_only = parseBool(value, arrows_only);
                } else if (key == "bPreservePlayer") {
                    preserve_player = parseBool(value, preserve_player);
                } else if (key == "iMaxProjectiles") {
                    max_projectiles = static_cast<std::uint32_t>(std::max(8, std::stoi(value)));
                } else if (key == "iIntervalMs") {
                    interval_ms = static_cast<std::uint32_t>(std::max(100, std::stoi(value)));
                }
            } else if (section == "Debug" && key == "bLogCulls") {
                log_culls = parseBool(value, log_culls);
            }
        }

        logger::info(
            "Settings: enabled={} arrowsOnly={} preservePlayer={} max={} intervalMs={}",
            enabled,
            arrows_only,
            preserve_player,
            max_projectiles,
            interval_ms);
    }
}  // namespace plugin
