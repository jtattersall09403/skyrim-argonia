# ArgoniaCore: all new state and its co-save families; calls the rules in core/ (PLAN §3). Ships (dist).
# src/ is the adapter layer only (CommonLibSSE-NG meets skse/core here); every rule is in core/ and tested there.
argonia_plugin(ArgoniaCore COMPONENT dist
  SOURCES src/main.cpp src/engine.cpp src/dialogue.cpp src/natives.cpp src/life.cpp src/combat.cpp src/views.cpp src/prisma_api.h src/core.h src/pch.h)
target_link_libraries(ArgoniaCore PRIVATE argonia_core)
# Papyrus sources: the natives and the intercept perk's fragment; compiled to .pex on the game machine by the
# Creation Kit's compiler (never committed).
install(FILES papyrus/ArgoniaCore.psc papyrus/ARG_PRKF_DialogueIntercept.psc papyrus/ARG_PRKF_RestIntercept.psc
  papyrus/ARG_PRKF_RoadClosed.psc
  DESTINATION Scripts/Source COMPONENT dist)
