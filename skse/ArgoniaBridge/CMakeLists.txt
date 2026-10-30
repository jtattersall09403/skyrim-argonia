# ArgoniaBridge: DEV ONLY (0.3 §a). The whole bridge list (SkyLink AI does not load on 1.7.104), by SkyLink's method: a named pipe, a token, the
# game's main thread for every handler. It is listed in skse/dev-only.txt and never ships (decision 0003).
if(ARGONIA_RELEASE)
  message(FATAL_ERROR "ArgoniaBridge is dev-only and cannot be part of a release build")
endif()
argonia_plugin(ArgoniaBridge COMPONENT dev SOURCES src/main.cpp src/ep_state.cpp src/ep_core.cpp src/ep_world.cpp src/ep_events.cpp src/ep_input.cpp src/ep_nav.cpp src/ep_dev.cpp src/tcp.cpp src/bridge.h src/server.h src/pch.h)
target_link_libraries(ArgoniaBridge PRIVATE argonia_bridge_protocol argonia_core ws2_32)
# Winsock and CommonLib's <Windows.h> clash in one TU, so the socket file skips the PCH (src/server.h).
set_source_files_properties(src/tcp.cpp PROPERTIES SKIP_PRECOMPILE_HEADERS ON)
target_compile_definitions(ArgoniaBridge PRIVATE ARGONIA_DEV_ONLY=1)
install(FILES ping.ps1 DESTINATION tools COMPONENT dev)
