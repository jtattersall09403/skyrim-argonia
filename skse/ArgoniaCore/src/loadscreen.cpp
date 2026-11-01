// The loading screen's slow motion (1.12 lane loading; core/loadscreen steps it): MistMenu's own per-frame call
// (IMenu::AdvanceMovie, vfunc 5, hooked through its vtable) turns the loading-screen model slowly about its upright
// axis and breathes its scale, after the engine's own frame. The menu only ever changes itself, inside its own call,
// while it exists: no other thread touches it. A mouse drag (or the stick, seen as angleZ changing) hands the model
// to the player for the rest of that screen. Each new model starts from the record's own rotation and scale.
#include "core.h"
#include "argonia/core/loadscreen.h"

namespace argonia::plugin {

namespace {

namespace ls = ac::loadscreen;

struct State {
  RE::BSFadeNode* model = nullptr;  // the model the drift belongs to (a new screen resets it)
  RE::NiMatrix3 base_rotate;
  float base_scale = 1.0f;
  float last_angle = 0.0f;
  ls::Drift drift;
};
State g_state;  // touched only inside MistMenu::AdvanceMovie

REL::Relocation<decltype(&RE::IMenu::AdvanceMovie)> g_advance;

struct MistAdvance {
  static void Thunk(RE::MistMenu* menu, float interval, std::uint32_t time) {
    g_advance(menu, interval, time);
    if (!menu) return;
    auto& m = menu->GetRuntimeData();
    if (!m.showLoadScreen) return;
    auto* model = m.loadScreenModel.get();
    if (!model) return;
    auto& s = g_state;
    if (s.model != model) {
      s = State{};
      s.model = model;
      s.base_rotate = model->local.rotate;
      s.base_scale = model->local.scale;
      s.last_angle = m.angleZ;
      SKSE::log::info("loadscreen: drift starts on a new model (scale {:.3f})", s.base_scale);
    }
    const bool dragging = m.leftButtonHeldDown || m.rightButtonHeldDown || m.angleZ != s.last_angle;
    s.last_angle = m.angleZ;
    const bool was = s.drift.dragged;
    s.drift = ls::step(s.drift, interval, dragging);
    if (s.drift.dragged) {
      if (!was) SKSE::log::info("loadscreen: the player took the model; drift held");
      return;
    }
    RE::NiMatrix3 turn;
    turn.SetEulerAnglesXYZ(0.0f, 0.0f, s.drift.yaw_deg * 0.0174532925f);
    model->local.rotate = s.base_rotate * turn;
    model->local.scale = s.base_scale * s.drift.scale;
    RE::NiUpdateData u;
    model->Update(u);
  }
};

}  // namespace

void LoadScreenInstall() {
  REL::Relocation<std::uintptr_t> vt{RE::VTABLE_MistMenu[0]};
  g_advance = vt.write_vfunc(0x5, &MistAdvance::Thunk);
  SKSE::log::info("loadscreen: MistMenu::AdvanceMovie hooked (the slow turn and breath)");
}

}  // namespace argonia::plugin
