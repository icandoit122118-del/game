cmake_minimum_required(VERSION 3.24)

project(
    @@NAME@@
    VERSION @@VERSION@@
    DESCRIPTION "@@DESCRIPTION@@"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

# 외부 라이브러리 없이 SKSE ABI 와 Address Library 로더를 직접 포함하는 최소 플러그인.
add_library(${PROJECT_NAME} SHARED src/main.cpp)

target_compile_definitions(
    ${PROJECT_NAME}
    PRIVATE
        PLUGIN_NAME="${PROJECT_NAME}"
        PLUGIN_AUTHOR="@@AUTHOR@@"
        PLUGIN_VERSION_MAJOR=${PROJECT_VERSION_MAJOR}
        PLUGIN_VERSION_MINOR=$<IF:$<BOOL:${PROJECT_VERSION_MINOR}>,${PROJECT_VERSION_MINOR},0>
        PLUGIN_VERSION_PATCH=$<IF:$<BOOL:${PROJECT_VERSION_PATCH}>,${PROJECT_VERSION_PATCH},0>
        WIN32_LEAN_AND_MEAN
        NOMINMAX
        UNICODE
        _UNICODE
)

if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE /W4 /utf-8 /permissive-)
endif()

target_link_libraries(${PROJECT_NAME} PRIVATE shell32 ole32)
