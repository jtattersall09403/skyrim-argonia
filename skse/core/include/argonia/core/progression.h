// Use, vastei and levels (76 §120): Morrowind's rank cost and use values, the worthiness rules ("in anger"),
// vastei per qualifying use and the ranks-per-level counter with the 1 : 3 credit. ArgoniaCore turns engine events
// into UseEvents (native map G16.1); vanilla gain is off by data (P4).
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/sheet.h"

#include <array>
#include <optional>
#include <span>

namespace argonia::core::progression {

using gen::UseKind;

struct UseEvent {
  SkillId skill;
  UseKind kind;
  double amount = 1;  // units of the use: 1 a use; seconds, metres or percent for those units
  // A blow, a hit taken or a kill.
  double damage = 0;               // dealt (weaponConnect) or taken (hitTaken)
  double target_max_health = 0;    // the target's (weaponConnect, armourKill)
  double own_max_health = 0;       // the player's (hitTaken, armourKill)
  bool target_hostile = true;      // a hostile that can fight back
  bool target_helpless = false;    // stuck, broken pathing: nothing accrues
  bool target_dummy = false;       // flagged trainingDummy: nothing accrues
  bool target_summoned = false;    // the player's own summon: nothing accrues
  // Situational facts the adapter knows.
  bool had_effect = true;          // a spell that changed something
  bool outside_settlement = true;  // run and swim count only outside settlement bounds
  bool first_since_rest = true;    // a brew not made, a fall location not fallen at, since the last rest
  bool real_outcome = true;        // a persuasion or check that changed something
  double jump_rise_m = 0, jump_run_m = 0;
  double lock_level = 0, lock_ceiling = 0;  // Security: the lock and the player's opening ceiling
  double xp_mult = 1;              // the rested entry's multiplier (rest::xp_multiplier)
};

struct Progress {
  std::array<double, gen::kSkillIdCount> xp{};  // use points toward each skill's next rank
  double vastei = 0;                             // carried
  int credit = 0;          // counted-rank credit toward the next pending level, in 1/ranks_per_credit units
  int pending_levels = 0;  // banked at the next rests, one per sitting
  double athletics_s = 0;  // Athletics seconds counted since the last rest (the per-rest cap)
  bool operator==(const Progress&) const = default;
};

struct Outcome {
  Progress progress;
  Sheet sheet;           // skills raised by any ranks gained
  double points = 0;     // use points credited
  double vastei = 0;     // vastei earned by this use
  int ranks = 0;         // ranks gained
  int levels = 0;        // pending levels made ready
};

// The worthiness of a use (76 §120.2): 0 when it does not count, else the factor that scales its canon value.
double worthiness(const UseEvent& ev);
// Canon points of one unit of the use for the skill (76 §120.1), before worthiness.
double use_points(UseKind kind, SkillId skill);
// Points to the next rank: (skill + 1) x class factor x specialisation factor (76 §120.1).
double rank_cost(SkillId s, const Sheet& sh);
// Ranks the level counter asks to take level `level` to the next (76 §120.5).
int ranks_for_level(int level);
// The armour skill's kill and hit points (76 §120.2), before the use's own value.
double armour_kill_value(SkillId armour_skill, double victim_max_health, double own_max_health);

Outcome apply(const Progress& p, const Sheet& sh, const Effective& e, const UseEvent& ev);

// Trainers and books (76 §120.1): ranks without vastei. The trainer cap (76 §117.1): a skill trains only below its
// governing attribute's base value.
bool can_train(const Sheet& sh, SkillId s);
Outcome grant_ranks(const Progress& p, const Sheet& sh, SkillId s, int ranks);

// A rest clears the per-rest counters.
Progress on_rest(const Progress& p);

// The `stats` family payload: the sheet and the progress (version 1).
inline constexpr std::uint32_t kStatsType = cosave::fourcc("STAT");
cosave::Bytes encode(const Sheet& sh, const Progress& p);
bool decode(std::span<const std::uint8_t> b, Sheet& sh, Progress& p);

}  // namespace argonia::core::progression
