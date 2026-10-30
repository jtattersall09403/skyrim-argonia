# skse/core: the rules Skyrim's own systems cannot carry (PLAN §3, 1.1 §a's native map). Pure C++: no Skyrim,
# SKSE or Windows type is ever included here, so every rule is unit-tested on the build VM. Its numbers come from
# generated/ (tools/argonia_world/core_tables.py; goal G11.2), never typed into a source.
configure_file(include/argonia/core/version.h.in "${CMAKE_CURRENT_BINARY_DIR}/generated/argonia/core/version.h" @ONLY)

set(ARGONIA_CORE_MODULES curve sheet effects carriers progression sitting rest death respawn conditions disposition
    journal items families weather json router roundtrip quest_runtime quest_state actions topics seam talk)
set(ARGONIA_CORE_SOURCES src/cosave.cpp)
foreach(m IN LISTS ARGONIA_CORE_MODULES)
  list(APPEND ARGONIA_CORE_SOURCES src/${m}.cpp)
endforeach()

add_library(argonia_core STATIC ${ARGONIA_CORE_SOURCES})
target_include_directories(argonia_core PUBLIC include generated "${CMAKE_CURRENT_BINARY_DIR}/generated")
target_compile_options(argonia_core PRIVATE ${ARGONIA_WARNINGS})

# One test executable per module (ctest core.<module>), plus the co-save contract and the generated message twin.
foreach(m IN ITEMS cosave messages ${ARGONIA_CORE_MODULES})
  add_executable(argonia_core_test_${m} tests/test_${m}.cpp)
  target_link_libraries(argonia_core_test_${m} PRIVATE argonia_core)
  target_include_directories(argonia_core_test_${m} PRIVATE tests)
  target_compile_options(argonia_core_test_${m} PRIVATE ${ARGONIA_WARNINGS})
  add_test(NAME core.${m} COMMAND argonia_core_test_${m})
endforeach()
