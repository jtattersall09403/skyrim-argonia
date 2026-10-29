# skse/core: the rules Skyrim's own systems cannot carry (PLAN §3, 1.1 §a's native map). Pure C++: no Skyrim,
# SKSE or Windows type is ever included here, so every rule is unit-tested on the build VM.
configure_file(include/argonia/core/version.h.in "${CMAKE_CURRENT_BINARY_DIR}/generated/argonia/core/version.h" @ONLY)

add_library(argonia_core STATIC src/cosave.cpp)
target_include_directories(argonia_core PUBLIC include "${CMAKE_CURRENT_BINARY_DIR}/generated")
target_compile_options(argonia_core PRIVATE ${ARGONIA_WARNINGS})

add_executable(argonia_core_tests tests/test_cosave.cpp)
target_link_libraries(argonia_core_tests PRIVATE argonia_core)
target_compile_options(argonia_core_tests PRIVATE ${ARGONIA_WARNINGS})
add_test(NAME core.cosave COMMAND argonia_core_tests)
