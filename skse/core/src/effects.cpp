#include "argonia/core/effects.h"

#include <algorithm>

namespace argonia::core::effects {

using gen::FieldKind;

namespace {

template <std::size_t N>
std::optional<std::uint8_t> find(const std::array<std::string_view, N>& names, std::string_view id) {
  for (std::size_t i = 0; i < N; ++i)
    if (names[i] == id) return std::uint8_t(i);
  return std::nullopt;
}

bool live(const StatEffect& e, double now) { return !e.until || *e.until > now; }

bool adds(EffectOp op) { return op == EffectOp::fortify || op == EffectOp::ability; }

}  // namespace

std::optional<Field> field_named(std::string_view id) {
  if (auto i = find(gen::kAttrIdNames, id)) return Field{Field::Kind::attribute, *i};
  if (auto i = find(gen::kSkillIdNames, id)) return Field{Field::Kind::skill, *i};
  if (auto i = find(gen::kStatFieldNames, id)) return Field{Field::Kind::stat, *i};
  return std::nullopt;
}

std::optional<EffectOp> op_named(std::string_view id) {
  if (auto i = find(gen::kEffectOpNames, id)) return EffectOp(*i);
  return std::nullopt;
}

std::optional<std::string> check(const StatEffect& e) {
  const auto op = std::string(gen::kEffectOpNames[std::size_t(e.op)]);
  if (e.field.kind != Field::Kind::stat) {
    if (e.op == EffectOp::resist || e.op == EffectOp::absorb) return op + " does not apply to an attribute or skill";
    if (e.magnitude < 0) return "a negative magnitude on an attribute or skill: use drain";
    return std::nullopt;
  }
  const auto kind = gen::kStatFieldKind[e.field.index];
  const auto name = std::string(gen::kStatFieldNames[e.field.index]);
  switch (kind) {
    case FieldKind::pool:
      if (e.op == EffectOp::restore) return "restore on " + name + " is an instant event, not a stack entry";
      if (e.op == EffectOp::resist || e.op == EffectOp::absorb) return op + " does not apply to " + name;
      return std::nullopt;
    case FieldKind::resist:
      if (e.op == EffectOp::restore) return "restore does not apply to " + name;
      return std::nullopt;
    case FieldKind::factor:
      if (!adds(e.op)) return op + " does not apply to the factor " + name;
      if (e.magnitude < 0) return "a negative factor on " + name;
      return std::nullopt;
    case FieldKind::per_int:
      if (!adds(e.op) && e.op != EffectOp::drain) return op + " does not apply to " + name;
      return std::nullopt;
    case FieldKind::flag:
      if (!adds(e.op)) return op + " does not apply to the flag " + name;
      return std::nullopt;
  }
  return "unknown field kind";
}

Effective apply(const Sheet& sh, std::span<const StatEffect> stack, double now) {
  Effective out = Effective::of(sh);
  Attributes a_up, a_down, a_dmg, a_rest;
  Skills s_up, s_down, s_dmg, s_rest;
  for (const auto& e : stack) {
    if (!live(e, now) || check(e)) continue;
    const double m = e.magnitude;
    if (e.field.kind != Field::Kind::stat) {
      const bool attr = e.field.kind == Field::Kind::attribute;
      double& up = attr ? a_up.v[e.field.index] : s_up.v[e.field.index];
      double& down = attr ? a_down.v[e.field.index] : s_down.v[e.field.index];
      double& dmg = attr ? a_dmg.v[e.field.index] : s_dmg.v[e.field.index];
      double& rest = attr ? a_rest.v[e.field.index] : s_rest.v[e.field.index];
      if (adds(e.op)) up += m;
      else if (e.op == EffectOp::drain) down += m;
      else if (e.op == EffectOp::damage) dmg += m;
      else if (e.op == EffectOp::restore) rest += m;
      continue;
    }
    double& f = out.field[e.field.index];
    switch (gen::kStatFieldKind[e.field.index]) {
      case FieldKind::pool:
      case FieldKind::per_int:
      case FieldKind::resist: f += (e.op == EffectOp::drain || e.op == EffectOp::damage) ? -m : m; break;
      case FieldKind::factor: f *= m; break;
      case FieldKind::flag: if (m > 0) f = 1.0; break;
    }
  }
  for (std::size_t i = 0; i < gen::kStatFieldCount; ++i)
    if (gen::kStatFieldKind[i] == FieldKind::resist) out.field[i] = std::min(out.field[i], gen::effects::resist_cap);
  auto settle = [](double base, double up, double down, double dmg, double rest) {
    return std::max(0.0, base + up - down - std::max(0.0, dmg - rest));
  };
  for (std::size_t i = 0; i < gen::kAttrIdCount; ++i)
    out.a.v[i] = settle(sh.a.v[i], a_up.v[i], a_down.v[i], a_dmg.v[i], a_rest.v[i]);
  for (std::size_t i = 0; i < gen::kSkillIdCount; ++i)
    out.s.v[i] = settle(sh.s.v[i], s_up.v[i], s_down.v[i], s_dmg.v[i], s_rest.v[i]);
  return out;
}

std::size_t expire(Stack& stack, double now) {
  const auto before = stack.size();
  std::erase_if(stack, [now](const StatEffect& e) { return !live(e, now); });
  return before - stack.size();
}

}  // namespace argonia::core::effects
