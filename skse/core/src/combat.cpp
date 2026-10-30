#include "argonia/core/combat.h"

#include <algorithm>
#include <array>
#include <cstdlib>

namespace argonia::core::combat {

namespace {

constexpr std::string_view kPinned[] = {"OneHanded", "TwoHanded", "Marksman"};

std::size_t armour_index(SkillId s) {
  for (std::size_t i = 0; i < gen::kArmourSkills.size(); ++i)
    if (gen::kArmourSkills[i].skill == s) return i;
  return gen::kArmourSkills.size();
}

std::string_view trim(std::string_view s) {
  while (!s.empty() && (s.front() == ' ' || s.front() == '\t')) s.remove_prefix(1);
  while (!s.empty() && (s.back() == ' ' || s.back() == '\t' || s.back() == '\r')) s.remove_suffix(1);
  return s;
}

// The value of `key = value` in a TOML text (any section), quotes removed; a comment line is skipped.
std::optional<std::string_view> toml_value(std::string_view text, std::string_view key) {
  while (!text.empty()) {
    const auto nl = text.find('\n');
    auto line = trim(text.substr(0, nl));
    text = nl == std::string_view::npos ? std::string_view() : text.substr(nl + 1);
    if (line.empty() || line.front() == '#') continue;
    const auto eq = line.find('=');
    if (eq == std::string_view::npos || trim(line.substr(0, eq)) != key) continue;
    auto v = trim(line.substr(eq + 1));
    if (const auto hash = v.find(" #"); hash != std::string_view::npos) v = trim(v.substr(0, hash));
    if (v.size() > 1 && v.front() == '"' && v.back() == '"') {
      v.remove_prefix(1);
      v.remove_suffix(1);
    }
    return v;
  }
  return std::nullopt;
}

}  // namespace

double armour_rating(const carriers::Carriers& c, std::span<const Piece> worn) {
  double ar = 0;
  for (const auto& p : worn) {
    const auto i = armour_index(p.skill);
    if (i < c.armour_rating_mult.size()) ar += std::max(0.0, p.raw_rating) * c.armour_rating_mult[i];
  }
  const double bare = std::max(0.0, gen::carriers::unarmored_slots - static_cast<double>(worn.size()));
  return ar + bare * c.unarmored_rating_per_slot;
}

double carrier_value(CarrierId id, const carriers::Carriers& c, const carriers::HandContext& right, double ar) {
  if (!gen::kCarriers[std::size_t(id)].wired) return 0;
  switch (id) {
    case CarrierId::right_attack_damage:
      return right.skill ? c.right.damage_position * c.right.strength_term - 1 : 0;
    case CarrierId::right_power_stamina: return right.skill ? c.right.stamina_mult - 1 : 0;
    case CarrierId::body_incoming_damage: return -carriers::mitigation(ar, gen::combat::reference_blow);
    case CarrierId::body_block: return c.block_stability - 1;
    default: return 0;  // a carrier wired in the table but not here is neutral (test_combat refuses that state)
  }
}

Pass compute(const Sheet& sh, const Effective& e, const Loadout& l) {
  Pass p;
  p.burden = derive(sh, e, l.carried_kg).burden;
  const auto c = carriers::compute(sh, e, p.burden, l.right, {});
  p.armour_rating = armour_rating(c, l.worn);
  for (std::size_t i = 0; i < gen::kCarriers.size(); ++i)
    if (gen::kCarriers[i].wired)
      p.writes.push_back({gen::kCarriers[i].actor_value, carrier_value(CarrierId(i), c, l.right, p.armour_rating)});
  p.roll_allowed = roll_allowed(p.burden);
  return p;
}

std::span<const std::string_view> pinned_vanilla_skills() { return kPinned; }

bool roll_allowed(BurdenTier t) { return gen::kBurdenTiers[std::size_t(t)].roll_distance.has_value(); }

std::optional<PerkLock> tk_dodge_perk_lock(std::string_view toml) {
  const auto perk = toml_value(toml, "sDodgeRequiredPerkID");
  if (!perk) return std::nullopt;
  const auto bar = perk->find('|');
  if (bar == std::string_view::npos || bar == 0) return std::nullopt;
  const std::string hex(trim(perk->substr(bar + 1)));
  char* end = nullptr;
  const unsigned long local = std::strtoul(hex.c_str(), &end, 0);  // base 0: the 0x prefix decides
  if (hex.empty() || !end || *end != '\0' || local == 0) return std::nullopt;
  PerkLock out;
  out.plugin = std::string(trim(perk->substr(0, bar)));
  out.local = static_cast<std::uint32_t>(local);
  const auto on = toml_value(toml, "bUsePerkLock");
  out.on = on && *on == "true";
  return out;
}

std::optional<bool> roll_perk_wanted(const std::optional<PerkLock>& lock, BurdenTier t) {
  if (!lock || !lock->on) return std::nullopt;
  return roll_allowed(t);
}

}  // namespace argonia::core::combat
