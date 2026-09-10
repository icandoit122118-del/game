#include "Hooks.h"
#include "ProjectileLimiter.h"
#include "Settings.h"

namespace plugin {
    void Hooks::install() {
        Settings::get().load();
        ProjectileLimiter::start();
        logger::info("WorldProjectileLimiter hooks ready");
    }
}  // namespace plugin
