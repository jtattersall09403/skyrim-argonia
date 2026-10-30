// L2: §b's round trip, generated from each family's schema (skse/core/schema/families.json). Every family this tree
// registers is bound here and proved by roundtrip::check; every schema has a family and every family a schema. TEST
// has two versions and a migration; TSTN has two versions and no migration, so loading version 1 is refused with a
// readable message. A drifted layout makes the check fail, so it is not a check that cannot fail.
#include "check.h"
#include "builds.h"
#include "argonia/core/family_layouts.h"
#include "argonia/core/roundtrip.h"
#include "argonia/core/seam.h"

#include <set>
#include <string>

using namespace argonia::core;
using namespace argonia::core::families;

namespace {

struct Live {
  seam::State st;                  // every real family, bound by the plugin's own seam::bind
  std::uint32_t a = 0, b = 0;      // TEST
  std::string name;                // TSTN
  std::int32_t count = 0;
} live;

bool lift_test_1_to_2(Bytes& bytes) {
  cosave::Reader r(bytes);
  auto a = r.u32();
  if (!a || !r.done()) return false;
  cosave::Writer w;
  w.u32(*a);
  w.u32(*a + 1);
  bytes = w.take();
  return true;
}

Family fam(std::uint32_t id, std::uint32_t version, std::function<Bytes()> save,
           std::function<bool(std::span<const std::uint8_t>)> load, std::function<void()> reset, std::vector<Step> steps = {}) {
  return Family{id, version, std::move(steps), std::move(save), std::move(load), std::move(reset)};
}

// Every family the tree defines: the real ones through seam::bind (what ArgoniaCore registers), then the tests'.
void bind_all(Registry& reg) {
  for (const auto& why : seam::bind(reg, live.st)) {
    std::fprintf(stderr, "  %s\n", why.c_str());
    CHECK(why.empty());
  }
  CHECK(reg.add(fam(
      cosave::fourcc("TEST"), 2, [] { cosave::Writer w; w.u32(live.a); w.u32(live.b); return w.take(); },
      [](std::span<const std::uint8_t> b) {
        cosave::Reader r(b);
        auto a = r.u32(); auto bb = r.u32();
        if (!a || !bb || !r.done()) return false;
        live.a = *a; live.b = *bb;
        return true;
      },
      [] { live.a = live.b = 0; }, {{1, lift_test_1_to_2}})));
  CHECK(reg.add(fam(
      cosave::fourcc("TSTN"), 2, [] { cosave::Writer w; w.str(live.name); w.i32(live.count); return w.take(); },
      [](std::span<const std::uint8_t> b) {
        cosave::Reader r(b);
        auto n = r.str(); auto c = r.i32();
        if (!n || !c || !r.done()) return false;
        live.name = *n; live.count = *c;
        return true;
      },
      [] { live.name.clear(); live.count = 0; })));
}

void every_family_against_its_schema() {
  Registry reg;
  bind_all(reg);
  const auto schemas = gen::family_schemas();
  std::set<std::uint32_t> declared;
  for (const auto& s : schemas) {
    declared.insert(s.id);
    for (const auto& line : roundtrip::check(reg, s)) {
      std::fprintf(stderr, "  %s\n", line.c_str());
      CHECK(line.empty());
    }
  }
  for (std::uint32_t id : reg.ids()) {
    if (!declared.count(id)) std::fprintf(stderr, "  family %s has no schema\n", fourcc_name(id).c_str());
    CHECK(declared.count(id) == 1);
  }
  CHECK(declared.size() == reg.ids().size() && schemas.size() == 12);
}

void two_versions_a_migration_and_a_refusal() {
  Registry reg;
  bind_all(reg);
  cosave::Writer w;
  w.u32(41);
  Report r = reg.load(cosave::fourcc("TEST"), 1, w.take());
  CHECK(r.status == Status::migrated && live.a == 41 && live.b == 42);
  cosave::Writer n;
  n.str("old");
  live.name = "kept?";
  r = reg.load(cosave::fourcc("TSTN"), 1, n.take());
  CHECK(r.status == Status::refused_no_migration && live.name.empty());
  CHECK(r.message == "co-save family TSTN: saved at version 1, this build reads version 2 and has no migration from "
                     "version 1 to 2; load refused, the family is reset");
}

void the_check_can_fail() {
  Registry reg;
  bind_all(reg);
  // DISP declared without its disposition field: the module's payload no longer fits.
  roundtrip::FamilySchema drifted{disposition::kDispositionsType, "disposition", false,
                                  {{1, false, {roundtrip::list("people", 100000, {roundtrip::u32("npc")}, true)}}}};
  CHECK(!roundtrip::check(reg, drifted).empty());
  // TSTN declared as migrating from version 1: it does not, and the check says so.
  roundtrip::FamilySchema wrong{cosave::fourcc("TSTN"), "test", true,
                                {{1, true, {roundtrip::str("name")}}, {2, false, {roundtrip::str("name"), roundtrip::i32("count")}}}};
  const auto lines = roundtrip::check(reg, wrong);
  CHECK(lines.size() == 1 && lines[0].find("version 1 did not migrate") != std::string::npos);
  roundtrip::FamilySchema missing{cosave::fourcc("NOPE"), "none", true, {{1, false, {}}}};
  CHECK(roundtrip::check(reg, missing).size() == 1);
}

void sampler_and_conformance() {
  const roundtrip::Layout l{roundtrip::u8("k", 0, 3), roundtrip::list("xs", 4, {roundtrip::u32("id"), roundtrip::f64("v", 0, 1)}, true)};
  CHECK(roundtrip::sample(l, 7) == roundtrip::sample(l, 7));
  for (std::uint64_t s = 1; s < 50; ++s) CHECK(!roundtrip::conforms(l, roundtrip::sample(l, s)));
  Bytes p = roundtrip::sample(l, 3);
  p.push_back(9);
  CHECK(roundtrip::conforms(l, p) == std::optional<std::string>("payload: bytes left after the last field"));
  cosave::Writer w;
  w.u8(4);  // outside 0..3
  w.u32(0);
  CHECK(roundtrip::conforms(l, w.take()) == std::optional<std::string>("payload.k: outside its range"));
  cosave::Writer k;
  k.u8(0); k.u32(2); k.u32(5); k.f64(0); k.u32(5); k.f64(0);  // a repeated key
  CHECK(roundtrip::conforms(l, k.take()) == std::optional<std::string>("payload.xs: keys do not rise"));
}

}  // namespace

int main() {
  every_family_against_its_schema();
  two_versions_a_migration_and_a_refusal();
  the_check_can_fail();
  sampler_and_conformance();
  return TEST_MAIN_RESULT("core.roundtrip");
}
