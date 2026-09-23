cmake_minimum_required(VERSION 3.24)

project(
    @@NAME@@
    VERSION @@VERSION@@
    DESCRIPTION "@@DESCRIPTION@@"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")

# CommonLibSSE-NG: SE/AE 를 하나의 DLL 로 지원하며 Address Library ID 로 주소를 찾는다.
find_package(CommonLibSSE CONFIG REQUIRED)

file(GLOB_RECURSE sources CONFIGURE_DEPENDS src/*.cpp src/*.h)

# SKSEPlugin_Version / SKSEPlugin_Query export 와 버전 정보를 자동 생성한다.
add_commonlibsse_plugin(
    ${PROJECT_NAME}
    AUTHOR "@@AUTHOR@@"
    SOURCES ${sources}
)

target_precompile_headers(${PROJECT_NAME} PRIVATE src/PCH.h)
target_include_directories(${PROJECT_NAME} PRIVATE src)
