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

int main() {
  the_registry();
  a_hook_is_installed_once();
  one_handler_per_surface();
  death_runs_its_flow();
  return TEST_MAIN_RESULT("core.router");
}
