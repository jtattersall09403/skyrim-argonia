// ArgoniaBridge internals shared by the server and the endpoint files (DEV ONLY, 0.3 §a).
#pragma once
#include "bridge_protocol.h"

namespace argonia::bridge {

using Handler = std::string (*)(const Request&);

// Every endpoint file registers its commands at static-init time: `const Register r{"player", &player};`.
std::map<std::string, Handler>& handlers();
struct Register {
  Register(const char* name, Handler h) { handlers()[name] = h; }
};

// Runs fn on the game's main thread (SKSE's task queue) and waits for its JSON reply; an error reply if the
// game does not run it within `timeout`.
std::string on_main_thread(const std::string& cmd, std::function<std::string()> fn,
                           std::chrono::milliseconds timeout = 3s);

// Runs a console line already set on `script` (SetCommand) under SEH, so a line that faults inside the game's
// compiler or a command handler comes back as false (a refusal) instead of killing the game. The shape is
// SkyLink AI's RunScriptSEH (github.com/jarvann/SkryimMCM, SkyrimMCPPlugin/src/Helpers.h; MIT by its README);
// the call is CommonLib's CompileAndRun, whose relocation is right on 1.7 (SkyLink's own is not).
// No C++ object lives in this frame, as __try requires.
inline bool compile_and_run_guarded(RE::Script* script, RE::TESObjectREFR* target) noexcept {
  __try {
    script->CompileAndRun(target);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

// Game messages the endpoints wait on (SKSE's messaging interface), counted so a waiter sees only new ones.
struct GameSignals {
  std::mutex m;
  std::condition_variable cv;
  std::uint64_t loads = 0;  // kPostLoadGame
  bool last_load_ok = false;
  std::uint64_t saves = 0;  // kSaveGame
  std::string last_save;
  std::uint64_t new_games = 0;
};
GameSignals& signals();

// My Games\Skyrim Special Edition (the parent of SKSE's log directory).
std::filesystem::path my_games();

// The player when it stands in a loaded cell; nullptr at the main menu or during a load.
RE::PlayerCharacter* player_in_world();

// Installed by main.cpp: the event sinks at data loaded, the player's animation sink after every load (both on
// the main thread), the frame-time hook at plugin load.
void events_install();
void events_on_game_loaded();
void input_install();

}  // namespace argonia::bridge
