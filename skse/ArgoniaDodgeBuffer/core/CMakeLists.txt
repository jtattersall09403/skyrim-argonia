# The pure logic (no engine types): the buffer window, the hold test, end-event matching and the ini reader.
add_library(dodgebuffer_core INTERFACE)
target_include_directories(dodgebuffer_core INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(dodgebuffer_core INTERFACE cxx_std_23)

add_executable(test_buffer ../tests/test_buffer.cpp)
target_link_libraries(test_buffer PRIVATE dodgebuffer_core)
target_compile_options(test_buffer PRIVATE ${ARGONIA_WARNINGS})
add_test(NAME dodgebuffer.buffer COMMAND test_buffer)
