#include "argonia/core/progression.h"

#include <algorithm>

namespace argonia::core::progression {

namespace c = gen::progression;

namespace {

const gen::UseRow& row(UseKind k) { return gen::kUses[std::size_t(k)]; }

bool target_counts(const UseEvent& ev) {
  return ev.target_hostile && !ev.target_helpless && !ev.target_dummy && !ev.target_summoned;
}

double fraction_worth(double part, double whole) {
  if (whole <= 0) return 0;
  return std::clamp(part / whole / c::full_use_damage_fraction, c::min_use_value, 1.0);
}

std::optional<gen::ArmourSkillRow> armour_row(SkillId s) {
  for (const auto& r : gen::kArmourSkills)
    if (r.skill == s) return r;
  return std::nullopt;
}

const gen::SkillClassRow& class_row(const Sheet& sh, SkillId s) {
  return gen::kSkillClasses[std::size_t(sh.cls.of[idx(s)])];
}

// One rank of `s` into the level counter: a full credit for a major or minor skill below the cap, else 1 : n.
int credit_of(const Sheet& sh, SkillId s, bool was_capped) {
  const int full = gen::kSkillClasses[std::size_t(SkillClass::misc)].ranks_per_credit;
  const auto& cls = class_row(sh, s);
  return was_capped ? 1 : full / cls.ranks_per_credit;
}

int full_credit() { return gen::kSkillClasses[std::size_t(SkillClass::misc)].ranks_per_credit; }

// Ranks from points, then pending levels from credit; vastei is the caller's.
void bank(Outcome& o, SkillId s, double points) {
  o.progress.xp[idx(s)] += points;
  for (;;) {
    const double cost = rank_cost(s, o.sheet);
    if (o.progress.xp[idx(s)] < cost) break;
    o.progress.xp[idx(s)] -= cost;
    const bool capped = o.sheet.s[s] >= c::skill_cap;
    if (!capped) o.sheet.s[s] = std::min(o.sheet.s[s] + 1.0, c::skill_cap);
    o.progress.credit += credit_of(o.sheet, s, capped);
    ++o.ranks;
  }
  for (;;) {
    const int need = ranks_for_level(o.sheet.level + o.progress.pending_levels) * full_credit();
    if (o.progress.credit < need) break;
    o.progress.credit -= need;
    ++o.progress.pending_levels;
    ++o.levels;
  }
}

}  // namespace

double use_points(UseKind kind, SkillId skill) {
  for (const auto& r : gen::kUseSkillPoints)
    if (r.use == kind && r.skill == skill) return r.points;
  return row(kind).points;
}

double rank_cost(SkillId s, const Sheet& sh) {
  const double spec = gen::kSkills[idx(s)].spec == sh.cls.spec ? c::spec_factor : 1.0;
  return (sh.s[s] + 1.0) * class_row(sh, s).xp_factor * spec;
}

int ranks_for_level(int level) {
  const std::size_t i = std::size_t(std::max(level, 1)) - 1;
  return gen::kRanksPerLevel[std::min(i, gen::kRanksPerLevel.size() - 1)];
}

double armour_kill_value(SkillId armour_skill, double victim_max_health, double own_max_health) {
  auto r = armour_row(armour_skill);
  if (!r || own_max_health <= 0) return 0;
  return r->win_weight *
         std::clamp(victim_max_health / (c::armour_kill_health_divisor * own_max_health), c::min_use_value, 1.0);
}

double worthiness(const UseEvent& ev) {
  if (ev.amount <= 0) return 0;
  switch (ev.kind) {
    case UseKind::weaponConnect:
      return target_counts(ev) && ev.damage > 0 ? fraction_worth(ev.damage, ev.target_max_health) : 0;
    case UseKind::hitTaken: {
      auto r = armour_row(ev.skill);
      if (!r || ev.damage <= 0 || ev.target_dummy) return 0;
      return r->hit_weight * fraction_worth(ev.damage, ev.own_max_health);
    }
    case UseKind::armourKill:
      return target_counts(ev) ? armour_kill_value(ev.skill, ev.target_max_health, ev.own_max_health) : 0;
    case UseKind::block: return ev.target_hostile && !ev.target_dummy && !ev.target_summoned ? 1 : 0;
    case UseKind::spellEffect: return ev.had_effect ? 1 : 0;
    case UseKind::run:
    case UseKind::swim: return ev.outside_settlement ? 1 : 0;
    case UseKind::jump:
      return ev.jump_rise_m >= c::jump_clears_rise_m || ev.jump_run_m >= c::jump_clears_run_m ? 1 : 0;
    case UseKind::fall: return ev.first_since_rest && ev.damage > 0 ? 1 : 0;
    case UseKind::brew: return ev.first_since_rest ? 1 : 0;
    case UseKind::lock:
    case UseKind::trap: return ev.lock_level >= ev.lock_ceiling - c::security_window ? 1 : 0;
    case UseKind::persuade:
    case UseKind::trade: return ev.real_outcome ? 1 : 0;
    case UseKind::climb:
    case UseKind::enchant:
    case UseKind::repair:
    case UseKind::temper:
    case UseKind::forge: return 1;
  }
  return 0;
}

Outcome apply(const Progress& p, const Sheet& sh, const Effective& e, const UseEvent& ev) {
  Outcome o{p, sh};
  const double w = worthiness(ev);
  if (w <= 0) return o;
  double amount = ev.amount;
  if (ev.kind == UseKind::run || ev.kind == UseKind::swim) {
    amount = std::min(amount, std::max(0.0, c::athletics_seconds_per_rest - p.athletics_s));
    o.progress.athletics_s += amount;
    if (amount <= 0) return o;
  }
  // armourKill's points are its own award times the class win weight (worthiness carries the weight).
  const double points = use_points(ev.kind, ev.skill) * amount * w;
  o.points = points;
  o.vastei = c::vastei_per_use * points * (1.0 + e.s[ev.skill] / c::vastei_skill_divisor);
  o.progress.vastei += o.vastei;
  bank(o, ev.skill, points * ev.xp_mult);
  return o;
}

bool can_train(const Sheet& sh, SkillId s) {
  return sh.s[s] < sh.a[gen::kSkills[idx(s)].gov] && sh.s[s] < c::skill_cap;
}

Outcome grant_ranks(const Progress& p, const Sheet& sh, SkillId s, int ranks) {
  Outcome o{p, sh};
  for (int i = 0; i < ranks; ++i) bank(o, s, rank_cost(s, o.sheet) - o.progress.xp[idx(s)]);
  return o;
}

Progress on_rest(const Progress& p) {
  Progress out = p;
  out.athletics_s = 0;
  return out;
}

cosave::Bytes encode(const Sheet& sh, const Progress& p) {
  cosave::Writer w;
  for (double v : sh.a.v) w.f64(v);
  for (double v : sh.s.v) w.f64(v);
  w.i32(sh.level);
  for (auto k : sh.cls.of) w.u8(std::uint8_t(k));
  w.u8(std::uint8_t(sh.cls.spec));
  w.u32(std::uint32_t(sh.cls.favoured.size()));
  for (auto a : sh.cls.favoured) w.u8(std::uint8_t(a));
  for (double v : p.xp) w.f64(v);
  w.f64(p.vastei);
  w.i32(p.credit);
  w.i32(p.pending_levels);
  w.f64(p.athletics_s);
  return w.take();
}

bool decode(std::span<const std::uint8_t> b, Sheet& sh, Progress& p) {
  cosave::Reader r(b);
  Sheet s;
  Progress q;
  for (double& v : s.a.v) { auto x = r.f64(); if (!x) return false; v = *x; }
  for (double& v : s.s.v) { auto x = r.f64(); if (!x) return false; v = *x; }
  auto level = r.i32();
  if (!level) return false;
  s.level = *level;
  for (auto& k : s.cls.of) {
    auto x = r.u8();
    if (!x || *x >= gen::kSkillClassCount) return false;
    k = SkillClass(*x);
  }
  auto spec = r.u8();
  auto nfav = r.u32();
  if (!spec || *spec >= gen::kSpecialisationCount || !nfav || *nfav > gen::kAttrIdCount) return false;
  s.cls.spec = Specialisation(*spec);
  for (std::uint32_t i = 0; i < *nfav; ++i) {
    auto x = r.u8();
    if (!x || *x >= gen::kAttrIdCount) return false;
    s.cls.favoured.push_back(AttrId(*x));
  }
  for (double& v : q.xp) { auto x = r.f64(); if (!x) return false; v = *x; }
  auto vastei = r.f64();
  auto credit = r.i32();
  auto pending = r.i32();
  auto ath = r.f64();
  if (!vastei || !credit || !pending || !ath || !r.done()) return false;
  q.vastei = *vastei;
  q.credit = *credit;
  q.pending_levels = *pending;
  q.athletics_s = *ath;
  sh = std::move(s);
  p = q;
  return true;
}

}  // namespace argonia::core::progression
