#include "argonia/core/router.h"

namespace argonia::core::router {

std::string_view name(SurfaceId s) { return gen::kSurfaceIdNames[std::size_t(s)]; }
std::string_view name(HookId h) { return gen::kHookIdNames[std::size_t(h)]; }
const gen::SurfaceRow& row(SurfaceId s) { return gen::kSurfaces[std::size_t(s)]; }

std::optional<SurfaceId> by_menu(std::string_view menu_name) {
  if (menu_name.empty()) return std::nullopt;
  for (std::size_t i = 0; i < gen::kSurfaces.size(); ++i)
    if (gen::kSurfaces[i].menu == menu_name) return SurfaceId(i);
  return std::nullopt;
}

bool Router::install(HookId h, std::string* why) {
  if (hooks_[std::size_t(h)]) {
    if (why) *why = "hook " + std::string(name(h)) + ": already installed; a system registers a handler, never a hook";
    return false;
  }
  hooks_[std::size_t(h)] = true;
  return true;
}

bool Router::handle(SurfaceId s, Handler h, std::string* why) {
  auto refuse = [&](const std::string& m) {
    if (why) *why = "surface " + std::string(name(s)) + ": " + m;
    return false;
  };
  const gen::SurfaceRow& r = row(s);
  if (!h) return refuse("an empty handler");
  if (r.replacement == Replacement::restyled) return refuse("restyled; the engine keeps it and it takes no handler");
  if (!installed(r.hook)) return refuse("its hook " + std::string(name(r.hook)) + " is not installed");
  if (handlers_[std::size_t(s)]) return refuse("already has a handler; one per surface");
  handlers_[std::size_t(s)] = std::move(h);
  return true;
}

Verdict Router::on_surface(SurfaceId s) const {
  Verdict v;
  v.surface = s;
  const gen::SurfaceRow& r = row(s);
  const Handler& h = handlers_[std::size_t(s)];
  switch (r.replacement) {
    case Replacement::restyled:
      return v;
    case Replacement::suppressed:
      v.action = Action::block;
      break;
    case Replacement::view:
      // Until the view's system lands the engine's surface shows, logged, rather than nothing at all.
      if (!h) {
        v.note = "surface " + std::string(name(s)) + ": our view " + std::string(r.by) + " is not registered yet";
        return v;
      }
      v.action = Action::block;
      break;
  }
  if (h) {
    h(s);
    v.handled = true;
  }
  return v;
}

Verdict Router::on_menu(std::string_view menu_name) const {
  const auto s = by_menu(menu_name);
  if (!s) {
    Verdict v;
    v.note = "menu '" + std::string(menu_name) + "' has no row in the router registry";
    return v;
  }
  return on_surface(*s);
}

std::vector<SurfaceId> Router::awaiting() const {
  std::vector<SurfaceId> out;
  for (std::size_t i = 0; i < gen::kSurfaces.size(); ++i)
    if (gen::kSurfaces[i].replacement == Replacement::view && !handlers_[i]) out.push_back(SurfaceId(i));
  return out;
}

std::vector<std::string> Router::load_log() const {
  std::vector<std::string> out;
  for (std::size_t i = 0; i < gen::kHookIdCount; ++i)
    if (hooks_[i]) out.push_back("hook " + std::string(gen::kHookIdNames[i]));
  for (std::size_t i = 0; i < gen::kSurfaceIdCount; ++i)
    if (handlers_[i]) out.push_back("handler " + std::string(gen::kSurfaceIdNames[i]));
  return out;
}

}  // namespace argonia::core::router
