# Argonia's SKSE tree: one small plugin, ArgoniaDodgeBuffer (owner ruling #51: our own SKSE code is allowed).
#   Linux (build VM):    the pure logic (core/) and its tests, plain C++, run by skse/check.sh
#   Windows (game box):  the same, plus the plugin against CommonLibSSE-NG with MSVC (preset windows-dev)
# Address Library ids only; never decompiled code or retail offsets (decision 0003).
cmake_minimum_required(VERSION 3.25)
project(ArgoniaSKSE VERSION 0.1.0 LANGUAGES CXX)

option(ARGONIA_PLUGINS "Build the SKSE plugin (needs MSVC and CommonLibSSE-NG)" ${WIN32})

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
add_subdirectory(ArgoniaDodgeBuffer/core)

if(ARGONIA_PLUGINS)
  include(cmake/CommonLib.cmake)
  add_subdirectory(ArgoniaDodgeBuffer)
endif()
