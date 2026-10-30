// The menu router (1.1 §d, native map P6) as pure logic: the registry of every vanilla surface Argonia takes over
// (data/router/surfaces.json, generated into gen::kSurfaces), the hooks installed once, one handler per surface,
// and the verdict for each surface the engine shows. ArgoniaCore's adapter installs the real hooks and acts on the
// verdict (closing a blocked menu); none of that is here, so the rules are tested on Linux.
#pragma once
#include "argonia/core/messages.h"
#include "argonia/core/router_table.h"

#include <expected>

#include <array>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::router {

using gen::HookId;
using gen::Replacement;
using gen::SurfaceId;
using gen::SurfaceKind;

using Handler = std::function<void(SurfaceId)>;

std::string_view name(SurfaceId s);
std::string_view name(HookId h);
const gen::SurfaceRow& row(SurfaceId s);
std::optional<SurfaceId> by_menu(std::string_view menu_name);  // the surface whose engine menu this is

enum class Action : std::uint8_t {
  pass,   // let the engine show it (restyled, unlisted, or our view not landed yet)
  block,  // close it at once; the handler, if any, has run
};

struct Verdict {
  Action action = Action::pass;
  std::optional<SurfaceId> surface;  // empty: the menu has no row (the L4 sweep lists these)
  bool handled = false;              // a handler ran
  std::string note;                  // one line for the SKSE log when the verdict is not the plain case
};

class Router {
 public:
  // Each hook is installed once; a second install is refused with a readable reason (S10a).
  bool install(HookId h, std::string* why = nullptr);
  bool installed(HookId h) const { return hooks_[std::size_t(h)]; }

  // One handler per surface, on a hook already installed; a restyled surface takes none (the engine keeps it).
  bool handle(SurfaceId s, Handler h, std::string* why = nullptr);
  bool has_handler(SurfaceId s) const { return bool(handlers_[std::size_t(s)]); }

  // What to do when the engine opens `menu_name` (MenuOpenCloseEvent) or reaches a non-menu surface.
  Verdict on_menu(std::string_view menu_name) const;
  Verdict on_surface(SurfaceId s) const;

  // Surfaces whose replacement is our view but whose system has not registered yet.
  std::vector<SurfaceId> awaiting() const;
  // The load log: each installed hook, then each handled surface (S11a reads it against the native map's list).
  std::vector<std::string> load_log() const;

 private:
  std::array<bool, gen::kHookIdCount> hooks_{};
  std::array<Handler, gen::kSurfaceIdCount> handlers_{};
};

// The vanilla HUD's clips (1.2 §d): hudmenu.swf's instance names under kHudRoot, as HUD mods (iHUD, SkyHUD)
// address them, for the HUD rows that hide something. ArgoniaCore hides each clip of a row that is suppressed or our
// view and takes it out of the movie's HudElements list, so the HUD's mode changes never show it again; the movie
// itself stays (the crosshair and subtitles are restyled rows).
struct HudClip {
  SurfaceId surface;
  std::string_view clip;
};
inline constexpr std::string_view kHudRoot = "_root.HUDMovieBaseInstance";
inline constexpr std::array<HudClip, 4> kHudClips{{
    {SurfaceId::hudBars, "Health"},
    {SurfaceId::hudBars, "Magica"},
    {SurfaceId::hudBars, "Stamina"},
    {SurfaceId::hudCompass, "CompassShoutMeterHolder"},  // the compass and the shout meter share the holder
}};
// The clips to hide: those whose row is not restyled, in table order.
std::vector<std::string_view> hidden_hud_clips();

// The view an intent is for (dialogue, journal, chart, sitting), from its type, so every view's intents reach
// ArgoniaCore through one listener (the web view's window.argoniaIntent) and are routed here; view.close names
// its view. A refusal is the schema twin's words (a malformed intent, a push sent as an intent).
std::expected<std::string_view, std::string> intent_view(std::string_view json);

}  // namespace argonia::core::router
