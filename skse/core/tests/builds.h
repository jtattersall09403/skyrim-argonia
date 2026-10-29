// The five reference builds every sheet-side test runs over (docs/loops.md: every archetype x five builds; 76 §116's
// Marsh Hand is the continuity anchor). Expected values in the tests were computed by hand from 76's text.
#pragma once
#include "argonia/core/sheet.h"

namespace argonia::test {

using namespace argonia::core;

struct Build { const char* name; Sheet sheet; double carried_kg; };

inline Sheet make(double str, double end, double agi, double spd, double intel, double wil, double per,
                  double ath, double acro, int level) {
  Sheet s;
  s.a[AttrId::strength] = str; s.a[AttrId::endurance] = end; s.a[AttrId::agility] = agi; s.a[AttrId::speed] = spd;
  s.a[AttrId::intelligence] = intel; s.a[AttrId::willpower] = wil; s.a[AttrId::personality] = per;
  for (auto& v : s.s.v) v = 5;
  s.s[SkillId::athletics] = ath; s.s[SkillId::acrobatics] = acro;
  s.level = level;
  for (auto& c : s.cls.of) c = SkillClass::misc;
  return s;
}

inline Sheet marsh_hand() {
  Sheet s = make(50, 50, 50, 50, 40, 40, 40, 40, 30, 10);
  s.s[SkillId::longBlade] = 60; s.s[SkillId::block] = 50; s.s[SkillId::heavyArmor] = 45;
  s.cls.spec = Specialisation::combat;
  for (auto k : {SkillId::longBlade, SkillId::block, SkillId::heavyArmor, SkillId::athletics, SkillId::axe})
    s.cls.of[idx(k)] = SkillClass::major;
  for (auto k : {SkillId::blunt, SkillId::spear, SkillId::smithing, SkillId::acrobatics, SkillId::restoration})
    s.cls.of[idx(k)] = SkillClass::minor;
  s.cls.favoured = {AttrId::strength, AttrId::endurance};
  return s;
}

inline Build builds[] = {
    {"marsh-hand", marsh_hand(), 45},
    {"novice", make(40, 40, 40, 45, 40, 40, 40, 15, 15, 1), 10},
    {"mage", make(30, 35, 40, 45, 80, 70, 50, 20, 10, 15), 20},
    {"hauler", make(70, 60, 35, 40, 30, 30, 30, 30, 20, 8), 300},
    {"god", make(100, 100, 100, 100, 100, 100, 100, 100, 100, 50), 0},
};

}  // namespace argonia::test
