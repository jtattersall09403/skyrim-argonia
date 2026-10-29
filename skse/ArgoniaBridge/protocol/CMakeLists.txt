# The bridge's protocol is pure C++ and built on every host; the plugin that uses it is dev-only and Windows-only.
add_library(argonia_bridge_protocol STATIC bridge_protocol.cpp)
target_include_directories(argonia_bridge_protocol PUBLIC .)
target_compile_options(argonia_bridge_protocol PRIVATE ${ARGONIA_WARNINGS})

add_executable(argonia_bridge_protocol_tests ../tests/test_protocol.cpp)
target_include_directories(argonia_bridge_protocol_tests PRIVATE ../../core/tests)
target_link_libraries(argonia_bridge_protocol_tests PRIVATE argonia_bridge_protocol)
target_compile_options(argonia_bridge_protocol_tests PRIVATE ${ARGONIA_WARNINGS})
add_test(NAME bridge.protocol COMMAND argonia_bridge_protocol_tests)
