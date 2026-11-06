# ArgoniaDodgeBuffer: an attack pressed during a TK Dodge RE dodge plays as the dodge ends (ruling #51).
argonia_plugin(ArgoniaDodgeBuffer COMPONENT dist
  SOURCES src/main.cpp src/pch.h core/buffer.h core/ini.h)
target_include_directories(ArgoniaDodgeBuffer PRIVATE core)
install(FILES ArgoniaDodgeBuffer.ini DESTINATION SKSE/Plugins COMPONENT dist)
