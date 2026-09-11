cmake_minimum_required(VERSION 3.24)

set(VCPKG_TARGET_TRIPLET "x64-windows-static-md" CACHE STRING "")

project(FootIKFix VERSION 0.5.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
set(CMAKE_SKIP_INSTALL_RULES TRUE)

include(FetchContent)

set(ENABLE_SKYRIM_SE   ON  CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_AE   ON  CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_VR   OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS        OFF CACHE BOOL "" FORCE)
set(SKSE_SUPPORT_XBYAK OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    CommonLibSSE
    SOURCE_DIR "D:/MO2-Skyrim/_unpack/build/CommonLibSSE-NG"
)
FetchContent_MakeAvailable(CommonLibSSE)

include("${commonlibsse_SOURCE_DIR}/cmake/CommonLibSSE.cmake")

add_commonlibsse_plugin(${PROJECT_NAME}
    SOURCES src/plugin.cpp
    NAME    "FootIKFix"
    AUTHOR  "고래 / Plan NG format-5"
    VERSION 0.5.0
)
set_target_properties(${PROJECT_NAME} PROPERTIES OUTPUT_NAME "FootIKFix")
target_include_directories(${PROJECT_NAME} PRIVATE src)
target_compile_options(${PROJECT_NAME} PRIVATE /W4)
target_precompile_headers(${PROJECT_NAME}
    PRIVATE "${CMAKE_SOURCE_DIR}/src/PCH.h"
)
