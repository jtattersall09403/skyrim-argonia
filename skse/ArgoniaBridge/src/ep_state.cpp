// The first endpoints (0.3 §a): player, console, save, load. Each refuses what it cannot do truthfully: no player
// in a world, a line the console would not compile, a save that is not on disk, a load the game did not finish.
#include "bridge.h"
#include "argonia/core/life.h"
#include "argonia/core/talk.h"

namespace argonia::bridge {
namespace {

std::string form_json(const RE::TESForm* f) {
  if (!f) return "null";
  return JsonObject().hex("id", f->GetFormID()).str("editor_id", f->GetFormEditorID()).str("name", f->GetName()).done();
}

// player: where the player is and how they are, read on the main thread.
std::string player(const Request& req) {
  return on_main_thread(req.command, [] {
    auto* p = player_in_world();
    if (!p) return reply_error("player", "no player in a world (main menu or loading)");
    auto pos = p->GetPosition();
    auto* av = p->AsActorValueOwner();
    auto* cell = p->GetParentCell();
    auto stat = [av](RE::ActorValue v) {
      return JsonObject().num("current", av->GetActorValue(v)).num("max", av->GetPermanentActorValue(v)).done();
    };
    float angle_z = p->GetAngleZ();
    return reply_ok("player", JsonObject()
                                  .raw("pos", JsonObject().num("x", pos.x).num("y", pos.y).num("z", pos.z).done())
                                  .num("angle_z", angle_z)
                                  .num("heading_deg", angle_z * 180.0 / 3.14159265358979323846)
                                  .raw("health", stat(RE::ActorValue::kHealth))
                                  .raw("stamina", stat(RE::ActorValue::kStamina))
                                  .raw("magicka", stat(RE::ActorValue::kMagicka))
                                  .raw("cell", form_json(cell))
                                  .boolean("interior", cell && cell->IsInteriorCell())
                                  .raw("worldspace", form_json(p->GetWorldspace()))
                                  .boolean("in_air", p->IsInMidair())
                                  .boolean("swimming", p->AsActorState()->IsSwimming())
                                  .boolean("dead", p->IsDead())
                                  .done());
  });
}

// console <line>: runs it as the console does (on the console's selected reference, if any) and returns what the
// console printed. A line the compiler refuses is an error, with the compiler's words.
std::string console(const Request& req) {
  auto line = rest(req);
  if (line.empty()) return reply_error("console", "usage: console <command line>");
  return on_main_thread(req.command, [line] {
    auto* log = RE::ConsoleLog::GetSingleton();
    auto* factory = RE::IFormFactory::GetConcreteFormFactoryByType<RE::Script>();
    auto* script = factory ? factory->Create() : nullptr;
    if (!log || !script) return reply_error("console", "no console log or script factory yet");
    std::string before = log->buffer.c_str() ? log->buffer.c_str() : "";
    script->SetCommand(line);
    auto selected = RE::Console::GetSelectedRef();
    bool ran = compile_and_run_guarded(script, selected.get());
    delete script;
    if (!ran) return reply_error("console", "`" + line + "` faulted inside the game (caught; the game runs on)");
    std::string after = log->buffer.c_str() ? log->buffer.c_str() : "";
    auto out = console_delta(before, after);
    if (console_refused(out)) return reply_error("console", "the console refused `" + line + "`: " + out);
    return reply_ok("console", JsonObject().str("command", line).str("output", out).done());
  });
}

std::filesystem::path save_path(const std::string& name) { return my_games() / "Saves" / (name + ".ess"); }

// save <name>: a save the game writes to Saves\<name>.ess; ok only once the file is there, newer than the request.
std::string save(const Request& req) {
  auto name = rest(req);
  if (!valid_save_name(name)) return reply_error("save", "usage: save <name> (1-64 of A-Z a-z 0-9 space _ -)");
  auto file = save_path(name);
  auto t0 = std::filesystem::file_time_type::clock::now();
  auto queued = on_main_thread(req.command, [name] {
    if (!player_in_world()) return reply_error("save", "no player in a world to save (main menu or loading)");
    auto* m = RE::BGSSaveLoadManager::GetSingleton();
    if (!m) return reply_error("save", "no save manager");
    m->Save(name.c_str());
    return reply_ok("save", "true");
  });
  if (queued.find("\"ok\":true") == std::string::npos) return queued;
  for (int i = 0; i < 300; ++i) {  // 30 s
    std::error_code ec;
    auto size = std::filesystem::file_size(file, ec);
    if (!ec && size > 0 && std::filesystem::last_write_time(file, ec) >= t0 - 2s) {
      std::this_thread::sleep_for(300ms);  // let the writer finish
      return reply_ok("save", JsonObject()
                                  .str("name", name)
                                  .str("file", file.string())
                                  .integer("bytes", static_cast<long long>(std::filesystem::file_size(file, ec)))
                                  .done());
    }
    std::this_thread::sleep_for(100ms);
  }
  return reply_error("save", "the game did not write " + file.string() + " within 30 s");
}

// load <name>: loads Saves\<name>.ess and answers once SKSE's post-load message says it finished (120 s cap).
std::string load(const Request& req) {
  auto name = rest(req);
  if (!valid_save_name(name)) return reply_error("load", "usage: load <name> (1-64 of A-Z a-z 0-9 space _ -)");
  if (!std::filesystem::exists(save_path(name))) return reply_error("load", "no save " + save_path(name).string());
  auto& s = signals();
  std::uint64_t loads_before;
  {
    std::scoped_lock l(s.m);
    loads_before = s.loads;
  }
  auto t0 = std::chrono::steady_clock::now();
  auto queued = on_main_thread(
      req.command,
      [name] {
        auto* m = RE::BGSSaveLoadManager::GetSingleton();
        if (!m) return reply_error("load", "no save manager");
        m->Load(name.c_str(), false);  // no missing-content prompt: the studio loads saves across profile changes
        return reply_ok("load", "true");
      },
      30s);
  if (queued.find("\"ok\":true") == std::string::npos) return queued;
  std::unique_lock l(s.m);
  if (!s.cv.wait_for(l, 120s, [&] { return s.loads > loads_before; }))
    return reply_error("load", "the game did not finish loading " + name + " within 120 s");
  if (!s.last_load_ok) return reply_error("load", "the game reported a failed load of " + name);
  auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
  return reply_ok("load", JsonObject().str("name", name).integer("ms", ms).done());
}

// greeting <speaker world id>: the window our dialogue opens on for that speaker (0.3 §e's timed loop reads the
// greeting back): an SKSE message to ArgoniaCore (core::talk::BridgeGreeting), answered before the dispatch returns.
std::string greeting(const Request& req) {
  namespace talk = argonia::core::talk;
  auto id = rest(req);
  if (id.empty() || id.size() >= sizeof(talk::BridgeGreeting::speaker))
    return reply_error("greeting", "usage: greeting <speaker world id, e.g. npc.imperial-fringe.claywater-station.well-keeper>");
  return on_main_thread(req.command, [id] {
    auto m = std::make_unique<talk::BridgeGreeting>();
    id.copy(m->speaker, sizeof(m->speaker) - 1);
    const bool sent = SKSE::GetMessagingInterface()->Dispatch(talk::kBridgeGreetingMessage, m.get(), sizeof(*m), "ArgoniaCore");
    if (!sent) return reply_error("greeting", "ArgoniaCore is not loaded (the message had no receiver)");
    if (!m->ok) return reply_error("greeting", m->error[0] ? m->error : "ArgoniaCore did not answer");
    return reply_ok("greeting", m->json);
  });
}

// core-suspend <quit|stream_drop|spot_reclaim>: ArgoniaCore's hidden suspend save (2.8 §c), the stream client's hand on a drop.
// The call is an SKSE message to ArgoniaCore (core::life::BridgeSuspend), dispatched on the main thread; ok only
// once Saves\ArgoniaSuspend.ess exists, newer than the call (30 s cap), as `save` does.
std::string core_suspend(const Request& req) {
  namespace life = argonia::core::life;
  auto why = rest(req);
  if (!life::suspend_why(why)) return reply_error("core-suspend", "usage: core-suspend <quit|stream_drop|spot_reclaim>");
  auto file = save_path(std::string(life::kSuspendSave));
  auto t0 = std::filesystem::file_time_type::clock::now();
  auto queued = on_main_thread(req.command, [why] {
    if (!player_in_world()) return reply_error("core-suspend", "no player in a world to save (main menu or loading)");
    life::BridgeSuspend m{};
    why.copy(m.why, sizeof(m.why) - 1);
    const bool sent = SKSE::GetMessagingInterface()->Dispatch(life::kBridgeSuspendMessage, &m, sizeof(m), "ArgoniaCore");
    if (!sent || !m.written)
      return reply_error("core-suspend", sent ? "ArgoniaCore refused: the game cannot save now (a menu or load open, "
                                                "or the player dying); its log says which"
                                              : "ArgoniaCore is not loaded (the message had no receiver)");
    return reply_ok("core-suspend", "true");
  });
  if (queued.find("\"ok\":true") == std::string::npos) return queued;
  for (int i = 0; i < 300; ++i) {  // 30 s
    std::error_code ec;
    auto size = std::filesystem::file_size(file, ec);
    if (!ec && size > 0 && std::filesystem::last_write_time(file, ec) >= t0 - 2s) {
      std::this_thread::sleep_for(300ms);  // let the writer finish
      return reply_ok("core-suspend", JsonObject().str("why", why).str("file", file.string()).done());
    }
    std::this_thread::sleep_for(100ms);
  }
  return reply_error("core-suspend", "ArgoniaCore queued the save but " + file.string() + " was not written within 30 s");
}

const Register r_player{"player", &player};
const Register r_console{"console", &console};
const Register r_save{"save", &save};
const Register r_load{"load", &load};
const Register r_core_suspend{"core-suspend", &core_suspend};
const Register r_greeting{"greeting", &greeting};

}  // namespace
}  // namespace argonia::bridge
