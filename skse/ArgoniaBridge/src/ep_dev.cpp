// The dev setters and the reads 1.7's journeys owed (lane bridge-gaps; DEV ONLY, the setters live in ArgoniaCore only for SetSkill, under ARGONIA_DEV_NATIVES):
//   dev-set <Native> [text] <n>   SetAttribute / SetVastei / SetSkill (the dev ArgoniaDev.SetSkill) through the Papyrus VM, ArgoniaCore's own natives, so their
//                                 clamps apply; the stored value comes back. Scene inputs at step 0 only.
//   dev-grow <ref> <n> [max]      landed blows (hit events into ArgoniaCore's own sink, the target's health lowered
//                                 first so the blow has damage) until GetPendingLevels >= n; the blow count comes back
//   tdm-target                    TrueDirectionalMovement's lock state and current target (its plugin API, V1)
//   refs <base> [radius]          the references of a base form in the form map (the vastei pile count); with a
//                                 radius, only those within it of the player (a scene's placed props)
//   ini <name:Section>            an INI setting as the game holds it (prefs first, then Skyrim.ini)
//   ltex                          the land texture under the player
//   logfile <name> <text>         an SKSE log beside ours: its line count and the lines containing the text
//   trace start <frames> [var..]  arms a per-frame trace of the player (position, health, ghost or any named graph
//   trace read [samples]          bool true = an i-frame); read gives the window (first/last i-frame frame)
#include "bridge.h"
#include "dev.h"
#include "argonia/core/bridge_call.h"

namespace argonia::bridge {
namespace {
using namespace argonia::bridge::dev;

RE::TESForm* find_any(std::string_view s) {
  if (s.starts_with("0x") || s.starts_with("0X") || s.size() == 8)
    if (auto id = to_form_id(s)) return RE::TESForm::LookupByID(*id);
  return RE::TESForm::LookupByEditorID(s);
}

std::string ref_json(const RE::TESForm* f) {
  if (!f) return "null";
  return JsonObject().hex("id", f->GetFormID()).str("editor_id", f->GetFormEditorID()).str("name", f->GetName()).done();
}

// ArgoniaCore's `core` read, for dev-grow's loop (the same message the `core` endpoint sends).
std::optional<double> core_number(const char* native) {
  namespace bc = argonia::core::bridge_call;
  auto m = std::make_unique<bc::BridgeCore>();
  std::string(native).copy(m->native, sizeof(m->native) - 1);
  if (!SKSE::GetMessagingInterface()->Dispatch(bc::kBridgeCoreMessage, m.get(), sizeof(*m), "ArgoniaCore") || !m->ok)
    return std::nullopt;
  std::string_view j = m->json;
  auto at = j.find("\"value\":");
  if (at == std::string_view::npos) return std::nullopt;
  auto tail = j.substr(at + 8);
  return to_number(tail.substr(0, tail.find_first_of(",}")));
}

// --- dev-set ---------------------------------------------------------------------------------------------------
class FloatResult final : public RE::BSScript::IStackCallbackFunctor {
 public:
  explicit FloatResult(std::shared_ptr<std::promise<float>> p) : p_(std::move(p)) {}
  void operator()(RE::BSScript::Variable r) override { p_->set_value(r.IsFloat() ? r.GetFloat() : -1.0f); }
  void SetObject(const RE::BSTSmartPointer<RE::BSScript::Object>&) override {}

 private:
  std::shared_ptr<std::promise<float>> p_;
};

std::string dev_set(const Request& req) {
  auto parsed = set_call(req);
  if (auto* why = std::get_if<std::string>(&parsed)) return reply_error("dev-set", *why);
  auto call = std::get<SetCall>(parsed);
  auto done = std::make_shared<std::promise<float>>();
  auto value = done->get_future();
  auto sent = on_main_thread("dev-set", [call, done] {
    auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton();
    if (!vm || !player_in_world()) return reply_error("dev-set", "no Papyrus VM or no player in a world");
    RE::BSTSmartPointer<RE::BSScript::IStackCallbackFunctor> cb(new FloatResult(done));
    auto* args = call.text ? RE::MakeFunctionArguments(RE::BSFixedString(*call.text), static_cast<float>(call.value))
                           : RE::MakeFunctionArguments(static_cast<float>(call.value));
    if (!vm->DispatchStaticCall(call.native == "SetSkill" ? "ArgoniaDev" : "ArgoniaCore", call.native.c_str(), args, cb))
      return reply_error("dev-set", "the VM refused " + call.native + " (ArgoniaCore.pex / ArgoniaDev.pex not loaded?)");
    return reply_ok("dev-set", "true");
  });
  if (sent.find("\"ok\":true") == std::string::npos) return sent;
  if (value.wait_for(5s) != std::future_status::ready) return reply_error("dev-set", "the native did not return within 5 s");
  const float stored = value.get();
  JsonObject o;
  o.str("native", call.native);
  if (call.text) o.str("name", *call.text);
  return reply_ok("dev-set", o.num("asked", call.value).num("value", stored).done());
}

// --- dev-grow --------------------------------------------------------------------------------------------------
std::string dev_grow(const Request& req) {
  auto parsed = grow_call(req);
  if (auto* why = std::get_if<std::string>(&parsed)) return reply_error("dev-grow", *why);
  auto g = std::get<GrowCall>(parsed);
  int blows = 0;
  double pending = 0;
  for (int batch = 0; blows < g.max_blows; ++batch) {
    auto r = on_main_thread("dev-grow", [&g, &blows, &pending] {
      auto* p = player_in_world();
      auto* f = find_any(g.target);
      auto* ref = f ? f->AsReference() : nullptr;
      auto* target = ref ? ref->As<RE::Actor>() : nullptr;
      if (!p || !target || target->IsDead()) return reply_error("dev-grow", "no player, or no living actor " + g.target);
      auto* weap = p->GetEquippedObject(false);
      auto* src = RE::ScriptEventSourceHolder::GetSingleton();
      if (!src) return reply_error("dev-grow", "no script event source");
      auto* avo = target->AsActorValueOwner();
      for (int i = 0; i < 10 && blows < g.max_blows; ++i, ++blows) {
        if (avo->GetActorValue(RE::ActorValue::kHealth) < 0.5f * avo->GetPermanentActorValue(RE::ActorValue::kHealth))
          target->RestoreActorValue(RE::ActorValue::kHealth, avo->GetPermanentActorValue(RE::ActorValue::kHealth));
        target->DamageActorValue(RE::ActorValue::kHealth, 20.0f);
        RE::TESHitEvent ev(target, p, weap ? weap->GetFormID() : 0, 0, RE::TESHitEvent::Flag::kNone);
        src->SendEvent(&ev);
      }
      pending = core_number("GetPendingLevels").value_or(-1);
      return reply_ok("dev-grow", "true");
    });
    if (r.find("\"ok\":true") == std::string::npos) return r;
    if (pending < 0) return reply_error("dev-grow", "ArgoniaCore did not answer GetPendingLevels");
    if (pending >= g.pending) break;
  }
  if (pending < g.pending)
    return reply_error("dev-grow", std::to_string(blows) + " blows left GetPendingLevels at " + json_number(pending));
  return reply_ok("dev-grow", JsonObject().integer("blows", blows).num("pending", pending).done());
}

// --- tdm-target ------------------------------------------------------------------------------------------------
// TrueDirectionalMovement's public API (its TrueDirectionalMovementAPI.h, interface V1): the first three entries.
namespace tdm {
class IVTDM1 {
 public:
  virtual bool GetDirectionalMovementState() noexcept = 0;
  virtual bool GetTargetLockState() noexcept = 0;
  virtual RE::ActorHandle GetCurrentTarget() noexcept = 0;
};
using Request = void* (*)(std::uint8_t version, SKSE::PluginHandle handle);
IVTDM1* api() {
  static IVTDM1* got = nullptr;
  if (got) return got;
  auto* mod = GetModuleHandleW(L"TrueDirectionalMovement.dll");
  auto fn = mod ? reinterpret_cast<Request>(GetProcAddress(mod, "RequestPluginAPI")) : nullptr;
  if (fn) got = static_cast<IVTDM1*>(fn(0, SKSE::GetPluginHandle()));
  return got;
}
}  // namespace tdm

std::string tdm_target(const Request&) {
  return on_main_thread("tdm-target", [] {
    auto* p = player_in_world();
    if (!p) return reply_error("tdm-target", "no player in a world");
    auto* api = tdm::api();
    if (!api) return reply_error("tdm-target", "TrueDirectionalMovement.dll gave no API (not loaded?)");
    auto t = api->GetCurrentTarget().get();
    return reply_ok("tdm-target", JsonObject()
                                      .boolean("directional", api->GetDirectionalMovementState())
                                      .boolean("locked", api->GetTargetLockState())
                                      .raw("target", t ? ref_json(t.get()) : "null")
                                      .num("dist", t ? t->GetPosition().GetDistance(p->GetPosition()) : -1.0)
                                      .done());
  });
}

// --- refs ------------------------------------------------------------------------------------------------------
std::string refs(const Request& req) {
  if (req.args.empty() || req.args.size() > 2) return reply_error("refs", "usage: refs <base form id | editor id> [radius]");
  std::string base = req.args[0];
  std::optional<double> radius;
  if (req.args.size() == 2 && !(radius = to_number(req.args[1]))) return reply_error("refs", "the radius is a number");
  return on_main_thread("refs", [base, radius] {
    auto* b = find_any(base);
    auto* p = player_in_world();
    if (radius && !p) return reply_error("refs", "no player in a world for the radius");
    if (!b) return reply_error("refs", "no base form " + base);
    std::string list = "[";
    long long count = 0, enabled = 0;
    {
      const auto& [map, lock] = RE::TESForm::GetAllForms();
      RE::BSReadLockGuard g(lock);
      for (auto& [id, form] : *map) {
        auto* r = form ? form->AsReference() : nullptr;
        if (!r || r->GetBaseObject() != b || r->IsDeleted()) continue;
        if (radius && (r->GetParentCell() != p->GetParentCell() && r->GetWorldspace() != p->GetWorldspace())) continue;
        if (radius && r->GetPosition().GetDistance(p->GetPosition()) > *radius) continue;
        ++count;
        if (!r->IsDisabled()) ++enabled;
        if (count <= 20) {
          auto pos = r->GetPosition();
          if (list.size() > 1) list += ',';
          list += JsonObject().hex("ref", r->GetFormID()).boolean("disabled", r->IsDisabled())
                      .num("x", pos.x).num("y", pos.y).num("z", pos.z).done();
        }
      }
    }
    return reply_ok("refs", JsonObject().raw("base", ref_json(b)).integer("count", count).integer("enabled", enabled)
                                .raw("refs", list + "]").done());
  });
}

// --- ini -------------------------------------------------------------------------------------------------------
std::string ini(const Request& req) {
  std::string name = rest(req);
  if (!valid_ini_name(name)) return reply_error("ini", "usage: ini <name:Section> (e.g. bShowCompass:Interface)");
  return on_main_thread("ini", [name] {
    RE::Setting* s = nullptr;
    const char* from = "";
    if (auto* prefs = RE::INIPrefSettingCollection::GetSingleton(); prefs && (s = prefs->GetSetting(name))) from = "SkyrimPrefs.ini";
    else if (auto* main = RE::INISettingCollection::GetSingleton(); main && (s = main->GetSetting(name))) from = "Skyrim.ini";
    if (!s) return reply_error("ini", "the game holds no setting " + name);
    std::string v;
    switch (name[0]) {
      case 'b': v = s->GetBool() ? "true" : "false"; break;
      case 'f': v = json_number(s->GetFloat()); break;
      case 'i': v = std::to_string(s->GetInteger()); break;
      case 'u': v = std::to_string(s->GetUnsignedInteger()); break;
      case 's': v = json_string(s->GetString() ? s->GetString() : ""); break;
      default: return reply_error("ini", "an INI name starts with b, f, i, u or s");
    }
    return reply_ok("ini", JsonObject().str("name", name).str("file", from).raw("value", v).done());
  });
}

// --- ltex ------------------------------------------------------------------------------------------------------
std::string ltex(const Request&) {
  return on_main_thread("ltex", [] {
    auto* p = player_in_world();
    auto* tes = RE::TES::GetSingleton();
    if (!p || !tes) return reply_error("ltex", "no player in a world");
    if (p->GetParentCell()->IsInteriorCell()) return reply_error("ltex", "the player is indoors: no land");
    auto pos = p->GetPosition();
    auto* t = tes->GetLandTexture(pos);
    return reply_ok("ltex", JsonObject().raw("texture", ref_json(t)).boolean("default", t == nullptr)
                                .raw("pos", JsonObject().num("x", pos.x).num("y", pos.y).num("z", pos.z).done()).done());
  });
}

// --- logfile ---------------------------------------------------------------------------------------------------
std::string logfile(const Request& req) {
  if (req.args.size() < 2 || !valid_log_name(req.args[0])) return reply_error("logfile", "usage: logfile <SKSE log name> <text>");
  auto dir = SKSE::log::log_directory();
  if (!dir) return reply_error("logfile", "no SKSE log directory");
  std::ifstream f(*dir / (req.args[0] + ".log"), std::ios::binary);
  if (!f) return reply_error("logfile", "no log " + req.args[0] + ".log");
  std::string text((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
  auto m = log_match(text, rest(req, 1));
  return reply_ok("logfile", JsonObject().str("name", req.args[0]).integer("lines", m.lines).integer("matches", m.matches)
                                 .boolean("found", m.matches > 0).str("first", m.first).done());
}

// --- trace -----------------------------------------------------------------------------------------------------
std::mutex g_tm;
std::vector<Sample> g_samples;
std::vector<std::string> g_vars;
long long g_left = 0, g_frame = 0;
std::chrono::steady_clock::time_point g_t0;

std::string trace(const Request& req) {
  const std::string usage = "usage: trace start <frames 10..1200> [graph bool...] | trace read [samples]";
  if (req.args.empty()) return reply_error("trace", usage);
  std::scoped_lock l(g_tm);
  if (req.args[0] == "start") {
    auto n = req.args.size() > 1 ? to_number(req.args[1]) : std::nullopt;
    if (!n || *n < 10 || *n > kTraceMaxFrames) return reply_error("trace", usage);
    g_samples.clear();
    g_vars.assign(req.args.begin() + 2, req.args.end());
    g_left = static_cast<long long>(*n);
    g_frame = 0;
    g_t0 = std::chrono::steady_clock::now();
    return reply_ok("trace", JsonObject().integer("armed", g_left).done());
  }
  if (req.args[0] == "read") {
    auto j = trace_json(g_samples, g_vars, req.args.size() > 1 && req.args[1] == "samples");
    return reply_ok("trace", j.substr(0, j.size() - 1) + ",\"running\":" + (g_left > 0 ? "true" : "false") + "}");
  }
  return reply_error("trace", usage);
}

const Register r_dev_set{"dev-set", &dev_set};
const Register r_dev_grow{"dev-grow", &dev_grow};
const Register r_tdm{"tdm-target", &tdm_target};
const Register r_refs{"refs", &refs};
const Register r_ini{"ini", &ini};
const Register r_ltex{"ltex", &ltex};
const Register r_logfile{"logfile", &logfile};
const Register r_trace{"trace", &trace};

}  // namespace

// Called by the player's per-frame update (ep_input.cpp), on the main thread.
void trace_frame(RE::PlayerCharacter* p) {
  std::scoped_lock l(g_tm);
  if (g_left <= 0) return;
  --g_left;
  Sample s;
  s.frame = g_frame++;
  s.ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - g_t0).count();
  auto pos = p->GetPosition();
  s.x = pos.x, s.y = pos.y, s.z = pos.z;
  s.health = p->AsActorValueOwner()->GetActorValue(RE::ActorValue::kHealth);
  s.ghost = p->IsGhost();
  for (const auto& v : g_vars) {
    bool b = false;
    p->GetGraphVariableBool(v, b);
    s.vars.push_back(b);
    s.ghost = s.ghost || b;
  }
  g_samples.push_back(std::move(s));
}

}  // namespace argonia::bridge
