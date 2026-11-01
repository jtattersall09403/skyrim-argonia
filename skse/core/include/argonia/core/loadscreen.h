// The loading screen's slow motion (1.12 lane loading, owner look 1): the model turns slowly about its upright axis
// and the view breathes in and out a little, as Skyrim's own screens feel; the player's drag takes over for the rest
// of that screen. ArgoniaCore steps this inside MistMenu's own per-frame call (AdvanceMovie) and applies the result
// to the menu's loadScreenModel. The rates are feel values of ours (no measured oracle: vanilla adds no motion on
// our stack, out/l112load/fix5), so they live here rather than in generated/.
#pragma once

namespace argonia::core::loadscreen {

inline constexpr float kTurnDegPerSec = 8.0f;   // a full turn in 45 s
inline constexpr float kZoomAmplitude = 0.04f;  // the model's scale swings +-4 %
inline constexpr float kZoomPeriodSec = 20.0f;  // one breath in and out
inline constexpr float kMaxStepSec = 0.25f;     // a hitch is not a jump

struct Drift {
  float seconds = 0.0f;  // motion time since the screen opened (frozen once dragged)
  float yaw_deg = 0.0f;  // turn added to the record's initial rotation, in [0, 360)
  float scale = 1.0f;    // multiplier on the record's initial scale
  bool dragged = false;  // the player has taken the model: no more motion this screen
};

// One frame: `dt` seconds since the last (clamped to [0, kMaxStepSec]); `dragging` is true while a mouse button or
// the stick turns the model. Once dragged, the drift holds where it is.
Drift step(Drift d, float dt, bool dragging);

}  // namespace argonia::core::loadscreen
