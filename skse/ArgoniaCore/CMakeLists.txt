# ArgoniaCore: all new state and its co-save families; calls the rules in core/ (PLAN §3). Ships (dist).
argonia_plugin(ArgoniaCore COMPONENT dist SOURCES src/main.cpp src/pch.h)
target_link_libraries(ArgoniaCore PRIVATE argonia_core)
# Papyrus source for the natives; compiled to .pex on the game machine by the Creation Kit's compiler (never committed).
install(FILES papyrus/ArgoniaCore.psc DESTINATION Scripts/Source COMPONENT dist)
