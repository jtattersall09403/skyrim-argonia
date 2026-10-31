// L2: the menu router (1.1 §d): the registry lists every kind of surface and 1.3 §b's dialogue intercept; a hook is
// installed once and a second registration of it is refused (S10a); one handler per surface; the verdicts for a
// view, a suppressed, a restyled and an unlisted surface.
#include "check.h"
#include "argonia/core/router.h"

#include <set>
#include <string>

using namespace argonia::core;
using namespace argonia::core::router;

namespace {

bool contains(const std::string& s, std::string_view part) { return s.find(part) != std::string::npos; }

void the_registry() {
  std::set<SurfaceKind> kinds;
  for (const auto& r : gen::kSurfaces) kinds.insert(r.kind);
  CHECK(kinds.size() == gen::kSurfaceKindCount);  // menus, dialogue, death, level-up, the HUD, notifications
  const auto d = by_menu("Dialogue Menu");
  CHECK(d && *d == SurfaceId::dialogueMenu);
  CHECK(row(SurfaceId::dialogueMenu).hook == HookId::dialogueIntercept);
  CHECK(row(SurfaceId::dialogueMenu).chunk == "1.3 §b" && row(SurfaceId::dialogueMenu).replacement == Replacement::view);
  CHECK(row(SurfaceId::playerDeath).hook == HookId::deathIntercept);
  CHECK(row(SurfaceId::levelUpMenu).replacement == Replacement::suppressed);
  CHECK(row(SurfaceId::hudCompass).replacement == Replacement::suppressed);
  CHECK(!by_menu("") && !by_menu("No Such Menu"));
}

void a_hook_is_installed_once() {
  Router r;
  std::string why;
  CHECK(r.install(HookId::dialogueIntercept, &why));
  CHECK(!r.install(HookId::dialogueIntercept, &why));  // S10a: the second registration is refused
  CHECK(contains(why, "hook dialogueIntercept: already installed"));
  CHECK(r.load_log() == std::vector<std::string>{"hook dialogueIntercept"});
}

void one_handler_per_surface() {
  Router r;
  std::string why;
  int opened = 0;
  Handler open = [&](SurfaceId) { ++opened; };
  CHECK(!r.handle(SurfaceId::dialogueMenu, open, &why) && contains(why, "dialogueIntercept is not installed"));
  CHECK(r.install(HookId::dialogueIntercept));
  CHECK(r.handle(SurfaceId::dialogueMenu, open, &why));
  CHECK(!r.handle(SurfaceId::dialogueMenu, open, &why) && contains(why, "already has a handler"));
  CHECK(r.install(HookId::menuOpenClose));
  CHECK(!r.handle(SurfaceId::inventoryMenu, open, &why) && contains(why, "restyled"));
  CHECK(!r.handle(SurfaceId::journalMenu, Handler{}, &why) && contains(why, "an empty handler"));

  Verdict v = r.on_menu("Dialogue Menu");
  CHECK(v.action == Action::block && v.handled && opened == 1 && v.surface == SurfaceId::dialogueMenu);
  v = r.on_menu("InventoryMenu");  // restyled: the engine keeps it
  CHECK(v.action == Action::pass && !v.handled && v.note.empty());
  v = r.on_menu("Journal Menu");  // our view, not landed yet: shown and logged
  CHECK(v.action == Action::pass && contains(v.note, "our view journal is not registered yet"));
  v = r.on_menu("Tutorial Menu");  // suppressed needs no handler
  CHECK(v.action == Action::block && !v.handled);
  v = r.on_menu("Some Mod Menu");
  CHECK(v.action == Action::pass && !v.surface && contains(v.note, "no row in the router registry"));

  const auto waiting = r.awaiting();
  CHECK(std::find(waiting.begin(), waiting.end(), SurfaceId::journalMenu) != waiting.end());
  CHECK(std::find(waiting.begin(), waiting.end(), SurfaceId::dialogueMenu) == waiting.end());
  const auto log = r.load_log();
  CHECK(log.size() == 3 && log.back() == "handler dialogueMenu");
}

void death_runs_its_flow() {
  Router r;
  bool respawned = false;
  CHECK(r.install(HookId::deathIntercept));
  CHECK(r.handle(SurfaceId::playerDeath, [&](SurfaceId s) { respawned = s == SurfaceId::playerDeath; }));
  Verdict v = r.on_surface(SurfaceId::playerDeath);
  CHECK(v.action == Action::block && v.handled && respawned);
}

}  // namespace

void intents_reach_their_view() {
  CHECK(intent_view(R"({"type":"sitting.buy","v":1,"body":{"attribute":"endurance"}})").value_or("") == "sitting");
  CHECK(intent_view(R"({"type":"sitting.done","v":1,"body":{}})").value_or("") == "sitting");
  CHECK(intent_view(R"({"type":"dialogue.goodbye","v":1,"body":{}})").value_or("") == "dialogue");
  CHECK(intent_view(R"({"type":"view.close","v":1,"body":{"view":"journal"}})").value_or("") == "journal");
  CHECK(!intent_view(R"({"type":"sitting.state","v":1,"body":{}})"));  // a push is never an intent
  CHECK(!intent_view("not json"));
  CHECK(!intent_view(R"({"type":"sitting.buy","v":1,"body":{"attribute":"luck"}})"));  // no Luck
}

// 1.2 §d: the vanilla bars and the compass are hidden through their rows; no restyled row's clip is.
void vanilla_hud_hidden() {
  CHECK((hidden_hud_clips() == std::vector<std::string_view>{"Health", "Magica", "Stamina", "CompassShoutMeterHolder"}));
  bool bars = false, compass = false;
  for (const auto& c : kHudClips) {
    CHECK(row(c.surface).kind == SurfaceKind::hud && row(c.surface).hook == HookId::hudElements);
    CHECK(row(c.surface).replacement != Replacement::restyled);
    bars |= c.surface == SurfaceId::hudBars;
    compass |= c.surface == SurfaceId::hudCompass;
  }
  CHECK(bars && compass);
  CHECK(row(SurfaceId::hudBars).replacement == Replacement::view && row(SurfaceId::hudBars).by == "hud");

  // game-10: the list held 22 entries and none matched by mark; any one of identity, mark or name takes it out.
  const auto hidden = hidden_hud_clips();
  std::vector<HudListEntry> list(22);
  list[2].same_object = true;
  list[5].marked = true;
  list[9].name = "CompassShoutMeterHolder";
  list[11].name = "Crosshair";  // a restyled clip stays
  CHECK((hud_list_removals(list, hidden) == std::vector<std::uint32_t>{9, 5, 2}));  // highest first
  CHECK(hud_list_removals(std::vector<HudListEntry>(22), hidden).empty());
  // The mode flags SetMode reads: every known mode, a mod's new ...Mode, never a clip's own members.
  for (auto m : kHudModes) CHECK(is_hud_mode(m));
  CHECK(is_hud_mode("FishingMode") && is_hud_mode("VATSPlayback"));
  CHECK(!is_hud_mode("Mode") && !is_hud_mode("_visible") && !is_hud_mode("argoniaHidden") && !is_hud_mode("onModeChange"));
}

void sheets_cover_the_hud() {
  CHECK(covers_hud("BarterMenu") && covers_hud("ContainerMenu") && covers_hud("InventoryMenu") && covers_hud("TweenMenu") && covers_hud("Book Menu"));
  CHECK(covers_hud("Journal Menu") && covers_hud("Sleep/Wait Menu"));
  CHECK(!covers_hud("FavoritesMenu") && !covers_hud("MessageBoxMenu") && !covers_hud("Quantity Menu"));
  CHECK(!covers_hud("TrueHUD") && !covers_hud("Fader Menu") && !covers_hud("HUD Menu") && !covers_hud(""));
}

int main() {
  sheets_cover_the_hud();
  vanilla_hud_hidden();
  intents_reach_their_view();
  the_registry();
  a_hook_is_installed_once();
  one_handler_per_surface();
  death_runs_its_flow();
  return TEST_MAIN_RESULT("core.router");
}
