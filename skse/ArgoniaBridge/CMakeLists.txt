# ArgoniaBridge: DEV ONLY (0.3 §a). Only what SkyLink AI lacks, by SkyLink's method: a named pipe, a token, the
# game's main thread for every handler. It is listed in skse/dev-only.txt and never ships (decision 0003).
if(ARGONIA_RELEASE)
  message(FATAL_ERROR "ArgoniaBridge is dev-only and cannot be part of a release build")
endif()
argonia_plugin(ArgoniaBridge COMPONENT dev SOURCES src/main.cpp src/pch.h)
target_link_libraries(ArgoniaBridge PRIVATE argonia_bridge_protocol argonia_core)
target_compile_definitions(ArgoniaBridge PRIVATE ARGONIA_DEV_ONLY=1)
install(FILES ping.ps1 DESTINATION tools COMPONENT dev)
