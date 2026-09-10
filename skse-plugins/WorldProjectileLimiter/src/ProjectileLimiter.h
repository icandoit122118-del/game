#pragma once

#include <atomic>
#include <thread>

namespace plugin {
    class ProjectileLimiter {
        public:
            static void start();
            static void stop();
            static void enforce();

        private:
            static void worker();
            static inline std::atomic_bool running{false};
            static inline std::thread workerThread;
    };
}  // namespace plugin
