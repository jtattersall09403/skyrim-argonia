# CommonLibSSE-NG, pinned (docs/research/journals/skse-build.md says why this fork and this tag).
# alandtse/CommonLibSSE-NG is the maintained NG line (GPL-3.0-or-later, as our code is): v15.2.0 declares
# RUNTIME_SSE_1_7_104 and reads Address Library format 5 (1.7.99+). Its dependencies come from our vcpkg.json.
include(FetchContent)

set(ARGONIA_COMMONLIB_TAG v15.2.0)
set(ARGONIA_COMMONLIB_SHA dec1be18b1880c1f643afedc0d01db0118d648f9)

# Its own unit tests are not ours to build; a release tag lets it link its published MSVC bundle (PREBUILT.md)
# instead of a ~16 min source build, falling back to source when the toolset differs.
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(COMMONLIB_PREBUILT ON CACHE BOOL "")

FetchContent_Declare(CommonLibSSE
  GIT_REPOSITORY https://github.com/alandtse/CommonLibSSE-NG.git
  GIT_TAG ${ARGONIA_COMMONLIB_TAG}
  GIT_SHALLOW TRUE
  GIT_SUBMODULES extern/openvr
  GIT_PROGRESS TRUE)
FetchContent_MakeAvailable(CommonLibSSE)

# A tag can move; the commit cannot. Refuse anything but the pinned commit.
find_package(Git REQUIRED)
execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${commonlibsse_SOURCE_DIR}" rev-parse HEAD
  OUTPUT_VARIABLE _argonia_cl_head OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT _argonia_cl_head STREQUAL ARGONIA_COMMONLIB_SHA)
  message(FATAL_ERROR "CommonLibSSE-NG ${ARGONIA_COMMONLIB_TAG} is ${_argonia_cl_head}, pinned ${ARGONIA_COMMONLIB_SHA}")
endif()
message(STATUS "CommonLibSSE-NG ${ARGONIA_COMMONLIB_TAG} at ${_argonia_cl_head}")

# One plugin, the Argonia way: Address Library (any runtime it knows, the pin is 1.7.104), our PCH, our install.
#   argonia_plugin(<name> COMPONENT dist|dev SOURCES ...)
function(argonia_plugin name)
  cmake_parse_arguments(P "" "COMPONENT" "SOURCES" ${ARGN})
  if(P_COMPONENT STREQUAL "dev" AND NOT "${name}.dll" IN_LIST ARGONIA_DEV_ONLY)
    message(FATAL_ERROR "${name} is dev-only but not in skse/dev-only.txt")
  endif()
  if(P_COMPONENT STREQUAL "dist" AND "${name}.dll" IN_LIST ARGONIA_DEV_ONLY)
    message(FATAL_ERROR "${name} is in skse/dev-only.txt and cannot be a dist plugin")
  endif()
  add_commonlibsse_plugin(${name}
    NAME "${name}"
    AUTHOR "Elder Souls: Argonia"
    VERSION ${PROJECT_VERSION}
    USE_ADDRESS_LIBRARY
    SOURCES ${P_SOURCES})
  target_precompile_headers(${name} PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src/pch.h")
  target_compile_options(${name} PRIVATE ${ARGONIA_WARNINGS})
  install(TARGETS ${name} RUNTIME DESTINATION SKSE/Plugins COMPONENT ${P_COMPONENT})
  install(FILES $<TARGET_PDB_FILE:${name}> DESTINATION SKSE/Plugins COMPONENT ${P_COMPONENT} OPTIONAL)
endfunction()
