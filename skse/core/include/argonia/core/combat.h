// The combat wiring's runtime side (1.6; docs/research/2026-10-30/combat-wiring.md): what ArgoniaCore writes into
// the engine for the player on every sheet, effect, equip or burden change. The P1 carriers (combat_carrier rows,
// read by ARG_Perk_Carriers with Multiply 1 + Actor Value Mult, so each value is factor − 1 and 0 is neutral), the
// vanilla weapon skills pinned at 0 (Skyrim's own skill damage term made neutral), and the roll lock: no roll when
// overloaded, carried by TK Dodge RE Addon's own perk lock (bUsePerkLock and sDodgeRequiredPerkID in tk-dodge.toml),
// the required perk given or taken by burden tier. ArgoniaCore does the actor-value and perk writes.
#pragma once
#include "argonia/core/carriers.h"
#include "argonia/core/sheet.h"
#include "argonia/core/tables_combat.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::combat {

using gen::CarrierId;

// A worn armour piece: the armour skill its class trains and its raw rating (76 §116: steel 50).
struct Piece {
  SkillId skill = SkillId::unarmored;
  double raw_rating = 0;
};

// What the engine says the player holds, wears and carries.
struct Loadout {
  carriers::HandContext right;  // the right-hand weapon's class skill (handToHand for fists), bow flag, shortfall
  std::vector<Piece> worn;      // armour pieces only (not clothing)
  double carried_kg = 0;
};

// The player's armour rating: each piece's raw rating times its class band, plus the Unarmored term for every
// slot of the four no piece covers (76 §118).
double armour_rating(const carriers::Carriers& c, std::span<const Piece> worn);

// The value one carrier's actor value holds (factor − 1); 0 for a reserved (unwired) carrier and for an empty hand.
double carrier_value(CarrierId id, const carriers::Carriers& c, const carriers::HandContext& right, double armour_rating);

struct Write {
  std::string_view actor_value;
  double value = 0;
  bool operator==(const Write&) const = default;
};
struct Pass {
  std::vector<Write> writes;  // every wired carrier, in kCarriers order
  BurdenTier burden{};
  bool roll_allowed = true;
  double armour_rating = 0;
};
// One write pass over the effective sheet and the loadout.
Pass compute(const Sheet& sh, const Effective& e, const Loadout& l);

// The vanilla weapon skill actor values pinned at 0 (w.damage.vanilla-skill): no skill mirror ever writes them.
std::span<const std::string_view> pinned_vanilla_skills();

// The roll is allowed in every burden tier that has a roll distance (none when overloaded, 76 §122).
bool roll_allowed(BurdenTier t);

// TK Dodge's perk lock, read from its tk-dodge.toml: whether bUsePerkLock is on, and the perk the roll requires
// ("Plugin.esp|0x809"). Empty when the file names no required perk.
struct PerkLock {
  bool on = false;
  std::string plugin;
  std::uint32_t local = 0;
  bool operator==(const PerkLock&) const = default;
};
std::optional<PerkLock> tk_dodge_perk_lock(std::string_view toml);

// Whether the roll perk must be given (true) or taken (false) now; empty when the lock is off (nothing to do).
std::optional<bool> roll_perk_wanted(const std::optional<PerkLock>& lock, BurdenTier t);

}  // namespace argonia::core::combat
