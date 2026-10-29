# SkyLink AI (Nexus 175682; source github.com/jarvann/SkryimMCM; MIT by its README; author "SkyrimMCP"/jarvann),
# rebuilt from source against our pinned CommonLibSSE-NG for 1.7.104. DEV ONLY: never ships (skse/dev-only.txt).
# Nothing of it is vendored: its source is fetched at the pinned commit and our one-line patch applied
# (skylink-1.7.104.patch; why in README.md). Built the way its own CMakeLists.txt builds it (a plain SHARED
# library over its src/, nlohmann-json, its own SKSEPluginInfo), not through our argonia_plugin() wrapper.
include(FetchContent)

set(ARGONIA_SKYLINK_SHA 82a0a80d31ae7d2254d40c129650d1e260da38a2)  # "Rebrand to...", 2026-03-27: the 1.0.0 upload

find_package(Git REQUIRED)
# SOURCE_SUBDIR names a folder with no CMakeLists, so FetchContent only fetches; its own CMake (which wants a
# local CommonLib clone in extern/) is never run.
FetchContent_Declare(skylink
  GIT_REPOSITORY https://github.com/jarvann/SkryimMCM.git
  GIT_TAG ${ARGONIA_SKYLINK_SHA}
  PATCH_COMMAND "${GIT_EXECUTABLE}" apply --whitespace=nowarn "${CMAKE_CURRENT_SOURCE_DIR}/skylink-1.7.104.patch"
  UPDATE_DISCONNECTED TRUE
  SOURCE_SUBDIR argonia-fetch-only)
FetchContent_MakeAvailable(skylink)

find_package(nlohmann_json CONFIG REQUIRED)
set(_sl "${skylink_SOURCE_DIR}/SkyrimMCPPlugin/src")
file(GLOB _sl_sources CONFIGURE_DEPENDS "${_sl}/*.cpp")
add_library(SkyrimMCPPlugin SHARED ${_sl_sources})
target_include_directories(SkyrimMCPPlugin PRIVATE "${_sl}")
target_link_libraries(SkyrimMCPPlugin PRIVATE CommonLibSSE::CommonLibSSE nlohmann_json::nlohmann_json)
# Its own SKSE_SUPPORT_XBYAK=0 is dropped: this CommonLib tests the macro with #ifdef, so 0 would turn xbyak on.
target_compile_definitions(SkyrimMCPPlugin PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(SkyrimMCPPlugin PRIVATE /utf-8)  # its sources are UTF-8
set_target_properties(SkyrimMCPPlugin PROPERTIES PREFIX "" OUTPUT_NAME SkyrimMCPPlugin)
install(TARGETS SkyrimMCPPlugin RUNTIME DESTINATION SKSE/Plugins COMPONENT skylink)
install(FILES $<TARGET_PDB_FILE:SkyrimMCPPlugin> DESTINATION SKSE/Plugins COMPONENT skylink OPTIONAL)
