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

// quest <form id | editor id>: its stage and state.
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
                                 .boolean("running", quest->IsRunning())
                                 .boolean("enabled", quest->IsEnabled())
                                 .boolean("completed", quest->IsCompleted())
                                 .done());
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

RE::Actor* actor_arg(const Request& req, std::size_t i, std::string& err) {
  if (req.args.size() <= i || req.args[i] == "player") {
    auto* p = player_in_world();
    if (!p) err = "no player in a world (main menu or loading)";
    return p;
  }
  auto* f = find_form(req.args[i]);
  auto* r = f ? f->AsReference() : nullptr;
  auto* a = r ? r->As<RE::Actor>() : nullptr;
  if (!a) err = "no actor reference " + req.args[i];
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

const Register r_teleport{"teleport", &teleport};
const Register r_time{"time", &time_ep};
const Register r_weather{"weather", &weather};
const Register r_quest{"quest", &quest};
const Register r_global{"global", &global};
const Register r_av{"av", &av};
const Register r_inventory{"inventory", &inventory};

}  // namespace
}  // namespace argonia::bridge
