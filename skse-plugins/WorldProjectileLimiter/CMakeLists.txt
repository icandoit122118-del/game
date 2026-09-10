cmake_minimum_required(VERSION 3.25)

# Before CommonLibSSE-NG subdirectory (no OpenVR on this PC).
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "Disable Skyrim VR for this plugin" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "Disable CommonLib tests" FORCE)

project(
        WorldProjectileLimiter
        VERSION 0.1.0
        LANGUAGES CXX)
set(PROJECT_LICENSE "MIT")
set(PROJECT_AUTHOR "OpenSkyrimSE-Perf")
set(PROJECT_FRIENDLY_NAME "World Projectile Limiter")
set(PROJECT_LONG_NAME "World Projectile Limiter SKSE")
set(PROJECT_DESCRIPTION "SKSE performance plugin: cull excess world projectiles (arrows/bolts)")
set(PROJECT_COPYRIGHT "Copyright")

list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")
include(GNUInstallDirs)
include(addpluginsources)
include(pluginconfig)
include(plugintarget)
include(pluginpackage)
cmake_language(DEFER CALL include pluginbuildoptions)
include("${PROJECT_SOURCE_DIR}/local.cmake" OPTIONAL)
