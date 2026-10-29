# Argonia's SKSE tree (PLAN §3, chunk 0.3 §b). One CMake for every host:
#   Linux (build VM):    core/ and the bridge protocol, pure C++, unit-tested by `make check` (preset linux-core)
#   Windows (game box):  the same, plus the plugins against CommonLibSSE-NG with MSVC (presets windows-dev|release)
# Address Library ids only; never decompiled code or retail offsets (decision 0003).
cmake_minimum_required(VERSION 3.25)
project(ArgoniaSKSE VERSION 0.3.0 LANGUAGES CXX)

option(ARGONIA_PLUGINS "Build the SKSE plugins (needs MSVC and CommonLibSSE-NG)" ${WIN32})
# A release build never contains a dev-only plugin (dev-only.txt; decision 0003, 0.3 §a).
option(ARGONIA_RELEASE "Release build: dev-only plugins are refused" OFF)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(MSVC)
  set(ARGONIA_WARNINGS /W4 /permissive- /utf-8)
else()
  set(ARGONIA_WARNINGS -Wall -Wextra -Wpedantic -Werror)
endif()

enable_testing()
add_subdirectory(core)
add_subdirectory(ArgoniaBridge/protocol)

# The dev-only list is the contract the release guard reads (3.4 installer, 0003 §release).
file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/dev-only.txt" ARGONIA_DEV_ONLY REGEX "^[^#].*\\.dll$")

if(ARGONIA_PLUGINS)
  include(cmake/CommonLib.cmake)
  add_subdirectory(ArgoniaCore)
  if(NOT ARGONIA_RELEASE)
    add_subdirectory(ArgoniaBridge)
  endif()
endif()
