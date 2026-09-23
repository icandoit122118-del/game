#pragma once

// Address Library for SKSE Plugins 데이터베이스(.bin) 로더.
//  - SE : Data/SKSE/Plugins/version-1-5-97-0.bin      (format 1)
//  - AE : Data/SKSE/Plugins/versionlib-1-7-104-0.bin  (format 2)
// 파일은 (ID, 게임 모듈 기준 오프셋) 쌍을 델타 압축해 저장한다.
// 이 헤더는 표준 라이브러리만 사용하므로 게임 밖에서도 테스트할 수 있다.

#include <array>
#include <cstdint>
#include <fstream>
#include <istream>
#include <optional>
#include <string>
#include <unordered_map>

namespace addrlib
{
    class Database
    {
    public:
        bool Load(std::istream& a_in)
        {
            _offsets.clear();
            _error.clear();

            const auto format = Read<std::int32_t>(a_in);
            if (format != 1 && format != 2) {
                return Fail("지원하지 않는 형식: " + std::to_string(format));
            }
            _format = format;
            for (auto& part : _version) {
                part = Read<std::int32_t>(a_in);
            }
            const auto nameLen = Read<std::int32_t>(a_in);
            if (nameLen < 0 || nameLen > 0x10000) {
                return Fail("모듈 이름 길이가 잘못되었습니다");
            }
            _module.resize(static_cast<std::size_t>(nameLen));
            a_in.read(_module.data(), nameLen);

            const auto ptrSize = static_cast<std::uint64_t>(Read<std::int32_t>(a_in));
            const auto count = Read<std::int32_t>(a_in);
            if (!a_in || ptrSize == 0 || count < 0) {
                return Fail("헤더가 손상되었습니다");
            }
            _offsets.reserve(static_cast<std::size_t>(count));

            std::uint64_t prevId = 0;
            std::uint64_t prevOffset = 0;
            for (std::int32_t i = 0; i < count; ++i) {
                const auto type = Read<std::uint8_t>(a_in);
                const auto low = type & 0xF;
                const auto high = type >> 4;

                std::uint64_t id = 0;
                switch (low) {
                case 0: id = Read<std::uint64_t>(a_in); break;
                case 1: id = prevId + 1; break;
                case 2: id = prevId + Read<std::uint8_t>(a_in); break;
                case 3: id = prevId - Read<std::uint8_t>(a_in); break;
                case 4: id = prevId + Read<std::uint16_t>(a_in); break;
                case 5: id = prevId - Read<std::uint16_t>(a_in); break;
                case 6: id = Read<std::uint16_t>(a_in); break;
                case 7: id = Read<std::uint32_t>(a_in); break;
                default: return Fail("ID 인코딩이 잘못되었습니다");
                }

                const bool scaled = (high & 8) != 0;
                const std::uint64_t base = scaled ? prevOffset / ptrSize : prevOffset;
                std::uint64_t offset = 0;
                switch (high & 7) {
                case 0: offset = Read<std::uint64_t>(a_in); break;
                case 1: offset = base + 1; break;
                case 2: offset = base + Read<std::uint8_t>(a_in); break;
                case 3: offset = base - Read<std::uint8_t>(a_in); break;
                case 4: offset = base + Read<std::uint16_t>(a_in); break;
                case 5: offset = base - Read<std::uint16_t>(a_in); break;
                case 6: offset = Read<std::uint16_t>(a_in); break;
                case 7: offset = Read<std::uint32_t>(a_in); break;
                }
                if (scaled) {
                    offset *= ptrSize;
                }
                if (!a_in) {
                    return Fail("데이터가 잘렸습니다");
                }
                _offsets[id] = offset;
                prevId = id;
                prevOffset = offset;
            }
            return true;
        }

        bool Load(const std::string& a_path)
        {
            std::ifstream file(a_path, std::ios::binary);
            if (!file) {
                return Fail("파일을 열 수 없습니다: " + a_path);
            }
            return Load(file);
        }

        // ID -> 게임 모듈 기준 오프셋 (없으면 nullopt). 실제 주소는 모듈 base + 오프셋.
        [[nodiscard]] std::optional<std::uint64_t> Offset(std::uint64_t a_id) const
        {
            const auto it = _offsets.find(a_id);
            return it != _offsets.end() ? std::optional(it->second) : std::nullopt;
        }

        [[nodiscard]] std::size_t Size() const { return _offsets.size(); }
        [[nodiscard]] int Format() const { return _format; }
        [[nodiscard]] const std::array<std::int32_t, 4>& Version() const { return _version; }
        [[nodiscard]] const std::string& Module() const { return _module; }
        [[nodiscard]] const std::string& Error() const { return _error; }

        // 런타임 버전에 맞는 파일 이름 (예: 1.7.104 -> versionlib-1-7-104-0.bin)
        static std::string FileName(int a_major, int a_minor, int a_build, int a_sub = 0)
        {
            const bool ae = a_major > 1 || (a_major == 1 && a_minor >= 6);
            return std::string(ae ? "versionlib-" : "version-") + std::to_string(a_major) + "-" +
                   std::to_string(a_minor) + "-" + std::to_string(a_build) + "-" + std::to_string(a_sub) + ".bin";
        }

    private:
        template <class T>
        static T Read(std::istream& a_in)
        {
            T value{};
            a_in.read(reinterpret_cast<char*>(&value), sizeof(T));
            return value;
        }

        bool Fail(std::string a_msg)
        {
            _error = std::move(a_msg);
            _offsets.clear();
            return false;
        }

        std::unordered_map<std::uint64_t, std::uint64_t> _offsets;
        std::array<std::int32_t, 4> _version{};
        std::string _module;
        std::string _error;
        int _format = 0;
    };
}
