// World endpoints (0.3 §a): teleport, time, weather; and the reads: quest, global, av, inventory. A setter reads
// its value back before it answers ok, so a write the game ignored is an error, not a silent pass.
#include "bridge.h"

namespace argonia::bridge {
namespace {

// "0x14" or an 8-digit hex id is a form id; anything else an editor id (found only for forms whose editor ids
// the game keeps: cells, quests, globals; others with powerofthree's Tweaks).
RE::TESForm* find_form(std::string_view s) {
  if ((s.starts_with("0x") || s.starts_with("0X") || s.size() == 8))
    if (auto id = to_form_id(s)) return RE::TESForm::LookupByID(*id);
  return RE::TESForm::LookupByEditorID(s);
}

RE::TESObjectCELL* find_interior(const std::string& edid) {
  if (auto* f = RE::TESForm::LookupByEditorID(edid); f && f->Is(RE::FormType::Cell)) return static_cast<RE::TESObjectCELL*>(f);
  auto* dh = RE::TESDataHandler::GetSingleton();
  if (!dh) return nullptr;
  for (auto* c : dh->interiorCells)
    if (c && _stricmp(c->GetFormEditorID(), edid.c_str()) == 0) return c;
  return nullptr;
}

std::string form_ref(const RE::TESForm* f) {
  if (!f) return "null";
  return JsonObject().hex("id", f->GetFormID()).str("editor_id", f->GetFormEditorID()).str("name", f->GetName()).done();
}

std::string where(RE::PlayerCharacter* p) {
  auto pos = p->GetPosition();
  return JsonObject()
      .raw("pos", JsonObject().num("x", pos.x).num("y", pos.y).num("z", pos.z).done())
      .raw("cell", form_ref(p->GetParentCell()))
      .raw("worldspace", form_ref(p->GetWorldspace()))
      .done();
}

bool loading() {
  auto* ui = RE::UI::GetSingleton();
  return !ui || ui->IsMenuOpen(RE::LoadingMenu::MENU_NAME);
}

// Waits (off the main thread) for a load to start and finish; the reply is where the player stands after it.
std::string wait_arrival(const std::string& cmd, RE::FormID before_cell, const std::string& want_editor_id) {
  bool started = false;
  for (int i = 0; i < 600; ++i) {  // 60 s
    std::this_thread::sleep_for(100ms);
    auto state = on_main_thread(cmd, [before_cell] {
      auto* p = player_in_world();
      if (loading() || !p) return std::string("loading");
      auto* cell = p->GetParentCell();
      if (cell && cell->GetFormID() != before_cell) return std::string("moved");
      return std::string("same");
    });
    if (state == "loading") {
      started = true;
      continue;
    }
    if (state == "moved" || (started && state == "same")) {
      return on_main_thread(cmd, [cmd, want_editor_id] {
        auto* p = player_in_world();
        if (!p) return reply_error(cmd, "no player after the move");
        auto* cell = p->GetParentCell();
        std::string got = cell ? cell->GetFormEditorID() : "";
        if (!want_editor_id.empty() && _stricmp(got.c_str(), want_editor_id.c_str()) != 0 && p->GetWorldspace() == nullptr)
          return reply_error(cmd, "arrived in " + got + ", not " + want_editor_id);
        return reply_ok(cmd, where(p));
      });
    }
    if (state.find("did not run the task") != std::string::npos) {  // a loading screen holds the task queue
      started = true;
      continue;
    }
    if (state.starts_with("{")) return state;  // an error from the main thread
    if (!started && i >= 50) return reply_error(cmd, "the game started no load within 5 s (unknown cell or reference?)");
  }
  return reply_error(cmd, "the load did not finish within 60 s");
}

// teleport cell <editor id> | teleport ref <form id> | teleport pos <x> <y> <z>
std::string teleport(const Request& req) {
  const std::string usage = "usage: teleport cell <editor id> | ref <form id> | pos <x> <y> <z>";
  if (req.args.size() < 2) return reply_error("teleport", usage);
  const auto& how = req.args[0];
  if (how == "pos") {
    if (req.args.size() != 4) return reply_error("teleport", usage);
    auto x = to_number(req.args[1]), y = to_number(req.args[2]), z = to_number(req.args[3]);
    if (!x || !y || !z) return reply_error("teleport", "pos needs three numbers");
    RE::NiPoint3 to{float(*x), float(*y), float(*z)};
    auto set = on_main_thread("teleport", [to] {
      auto* p = player_in_world();
      if (!p) return reply_error("teleport", "no player in a world (main menu or loading)");
      p->SetPosition(to, true);
      return reply_ok("teleport", "true");
    });
    if (set.find("\"ok\":true") == std::string::npos) return set;
    std::this_thread::sleep_for(200ms);
    return on_main_thread("teleport", [to] {
      auto* p = player_in_world();
      if (!p) return reply_error("teleport", "no player after the move");
      auto at = p->GetPosition();
      if (std::abs(at.x - to.x) > 64 || std::abs(at.y - to.y) > 64 || std::abs(at.z - to.z) > 512)
        return reply_error("teleport", "the player is not at the target after the move: " + where(p));
      return reply_ok("teleport", where(p));
    });
  }
  if (how != "cell" && how != "ref") return reply_error("teleport", usage);
  std::string target = rest(req, 1);
  auto before = std::make_shared<std::atomic<RE::FormID>>(0);
  auto started = on_main_thread("teleport", [how, target, before] {
    auto* p = player_in_world();
    if (!p) return reply_error("teleport", "no player in a world (main menu or loading)");
    *before = p->GetParentCell() ? p->GetParentCell()->GetFormID() : 0;
    if (how == "ref") {
      auto* ref = find_form(target);
      auto* r = ref ? ref->AsReference() : nullptr;
      if (!r) return reply_error("teleport", "no reference " + target);
      p->MoveTo(r);
      return reply_ok("teleport", "true");
    }
    // An unknown name is refused before coc: coc searches every plugin's cells for it on the main thread, which
    // held the task queue past 3 s with this load order (live, 2026-10-29). Interior cells only (they stay in
    // memory with their editor ids); an exterior is reached by `teleport pos` or `ref`.
    if (!find_interior(target)) return reply_error("teleport", "no interior cell " + target + " (exteriors: teleport pos or ref)");
    // coc, as the console does it.
    auto* factory = RE::IFormFactory::GetConcreteFormFactoryByType<RE::Script>();
    auto* script = factory ? factory->Create() : nullptr;
    if (!script) return reply_error("teleport", "no script factory");
    script->SetCommand("coc " + target);
    bool ran = compile_and_run_guarded(script, p);
    delete script;
    if (!ran) return reply_error("teleport", "coc " + target + " faulted inside the game (caught)");
    return reply_ok("teleport", "true");
  });
  if (started.find("\"ok\":true") == std::string::npos) return started;
  return wait_arrival("teleport", before->load(), how == "cell" ? target : "");
}

std::string calendar_json(RE::Calendar* c) {
  return JsonObject()
      .num("hour", c->GetHour())
      .num("day", c->GetDay())
      .integer("month", c->GetMonth())
      .integer("year", c->GetYear())
      .num("days_passed", c->GetCurrentGameTime())
      .num("timescale", c->GetTimescale())
      .done();
}

// time [hour]: the calendar; with an hour (0 <= h < 24) sets GameHour and reads it back.
std::string time_ep(const Request& req) {
  std::optional<double> hour;
  if (!req.args.empty()) {
    hour = to_number(req.args[0]);
    if (!hour || *hour < 0 || *hour >= 24) return reply_error("time", "the hour must be a number in [0, 24)");
  }
  return on_main_thread("time", [hour] {
    auto* c = RE::Calendar::GetSingleton();
    if (!c || !c->gameHour) return reply_error("time", "no calendar yet (main menu?)");
    if (hour) {
      c->gameHour->value = float(*hour);
      if (std::abs(c->GetHour() - *hour) > 0.01) return reply_error("time", "the hour did not take");
    }
    return reply_ok("time", calendar_json(c));
  });
}

// weather [form id | editor id]: the current weather; with one, forces it and reads it back.
std::string weather(const Request& req) {
  std::string want = rest(req);
  return on_main_thread("weather", [want] {
    auto* sky = RE::Sky::GetSingleton();
    if (!sky || !player_in_world()) return reply_error("weather", "no sky (main menu or loading)");
    if (!want.empty()) {
      auto* f = find_form(want);
      auto* w = f ? f->As<RE::TESWeather>() : nullptr;
      if (!w) return reply_error("weather", "no weather " + want);
      sky->ForceWeather(w, true);
      if (sky->currentWeather != w) return reply_error("weather", "the sky did not take " + want);
    }
    return reply_ok("weather", JsonObject()
                                   .raw("current", form_ref(sky->currentWeather))
                                   .raw("last", form_ref(sky->lastWeather))
                                   .num("transition", sky->currentWeatherPct)
                                   .boolean("interior", player_in_world()->GetParentCell()->IsInteriorCell())
                                   .done());
  });
}

// quest <form id | editor id>: its stage and state. `running` is the console's GetQuestRunning (the quest's enabled
// flag): CommonLib's IsRunning() is only "not stopping", true for 2,385 idle quests (game-7); it stays as `not_stopping`.
std::string quest(const Request& req) {
  std::string q = rest(req);
  if (q.empty()) return reply_error("quest", "usage: quest <form id | editor id>");
  return on_main_thread("quest", [q] {
    auto* f = find_form(q);
    auto* quest = f ? f->As<RE::TESQuest>() : nullptr;
    if (!quest) return reply_error("quest", "no quest " + q);
    return reply_ok("quest", JsonObject()
                                 .hex("id", quest->GetFormID())
                                 .str("editor_id", quest->GetFormEditorID())
                                 .str("name", quest->GetName())
                                 .integer("stage", quest->GetCurrentStageID())
                                 .boolean("running", quest->IsEnabled())
                                 .boolean("not_stopping", quest->IsRunning())
                                 .boolean("enabled", quest->IsEnabled())
                                 .boolean("completed", quest->IsCompleted())
                                 .done());
  });
}

// quests: every running quest, by editor id and its plugin (the quarantine journey's list, 0.4 §b). The console's
// `sq` is no use for this: its output is the console buffer's tail, 1,567 "(Off)" lines, the running ones cut off.
std::string quests(const Request&) {
  return on_main_thread("quests", [] {
    auto* dh = RE::TESDataHandler::GetSingleton();
    if (!dh) return reply_error("quests", "no data handler yet");
    std::string out = "[";
    std::size_t total = 0;
    for (auto* q : dh->GetFormArray<RE::TESQuest>()) {
      if (!q) continue;
      ++total;
      if (!q->IsEnabled()) continue;  // the console's GetQuestRunning; CommonLib's IsRunning() is only "not stopping"
      auto* file = q->GetFile(0);
      if (out.size() > 1) out += ',';
      out += JsonObject()
                 .hex("id", q->GetFormID())
                 .str("editor_id", q->GetFormEditorID())
                 .str("plugin", file ? file->GetFilename() : "")
                 .integer("stage", q->GetCurrentStageID())
                 .done();
    }
    return reply_ok("quests", JsonObject().integer("total", static_cast<int>(total)).raw("running", out + "]").done());
  });
}

// music: the music type playing and the queue under it (the quarantine journey's read: only our silence plays).
std::string music(const Request&) {
  return on_main_thread("music", [] {
    auto* mm = RE::BSMusicManager::GetSingleton();
    if (!mm) return reply_error("music", "no music manager yet");
    // Not every BSIMusicType is a form: the engine's own NoMusic is not, and casting it to BGSMusicType crashed the
    // game (game-7). Only an object whose vtable is BGSMusicType's BSIMusicType vtable is read as a form.
    static const std::uintptr_t form_vt = REL::Relocation<std::uintptr_t>{RE::VTABLE_BGSMusicType[1]}.address();
    auto ref = [](RE::BSIMusicType* t) -> std::string {
      if (!t) return "null";
      if (*reinterpret_cast<std::uintptr_t*>(t) != form_vt) return R"({"id":null,"editor_id":"","engine":true})";
      return form_ref(static_cast<RE::BGSMusicType*>(t));
    };
    std::string queue = "[";
    for (auto* t : mm->musicQueue) {
      if (queue.size() > 1) queue += ',';
      queue += ref(t);
    }
    return reply_ok("music", JsonObject().raw("current", ref(mm->current)).raw("queue", queue + "]").done());
  });
}

// plugin <file>: a loaded plugin's runtime form-id prefix ("10" for a full plugin, "FE001" for a light one). The
// game keeps no reference's editor id, so `player.moveto ARG_Ref_...` is refused at the console (game-7); the
// scenes and journeys name refs by the world database's local id under this prefix (infra/gpu-box/scene_ids.py).
std::string plugin(const Request& req) {
  std::string name = rest(req);
  if (name.empty()) return reply_error("plugin", "usage: plugin <file name>");
  return on_main_thread("plugin", [name] {
    auto* dh = RE::TESDataHandler::GetSingleton();
    auto* file = dh ? dh->LookupModByName(name) : nullptr;
    if (!file || file->GetCompileIndex() == 0xFF) return reply_error("plugin", "not loaded: " + name);
    char prefix[8];
    if (file->IsLight()) std::snprintf(prefix, sizeof prefix, "FE%03X", file->GetSmallFileCompileIndex());
    else std::snprintf(prefix, sizeof prefix, "%02X", file->GetCompileIndex());
    return reply_ok("plugin", JsonObject().str("file", file->GetFilename()).str("prefix", prefix)
                                  .boolean("light", file->IsLight()).done());
  });
}

// global <form id | editor id>: its value.
std::string global(const Request& req) {
  std::string g = rest(req);
  if (g.empty()) return reply_error("global", "usage: global <form id | editor id>");
  return on_main_thread("global", [g] {
    auto* f = find_form(g);
    auto* gl = f ? f->As<RE::TESGlobal>() : nullptr;
    if (!gl) return reply_error("global", "no global " + g);
    return reply_ok("global", JsonObject().hex("id", gl->GetFormID()).str("editor_id", gl->GetFormEditorID()).num("value", gl->value).done());
  });
}

}  // namespace

std::string actor_unready(RE::Actor* a) {
  if (!a) return "is missing";
  if (a->IsDisabled()) return "is disabled";
  auto* cell = a->GetParentCell();
  if (!a->Is3DLoaded() || !cell || !cell->IsAttached()) return "is not loaded (no 3D or not in a loaded cell)";
  if (!a->GetActorRuntimeData().currentProcess) return "has no AI process";
  return {};
}

namespace {

RE::Actor* actor_arg(const Request& req, std::size_t i, std::string& err) {
  if (req.args.size() <= i || req.args[i] == "player") {
    auto* p = player_in_world();
    if (!p) err = "no player in a world (main menu or loading)";
    return p;
  }
  auto* f = find_form(req.args[i]);
  auto* r = f ? f->AsReference() : nullptr;
  auto* a = r ? r->As<RE::Actor>() : nullptr;
  if (!a) {
    err = "no actor reference " + req.args[i];
    return nullptr;
  }
  if (auto why = actor_unready(a); !why.empty()) {
    err = "actor " + req.args[i] + " " + why;
    return nullptr;
  }
  return a;
}

// av <actor value name> [player | <actor ref id>]: current, base and permanent values.
std::string av(const Request& req) {
  if (req.args.empty()) return reply_error("av", "usage: av <name> [player | <ref id>]");
  return on_main_thread("av", [req] {
    auto v = RE::ActorValueList::LookupActorValueByName(req.args[0].c_str());
    // The lookup answers an unknown name with a real value (0 for NoSuchValueZZ, live 2026-10-29), so the
    // name must come back from the value it found.
    const char* back = v == RE::ActorValue::kNone || v >= RE::ActorValue::kTotal ? nullptr : RE::ActorValueList::GetActorValueName(v);
    if (!back || _stricmp(back, req.args[0].c_str()) != 0) return reply_error("av", "no actor value " + req.args[0]);
    std::string err;
    auto* a = actor_arg(req, 1, err);
    if (!a) return reply_error("av", err);
    auto* o = a->AsActorValueOwner();
    return reply_ok("av", JsonObject()
                              .str("name", req.args[0])
                              .hex("actor", a->GetFormID())
                              .num("current", o->GetActorValue(v))
                              .num("base", o->GetBaseActorValue(v))
                              .num("permanent", o->GetPermanentActorValue(v))
                              .done());
  });
}

// graph <player | ref id> <name>...: each behaviour graph variable as bool, int and float (the types the graph
// answers; a name no graph knows is null). bAnimationDriven is the root-motion read of 0.2 §c's dodge.
std::string graph(const Request& req) {
  if (req.args.size() < 2) return reply_error("graph", "usage: graph <player | ref id> <name>...");
  return on_main_thread("graph", [req] {
    std::string err;
    auto* a = actor_arg(req, 0, err);
    if (!a) return reply_error("graph", err);
    JsonObject vars;
    for (std::size_t i = 1; i < req.args.size(); ++i) {
      const auto& n = req.args[i];
      bool b = false;
      std::int32_t iv = 0;
      float f = 0.0f;
      const bool hb = a->GetGraphVariableBool(n, b), hi = a->GetGraphVariableInt(n, iv), hf = a->GetGraphVariableFloat(n, f);
      if (!hb && !hi && !hf) {
        vars.raw(n, "null");
        continue;
      }
      vars.raw(n, JsonObject().boolean("bool", b).integer("int", iv).num("float", f).done());
    }
    return reply_ok("graph", JsonObject().hex("actor", a->GetFormID()).raw("vars", vars.done()).done());
  });
}

// inventory [player | <ref id>]: every item with its count and whether it is worn.
std::string inventory(const Request& req) {
  return on_main_thread("inventory", [req] {
    RE::TESObjectREFR* who = nullptr;
    if (req.args.empty() || req.args[0] == "player") {
      who = player_in_world();
      if (!who) return reply_error("inventory", "no player in a world (main menu or loading)");
    } else {
      auto* f = find_form(req.args[0]);
      who = f ? f->AsReference() : nullptr;
      if (!who) return reply_error("inventory", "no reference " + req.args[0]);
    }
    std::string items = "[";
    for (auto& [obj, data] : who->GetInventory()) {
      if (!obj || data.first <= 0) continue;
      if (items.size() > 1) items += ',';
      items += JsonObject()
                   .hex("id", obj->GetFormID())
                   .str("name", obj->GetName())
                   .integer("count", data.first)
                   .boolean("worn", data.second && data.second->IsWorn())
                   .done();
    }
    return reply_ok("inventory", JsonObject().hex("owner", who->GetFormID()).raw("items", items + "]").done());
  });
}

// One actor's AI state: its process level (-1 none, 0 high ... 3 low), whether its own AI runs (kProcessMe, which
// Papyrus EnableAI and the console's `tai` on a ref switch), the package it runs, and the flags a frozen actor shows.
std::string actor_json(RE::Actor* a, const RE::NiPoint3& from) {
  auto* base = a->GetActorBase();
  auto* pkg = a->GetCurrentPackage();
  auto pos = a->GetPosition();
  auto* cell = a->GetParentCell();
  return JsonObject()
      .hex("ref", a->GetFormID())
      .hex("base", base ? base->GetFormID() : 0)
      .str("name", a->GetName())
      .integer("level", static_cast<int>(a->GetProcessLevel()))
      .boolean("process", a->GetActorRuntimeData().currentProcess != nullptr)
      .boolean("ai_enabled", a->IsAIEnabled())
      .hex("package", pkg ? pkg->GetFormID() : 0)
      .boolean("combat", a->IsInCombat())
      .boolean("dead", a->IsDead())
      .boolean("disabled", a->IsDisabled())
      .boolean("loaded_3d", a->Get3D() != nullptr)
      .hex("cell", cell ? cell->GetFormID() : 0)
      .num("dist", pos.GetDistance(from))
      .raw("pos", JsonObject().num("x", pos.x).num("y", pos.y).num("z", pos.z).done())
      .done();
}

// actors [radius] [ref id...]: the engine's process switches (the global AI toggles), then every actor in the four
// process lists within radius of the player (default 6000), and each named ref whether listed or not. The read that
// splits "no AI" (game-8): an actor with no process has no package; a listed one with ai_enabled false is switched off.
std::string actors(const Request& req) {
  return on_main_thread("actors", [req] {
    auto* p = player_in_world();
    auto* lists = RE::ProcessLists::GetSingleton();
    if (!p || !lists) return reply_error("actors", "no player in a world or no process lists");
    double radius = 6000.0;
    std::vector<RE::Actor*> named;
    for (const auto& s : req.args) {
      if (auto* f = s.size() == 8 || s.starts_with("0x") ? find_form(s) : nullptr) {
        auto* r = f->AsReference();
        if (auto* a = r ? r->As<RE::Actor>() : nullptr) named.push_back(a);
        else return reply_error("actors", "no actor reference " + s);
      } else {
        try { radius = std::stod(s); } catch (...) { return reply_error("actors", "usage: actors [radius] [ref id...]"); }
      }
    }
    const auto from = p->GetPosition();
    std::string listed = "[";
    const std::pair<const char*, RE::BSTArray<RE::ActorHandle>*> sets[] = {
        {"high", &lists->highActorHandles}, {"middle_high", &lists->middleHighActorHandles},
        {"middle_low", &lists->middleLowActorHandles}, {"low", &lists->lowActorHandles}};
    int counts[4] = {0, 0, 0, 0};
    for (int i = 0; i < 4; ++i)
      for (auto& h : *sets[i].second) {
        auto a = h.get();
        if (!a) continue;
        ++counts[i];
        if (a->GetPosition().GetDistance(from) > radius) continue;
        if (listed.size() > 1) listed += ',';
        listed += actor_json(a.get(), from);
      }
    std::string refs = "[";
    for (auto* a : named) {
      if (refs.size() > 1) refs += ',';
      refs += actor_json(a, from);
    }
    return reply_ok("actors", JsonObject()
                                  .raw("switches", JsonObject()
                                                       .boolean("high", lists->processHigh)
                                                       .boolean("middle_high", lists->processMHigh)
                                                       .boolean("middle_low", lists->processMLow)
                                                       .boolean("low", lists->processLow)
                                                       .boolean("schedules", lists->runSchedules)
                                                       .boolean("movement", lists->runMovement)
                                                       .boolean("detection", lists->runDetection)
                                                       .done())
                                  .raw("counts", JsonObject().integer("high", counts[0]).integer("middle_high", counts[1])
                                                     .integer("middle_low", counts[2]).integer("low", counts[3]).done())
                                  .num("radius", radius)
                                  .raw("listed", listed + "]")
                                  .raw("refs", refs + "]")
                                  .done());
  });
}

// crime-gold <faction form id | editor id>: the player's crime gold with that faction (Papyrus Faction's
// GetCrimeGoldViolent / NonViolent). The console's GetCrimeGoldViolent takes no faction: it reads the calling
// actor's own value (diag2-dialogue-crime, 2026-10-30).
std::string crime_gold(const Request& req) {
  std::string want = rest(req);
  if (want.empty()) return reply_error("crime-gold", "usage: crime-gold <faction form id | editor id>");
  return on_main_thread("crime-gold", [want] {
    auto* f = find_form(want);
    auto* fac = f ? f->As<RE::TESFaction>() : nullptr;
    if (!fac) return reply_error("crime-gold", "no faction " + want);
    return reply_ok("crime-gold", JsonObject()
                                      .raw("faction", form_ref(fac))
                                      .integer("violent", fac->GetCrimeGoldViolent())
                                      .integer("nonviolent", fac->GetCrimeGoldNonViolent())
                                      .done());
  });
}

const Register r_actors{"actors", &actors};
const Register r_teleport{"teleport", &teleport};
const Register r_time{"time", &time_ep};
const Register r_weather{"weather", &weather};
const Register r_quest{"quest", &quest};
const Register r_quests{"quests", &quests};
const Register r_music{"music", &music};
const Register r_plugin{"plugin", &plugin};
const Register r_global{"global", &global};
const Register r_av{"av", &av};
const Register r_graph{"graph", &graph};
const Register r_inventory{"inventory", &inventory};
const Register r_crime_gold{"crime-gold", &crime_gold};

}  // namespace
}  // namespace argonia::bridge
