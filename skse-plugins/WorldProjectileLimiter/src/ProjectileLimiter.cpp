#include "ProjectileLimiter.h"
#include "Settings.h"

#include <vector>

namespace plugin {
    namespace {
        [[nodiscard]] bool isArrowLike(RE::Projectile* projectile) {
            if (!projectile) {
                return false;
            }
            auto& data = projectile->GetProjectileRuntimeData();
            if (data.ammoSource) {
                return true;
            }
            if (const auto* base = projectile->GetProjectileBase()) {
                return base->IsArrow() || base->IsMissile();
            }
            return false;
        }

        [[nodiscard]] bool isPlayerOwned(RE::Projectile* projectile) {
            if (!projectile) {
                return false;
            }
            auto& data = projectile->GetProjectileRuntimeData();
            if (const auto shooter = data.shooter.get()) {
                return shooter->IsPlayerRef();
            }
            return false;
        }

        void collect(RE::BSTArray<RE::ProjectileHandle>& handles, std::vector<RE::Projectile*>& out) {
            for (auto& handle : handles) {
                if (auto ptr = handle.get()) {
                    out.push_back(ptr.get());
                }
            }
        }
    }  // namespace

    void ProjectileLimiter::start() {
        if (running.exchange(true)) {
            return;
        }
        workerThread = std::thread(&ProjectileLimiter::worker);
        logger::info("Projectile limiter worker started");
    }

    void ProjectileLimiter::stop() {
        if (!running.exchange(false)) {
            return;
        }
        if (workerThread.joinable()) {
            workerThread.join();
        }
        logger::info("Projectile limiter worker stopped");
    }

    void ProjectileLimiter::worker() {
        while (running.load()) {
            const auto interval = Settings::get().interval_ms;
            std::this_thread::sleep_for(std::chrono::milliseconds(interval));
            if (!running.load()) {
                break;
            }
            if (auto* tasks = SKSE::GetTaskInterface()) {
                tasks->AddTask([] { enforce(); });
            }
        }
    }

    void ProjectileLimiter::enforce() {
        const auto& settings = Settings::get();
        if (!settings.enabled) {
            return;
        }

        auto* manager = RE::Projectile::Manager::GetSingleton();
        if (!manager) {
            return;
        }

        std::vector<RE::Projectile*> candidates;
        candidates.reserve(manager->limited.size() + manager->unlimited.size());

        {
            const RE::BSSpinLockGuard lock(manager->projectileLock);
            collect(manager->limited, candidates);
            collect(manager->unlimited, candidates);
        }

        if (settings.arrows_only) {
            std::erase_if(candidates, [](RE::Projectile* projectile) { return !isArrowLike(projectile); });
        }

        if (candidates.size() <= settings.max_projectiles) {
            return;
        }

        // Prefer culling non-player, then oldest livingTime first.
        std::ranges::sort(candidates, [&](RE::Projectile* a, RE::Projectile* b) {
            const bool aPlayer = isPlayerOwned(a);
            const bool bPlayer = isPlayerOwned(b);
            if (settings.preserve_player && aPlayer != bPlayer) {
                return !aPlayer && bPlayer;
            }
            return a->GetProjectileRuntimeData().livingTime > b->GetProjectileRuntimeData().livingTime;
        });

        const auto excess = candidates.size() - settings.max_projectiles;
        std::uint32_t culled = 0;
        for (std::size_t i = 0; i < excess; ++i) {
            auto* projectile = candidates[i];
            if (!projectile) {
                continue;
            }
            if (settings.preserve_player && isPlayerOwned(projectile)) {
                continue;
            }
            projectile->Kill();
            ++culled;
        }

        if (culled > 0 && settings.log_culls) {
            logger::info("Culled {} world projectiles (pool was {})", culled, candidates.size());
        }
    }
}  // namespace plugin
