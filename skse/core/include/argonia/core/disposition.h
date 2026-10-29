// Disposition 0-100 per person (76 §125, native map G18.3): a base from the person's row, the player's
// Personality and the priors ArgoniaCore gathers (faction reactions, membership, race, deeds), moved by changes,
// read in bands. Persuasion joins in 2.5.
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/tables_conditions.h"

#include <cstdint>
#include <map>
#include <optional>
#include <span>

namespace argonia::core::disposition {

using gen::DispositionBand;
using NpcId = std::uint32_t;

struct Speaker { double authored_base = 0; };  // the person's own starting regard (their world row)
struct Priors {
  double personality = 0;        // the player's effective Personality
  double faction_reaction = 0;   // faction_reaction rows between the speaker's factions and the player's
  double membership = 0;         // faction_rules_member_disposition for a shared faction at the player's rank
  double race = 0;               // the speaker's race prior toward the player's race
  double deeds = 0;              // remembered deeds toward this person
};

int clamp(double d);
int base(const Speaker& s, const Priors& p);
DispositionBand band(int d);
struct Change { int delta = 0; };
int apply(int d, const Change& c);

// The `dispositions` family: the current value of each person met (version 1).
inline constexpr std::uint32_t kDispositionsType = cosave::fourcc("DISP");
using Table = std::map<NpcId, int>;
cosave::Bytes encode(const Table& t);
std::optional<Table> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::disposition
