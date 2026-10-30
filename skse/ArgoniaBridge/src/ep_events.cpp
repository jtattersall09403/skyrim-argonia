// Events (0.3 §a): hits, the player's animation events, quest stages and menus, each with a sequence number, the
// real time since the plugin loaded and the game time, in a ring of the last 4096. A journey reads them with
// `events <since>` or blocks on one with `wait_event` (its expectation with a timeout).
#include "bridge.h"

namespace argonia::bridge {
namespace {

struct Event {
  std::uint64_t seq;
  std::string kind;  // hit | anim | quest | menu | mod
  std::string match;  // what wait_event matches: the anim tag, the quest id, the menu name, the hit target id, the
                      // mod event's name (ArgoniaJournalNotice: ArgoniaCore's "journal updated" notice)
  std::string json;   // the whole event, a JSON object
};

constexpr std::size_t kRing = 4096;
std::mutex g_m;
std::condition_variable g_cv;
std::deque<Event> g_ring;
std::uint64_t g_seq = 0;
const auto g_t0 = std::chrono::steady_clock::now();

void push(std::string kind, std::string match, JsonObject fields) {
  auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - g_t0).count();
  auto* cal = RE::Calendar::GetSingleton();
  float game_days = cal ? cal->GetCurrentGameTime() : 0.0f;
  {
    std::scoped_lock l(g_m);
    ++g_seq;
    auto json = JsonObject().integer("seq", static_cast<long long>(g_seq)).str("kind", kind).integer("t_ms", ms)
                    .num("game_days", game_days).raw("data", fields.done()).done();
    g_ring.push_back(Event{g_seq, std::move(kind), std::move(match), std::move(json)});
    if (g_ring.size() > kRing) g_ring.pop_front();
  }
  g_cv.notify_all();
}

std::string hex(std::uint32_t id) {
  char b[16];
  std::snprintf(b, sizeof b, "%08X", static_cast<unsigned>(id));
  return b;
}

struct Sinks : RE::BSTEventSink<RE::TESHitEvent>,
               RE::BSTEventSink<RE::TESQuestStageEvent>,
               RE::BSTEventSink<RE::MenuOpenCloseEvent>,
               RE::BSTEventSink<RE::BSAnimationGraphEvent>,
               RE::BSTEventSink<SKSE::ModCallbackEvent>,
               RE::BSTEventSink<SKSE::CrosshairRefEvent> {
  RE::BSEventNotifyControl ProcessEvent(const RE::TESHitEvent* e, RE::BSTEventSource<RE::TESHitEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    auto t = e->target ? e->target->GetFormID() : 0, c = e->cause ? e->cause->GetFormID() : 0;
    push("hit", hex(t), JsonObject().hex("target", t).hex("cause", c).hex("source", e->source)
                            .hex("projectile", e->projectile)
                            .boolean("power", e->flags.any(RE::TESHitEvent::Flag::kPowerAttack))
                            .boolean("blocked", e->flags.any(RE::TESHitEvent::Flag::kHitBlocked)));
    return RE::BSEventNotifyControl::kContinue;
  }
  RE::BSEventNotifyControl ProcessEvent(const RE::TESQuestStageEvent* e, RE::BSTEventSource<RE::TESQuestStageEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    auto* q = RE::TESForm::LookupByID(e->formID);
    push("quest", hex(e->formID), JsonObject().hex("quest", e->formID).str("editor_id", q ? q->GetFormEditorID() : "")
                                      .integer("stage", e->stage));
    return RE::BSEventNotifyControl::kContinue;
  }
  RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* e, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    push("menu", e->menuName.c_str(), JsonObject().str("menu", e->menuName.c_str()).boolean("opening", e->opening));
    return RE::BSEventNotifyControl::kContinue;
  }
  RE::BSEventNotifyControl ProcessEvent(const RE::BSAnimationGraphEvent* e, RE::BSTEventSource<RE::BSAnimationGraphEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    push("anim", e->tag.c_str(), JsonObject().str("tag", e->tag.c_str()).str("payload", e->payload.c_str())
                                     .hex("holder", e->holder ? e->holder->GetFormID() : 0));
    return RE::BSEventNotifyControl::kContinue;
  }
  RE::BSEventNotifyControl ProcessEvent(const SKSE::ModCallbackEvent* e, RE::BSTEventSource<SKSE::ModCallbackEvent>*) override {
    if (!e) return RE::BSEventNotifyControl::kContinue;
    push("mod", e->eventName.c_str(), JsonObject().str("event", e->eventName.c_str()).str("str", e->strArg.c_str())
                                          .num("num", e->numArg));
    return RE::BSEventNotifyControl::kContinue;
  }
  // SKSE's crosshair event: the ref under the crosshair (none: 0), kept for the `crosshair` read; not in the ring.
  RE::BSEventNotifyControl ProcessEvent(const SKSE::CrosshairRefEvent* e, RE::BSTEventSource<SKSE::CrosshairRefEvent>*) override {
    crosshair.store(e && e->crosshairRef ? e->crosshairRef->GetFormID() : 0);
    return RE::BSEventNotifyControl::kContinue;
  }
  std::atomic<RE::FormID> crosshair{0};
};
Sinks g_sinks;

// crosshair: the reference under the player's crosshair (SKSE's crosshair event), or null; the `talk` action waits
// on it before E (diag2-dialogue-crime: an NPC under AI walked out of the crosshair before the key).
std::string crosshair(const Request&) {
  return on_main_thread("crosshair", [] {
    auto id = g_sinks.crosshair.load();
    auto* f = id ? RE::TESForm::LookupByID(id) : nullptr;
    auto* p = RE::PlayerCharacter::GetSingleton();
    auto* r = f ? f->AsReference() : nullptr;
    std::string ref = f ? JsonObject().hex("id", id).str("editor_id", f->GetFormEditorID()).str("name", r ? r->GetDisplayFullName() : f->GetName()).done()
                        : "null";
    return reply_ok("crosshair", JsonObject().raw("ref", ref)
                                     .num("dist", r && p ? r->GetPosition().GetDistance(p->GetPosition()) : -1.0)
                                     .done());
  });
}
const Register r_crosshair{"crosshair", &crosshair};

std::string events(const Request& req) {
  std::uint64_t since = 0;
  if (!req.args.empty()) {
    auto n = to_number(req.args[0]);
    if (!n || *n < 0) return reply_error("events", "usage: events [since seq] [kind]");
    since = static_cast<std::uint64_t>(*n);
  }
  std::string kind = req.args.size() > 1 ? req.args[1] : "";
  std::string list = "[";
  std::uint64_t last = 0;
  std::size_t n = 0;
  {
    std::scoped_lock l(g_m);
    last = g_seq;
    for (auto& e : g_ring) {
      if (e.seq <= since || (!kind.empty() && e.kind != kind)) continue;
      if (++n > 1000) break;
      if (list.size() > 1) list += ',';
      list += e.json;
    }
  }
  return reply_ok("events", JsonObject().integer("last", static_cast<long long>(last)).raw("events", list + "]").done());
}

// wait_event <kind> <match | *> <timeout ms> [since]: the first such event after `since` (default: now), or an
// error when the timeout passes; a journey's expectation that can fail.
std::string wait_event(const Request& req) {
  if (req.args.size() < 3) return reply_error("wait_event", "usage: wait_event <kind> <match|*> <timeout ms> [since]");
  auto ms = to_number(req.args[2]);
  if (!ms || *ms < 0 || *ms > 60000) return reply_error("wait_event", "the timeout must be 0..60000 ms");
  const auto& kind = req.args[0];
  const auto& match = req.args[1];
  std::unique_lock l(g_m);
  std::uint64_t since = g_seq;
  if (req.args.size() > 3) {
    auto s = to_number(req.args[3]);
    if (!s || *s < 0) return reply_error("wait_event", "since must be a sequence number");
    since = static_cast<std::uint64_t>(*s);
  }
  const Event* hit = nullptr;
  auto found = [&] {
    for (auto& e : g_ring)
      if (e.seq > since && e.kind == kind && (match == "*" || _stricmp(e.match.c_str(), match.c_str()) == 0)) {
        hit = &e;
        return true;
      }
    return false;
  };
  if (!g_cv.wait_for(l, std::chrono::milliseconds(static_cast<long long>(*ms)), found))
    return reply_error("wait_event", "no " + kind + " event matching " + match + " within " + req.args[2] + " ms");
  return reply_ok("wait_event", hit->json);
}

const Register r_events{"events", &events};
const Register r_wait{"wait_event", &wait_event};

}  // namespace

void events_install() {
  if (auto* h = RE::ScriptEventSourceHolder::GetSingleton()) {
    h->AddEventSink<RE::TESHitEvent>(&g_sinks);
    h->AddEventSink<RE::TESQuestStageEvent>(&g_sinks);
  }
  if (auto* ui = RE::UI::GetSingleton()) ui->AddEventSink<RE::MenuOpenCloseEvent>(&g_sinks);
  if (auto* mods = SKSE::GetModCallbackEventSource()) mods->AddEventSink(&g_sinks);
  if (auto* cross = SKSE::GetCrosshairRefEventSource()) cross->AddEventSink(&g_sinks);
}

// The player's animation graph is rebuilt by every load, so its sink is re-added (main thread).
void events_on_game_loaded() {
  if (auto* p = RE::PlayerCharacter::GetSingleton()) {
    p->RemoveAnimationGraphEventSink(&g_sinks);
    p->AddAnimationGraphEventSink(&g_sinks);
  }
}

}  // namespace argonia::bridge
