#include "argonia/core/life.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace argonia::core::life {

namespace {

using progression::UseEvent;
using gen::UseKind;

constexpr std::string_view kWeaponClassPrefix = "weapon_class.";

// 1.3 §a's table: fourteen skills on a vanilla actor value, the rest on Custom Skills Framework (no name yet).
// Marksman is not mirrored: the vanilla weapon skills stay pinned at 0 (combat::pinned_vanilla_skills).
constexpr std::array<SkillMirror, gen::kSkillIdCount> kSkillMirrors{{
    {SkillId::acrobatics, ""},          {SkillId::alchemy, "Alchemy"},       {SkillId::alteration, "Alteration"},
    {SkillId::athletics, ""},           {SkillId::axe, ""},                  {SkillId::block, "Block"},
    {SkillId::blunt, ""},               {SkillId::conjuration, "Conjuration"}, {SkillId::destruction, "Destruction"},
    {SkillId::enchant, "Enchanting"},   {SkillId::handToHand, ""},           {SkillId::heavyArmor, "HeavyArmor"},
    {SkillId::illusion, "Illusion"},    {SkillId::lightArmor, "LightArmor"}, {SkillId::longBlade, ""},
    {SkillId::marksman, ""},           {SkillId::mediumArmor, ""},          {SkillId::mercantile, ""},
    {SkillId::mysticism, ""},           {SkillId::restoration, "Restoration"}, {SkillId::security, "Lockpicking"},
    {SkillId::shortBlade, ""},          {SkillId::smithing, "Smithing"},     {SkillId::sneak, "Sneak"},
    {SkillId::spear, ""},               {SkillId::speechcraft, "Speechcraft"},{SkillId::unarmored, ""},
}};

constexpr std::array<std::string_view, 18> kVanillaSkills{
    "OneHanded", "TwoHanded", "Marksman", "Block", "Smithing", "HeavyArmor", "LightArmor", "Pickpocket", "Lockpicking",
    "Sneak", "Alchemy", "Speechcraft", "Alteration", "Conjuration", "Destruction", "Illusion", "Restoration", "Enchanting"};

UseEvent base(SkillId s, UseKind k) {
  UseEvent ev{};
  ev.skill = s;
  ev.kind = k;
  return ev;
}

}  // namespace

std::optional<SkillId> skill_named(std::string_view id) {
  for (std::size_t i = 0; i < gen::kSkillIdCount; ++i)
    if (gen::kSkillIdNames[i] == id) return SkillId(i);
  return std::nullopt;
}

std::optional<SkillId> weapon_skill(std::string_view class_world_id) {
  if (!class_world_id.starts_with(kWeaponClassPrefix)) return std::nullopt;
  return skill_named(class_world_id.substr(kWeaponClassPrefix.size()));
}

std::span<const SkillMirror> skill_mirrors() { return kSkillMirrors; }
std::span<const std::string_view> vanilla_skills() { return kVanillaSkills; }

Worn worn_of(std::span<const combat::Piece> pieces) {
  Worn w;
  for (const auto& p : pieces) {
    if (p.skill == SkillId::heavyArmor) ++w.heavy;
    else if (p.skill == SkillId::mediumArmor) ++w.medium;
    else if (p.skill == SkillId::lightArmor) ++w.light;
  }
  return w;
}

std::optional<SkillId> blow_skill(bool is_weapon, bool hand_to_hand, std::optional<SkillId> weapon_class) {
  if (!is_weapon) return std::nullopt;
  if (hand_to_hand) return SkillId::handToHand;
  return weapon_class;
}

SkillId armour_skill(const Worn& w) {
  if (w.heavy + w.medium + w.light <= 0) return SkillId::unarmored;
  if (w.heavy >= w.medium && w.heavy >= w.light) return SkillId::heavyArmor;
  if (w.medium >= w.light) return SkillId::mediumArmor;
  return SkillId::lightArmor;
}

double HealthWatch::damage(std::uint32_t actor, double health_now, double health_max) {
  auto [it, fresh] = last_.try_emplace(actor, health_max);
  const double before = fresh ? health_max : it->second;
  it->second = health_now;
  return std::max(0.0, before - health_now);
}

UseEvent hit_dealt(std::optional<SkillId> weapon, double damage, const Target& t) {
  UseEvent ev = base(weapon.value_or(SkillId::handToHand), UseKind::weaponConnect);
  ev.damage = damage;
  ev.target_max_health = t.max_health;
  ev.target_hostile = t.hostile;
  ev.target_dummy = t.dummy;
  ev.target_summoned = t.summoned;
  ev.target_helpless = t.helpless;
  return ev;
}

std::vector<UseEvent> hit_taken(double damage, double own_max_health, const Worn& w, bool blocked,
                                bool attacker_hostile) {
  std::vector<UseEvent> out;
  UseEvent armour = base(armour_skill(w), UseKind::hitTaken);
  armour.damage = damage;
  armour.own_max_health = own_max_health;
  out.push_back(armour);
  if (blocked) {
    UseEvent b = base(SkillId::block, UseKind::block);
    b.target_hostile = attacker_hostile;
    out.push_back(b);
  }
  return out;
}

UseEvent kill(const Target& victim, double own_max_health, const Worn& w) {
  UseEvent ev = base(armour_skill(w), UseKind::armourKill);
  ev.target_max_health = victim.max_health;
  ev.own_max_health = own_max_health;
  ev.target_hostile = victim.hostile;
  ev.target_dummy = victim.dummy;
  ev.target_summoned = victim.summoned;
  ev.target_helpless = victim.helpless;
  return ev;
}

UseEvent cast(SkillId school, bool had_effect) {
  UseEvent ev = base(school, UseKind::spellEffect);
  ev.had_effect = had_effect;
  return ev;
}

UseEvent unlock(double lock_level, double ceiling) {
  UseEvent ev = base(SkillId::security, UseKind::lock);
  ev.lock_level = lock_level;
  ev.lock_ceiling = ceiling;
  return ev;
}

Gain use(seam::State& s, const UseEvent& ev) {
  const auto out = progression::apply(s.prog, s.sheet, Effective::of(s.sheet), ev);
  s.prog = out.progress;
  s.sheet = out.sheet;
  return Gain{ev.skill, out.points, out.vastei, out.ranks, out.levels};
}

Rested rest_at(seam::State& s, const rest::Context& ctx, const Roster& roster) {
  Rested r;
  r.outcome = rest::on_rest(ctx, s.prog.pending_levels);
  if (r.outcome.ruling.verdict != rest::Verdict::rest) {
    r.notice = rest::to_string(r.outcome.ruling.why);
    return r;
  }
  if (r.outcome.wake_point) s.death.wake = *r.outcome.wake_point;
  s.prog = progression::on_rest(s.prog);
  if (r.outcome.respawn) r.reset = respawn::to_reset(roster.actors);
  if (r.outcome.open_sitting)
    if (auto st = sitting::open(s.sheet, s.prog.vastei, s.prog.pending_levels)) r.sitting = std::move(*st);
  r.save_now = r.outcome.save && !r.sitting;
  return r;
}

std::string attribute_label(AttrId a) {
  std::string n(gen::kAttrIdNames[idx(a)]);
  if (!n.empty() && n[0] >= 'a' && n[0] <= 'z') n[0] = char(n[0] - 'a' + 'A');
  return n;
}

Sitting open_sitting(const sitting::State& st, const seam::State& s) {
  Sitting sit{st, derive(s.sheet, Effective::of(s.sheet), 0).health, std::max(0, s.prog.pending_levels - 1), {}};
  return sit;
}

namespace {
msg::SittingRefusal refusal_of(sitting::Refusal r) {
  switch (r) {
    case sitting::Refusal::no_pending_level: return msg::SittingRefusal::noPendingLevel;
    case sitting::Refusal::at_cap_this_sitting: return msg::SittingRefusal::atCapThisSitting;
    case sitting::Refusal::at_purchase_cap: return msg::SittingRefusal::atPurchaseCap;
    case sitting::Refusal::too_dear: return msg::SittingRefusal::tooDear;
  }
  return msg::SittingRefusal::tooDear;
}
}  // namespace

msg::SittingState view(const Sitting& sit) {
  msg::SittingState v;
  v.level = sit.st.sheet.level;
  v.vastei = sit.st.vastei;
  v.pending_after = sit.pending_after;
  for (std::size_t i = 0; i < gen::kAttrIdCount; ++i) {
    const auto a = AttrId(i);
    msg::SittingAttribute row;
    row.id = msg::AttributeId(i);
    row.name = attribute_label(a);
    row.value = std::int64_t(std::floor(sit.st.sheet.a[a]));
    row.bought = sit.st.bought[i];
    row.cap = std::int64_t(gen::sitting::points_per_attribute_cap);
    row.cost = sitting::cost(sit.st, a);
    if (auto b = sitting::buy(sit.st, a); !b) row.refusal = refusal_of(b.error());
    v.attributes.push_back(std::move(row));
  }
  v.health = {sit.health_before, derive(sit.st.sheet, Effective::of(sit.st.sheet), 0).health};
  if (!sit.notice.empty()) v.notice = sit.notice;
  return v;
}

static_assert(std::size_t(msg::AttributeId::willpower) + 1 == gen::kAttrIdCount, "the schema's AttributeId follows AttrId");

void close(const Sitting& sit, seam::State& s) {
  const auto c = sitting::close(sit.st);
  s.sheet = c.sheet;
  s.prog.vastei = c.vastei;
  s.prog.pending_levels = std::max(0, s.prog.pending_levels - int(gen::sitting::levels_per_sitting));
}

SittingReply on_intent_text(Sitting& sit, std::string_view json, seam::State& s) {
  SittingReply r;
  auto in = msg::decode_intent(json);
  if (!in) {
    r.notes.push_back("sitting: intent refused: " + in.error());
    r.state = view(sit);
    return r;
  }
  if (const auto* b = std::get_if<msg::SittingBuy>(&*in)) {
    const auto a = AttrId(std::size_t(b->attribute));
    auto next = sitting::buy(sit.st, a);
    if (next) {
      r.notes.push_back("sitting: bought " + attribute_label(a) + " for " + std::to_string(sit.st.vastei - next->vastei));
      sit.st = std::move(*next);
      sit.notice.clear();
    } else {
      sit.notice = attribute_label(a) + ": " + sitting::to_string(next.error());
      r.notes.push_back("sitting: " + sit.notice);
    }
    r.state = view(sit);
    return r;
  }
  if (std::holds_alternative<msg::SittingDone>(*in)) {
    close(sit, s);
    r.closed = r.save_now = true;
    r.notes.push_back("sitting: closed at level " + std::to_string(s.sheet.level) + ", vastei " +
                      std::to_string(s.prog.vastei));
    return r;
  }
  r.notes.push_back("sitting: an intent for another view; ignored");
  r.state = view(sit);
  return r;
}

Died die(seam::State& s, rest::Pos at, const Roster& roster) {
  Died d;
  d.had_wake_point = s.death.wake.has_value();
  d.outcome = death::on_death(s.prog.vastei, at, s.death.wake.value_or(at));
  d.replaced_pile = s.death.pile.has_value();
  s.death.pile = d.outcome.pile;  // a second death replaces the pile, even with nothing carried
  s.prog.vastei = d.outcome.carried;
  if (d.outcome.counts_as_rest) d.reset = respawn::to_reset(roster.actors);
  return d;
}

std::optional<double> take_pile(seam::State& s, rest::Pos player) {
  if (!s.death.pile) return std::nullopt;
  auto got = death::take(*s.death.pile, player);
  if (!got) return std::nullopt;
  s.prog.vastei += *got;
  s.death.pile.reset();
  return got;
}

rest::Pos at_units(double x, double y, double z, std::uint32_t cell) {
  const double m = gen::units::units_per_metre;
  return {x / m, y / m, z / m, cell};
}

std::array<double, 3> to_units(const rest::Pos& p) {
  const double m = gen::units::units_per_metre;
  return {p.x * m, p.y * m, p.z * m};
}

std::string pile_name(double vastei) {
  return "Vastei (" + std::to_string(static_cast<long long>(std::floor(vastei))) + ")";
}

const char* to_string(SuspendWhy w) {
  switch (w) {
    case SuspendWhy::quit: return "quit";
    case SuspendWhy::stream_drop: return "stream drop";
    case SuspendWhy::interval: return "interval";
  }
  return "?";
}

std::optional<SuspendWhy> suspend_why(std::string_view wire) {
  if (wire == "quit") return SuspendWhy::quit;
  if (wire == "stream_drop") return SuspendWhy::stream_drop;
  return std::nullopt;
}

bool suspend_due(SuspendWhy why, double now_s, std::optional<double> last_save_s, bool in_combat, bool can_save_now,
                 bool menu_open) {
  if (!can_save_now) return false;
  if (why == SuspendWhy::quit || why == SuspendWhy::stream_drop) return true;
  if (in_combat || menu_open) return false;
  return !last_save_s || now_s - *last_save_s >= gen::rest::suspend_save_interval_s;
}

std::optional<SuspendWhy> QuitWatch::on_menu(bool opening, bool quit_requested) {
  if (!quit_requested) {
    saved_ = false;
    return std::nullopt;
  }
  if (opening || saved_) return std::nullopt;
  saved_ = true;
  return SuspendWhy::quit;
}

std::vector<std::string> install(router::Router& r, router::Handler on_level_up, router::Handler on_death) {
  std::vector<std::string> log;
  std::string why;
  for (auto h : {router::HookId::progressionOff, router::HookId::deathIntercept}) {
    if (r.install(h, &why)) log.push_back("hook " + std::string(router::name(h)));
    else log.push_back("refused: " + why);
  }
  if (r.handle(router::SurfaceId::levelUpMenu, std::move(on_level_up), &why)) log.push_back("handler levelUpMenu");
  else log.push_back("refused: " + why);
  if (r.handle(router::SurfaceId::playerDeath, std::move(on_death), &why)) log.push_back("handler playerDeath");
  else log.push_back("refused: " + why);
  return log;
}

}  // namespace argonia::core::life
