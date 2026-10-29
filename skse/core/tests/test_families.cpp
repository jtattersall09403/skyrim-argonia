// L2: the save contract (1.1 §b): a test family with two schema versions and a migration (1.1's acceptance), the
// readable refusals (no migration, newer, broken, unknown, version 0), duplicate registration refused (S10a), reset
// on refusal and reset_all (the scene reset), and the round trip of every family this tree defines.
#include "check.h"
#include "builds.h"
#include "argonia/core/death.h"
#include "argonia/core/disposition.h"
#include "argonia/core/families.h"
#include "argonia/core/items.h"
#include "argonia/core/journal.h"
#include "argonia/core/progression.h"

#include <string>

using namespace argonia::core;
using namespace argonia::core::families;

namespace {

// TEST v1 {a}; v2 {a, b = a + 1}.
struct TestState { std::uint32_t a = 0, b = 0; int resets = 0; } g;

bool lift_1_to_2(Bytes& bytes) {
  cosave::Reader r(bytes);
  auto a = r.u32();
  if (!a || !r.done()) return false;
  cosave::Writer w;
  w.u32(*a);
  w.u32(*a + 1);
  bytes = w.take();
  return true;
}

Family test_family(std::vector<Step> steps = {{1, lift_1_to_2}}) {
  Family f;
  f.id = cosave::fourcc("TEST");
  f.version = 2;
  f.migrations = std::move(steps);
  f.save = [] { cosave::Writer w; w.u32(g.a); w.u32(g.b); return w.take(); };
  f.load = [](std::span<const std::uint8_t> b) {
    cosave::Reader r(b);
    auto a = r.u32(); auto bb = r.u32();
    if (!a || !bb || !r.done()) return false;
    g.a = *a; g.b = *bb;
    return true;
  };
  f.reset = [] { g.a = g.b = 0; ++g.resets; };
  return f;
}

Bytes v1(std::uint32_t a) { cosave::Writer w; w.u32(a); return w.take(); }

bool contains(const std::string& s, const char* part) { return s.find(part) != std::string::npos; }

void two_versions_and_a_migration() {
  Registry reg;
  CHECK(reg.add(test_family()));
  g = {};
  Report r = reg.load(cosave::fourcc("TEST"), 1, v1(41));
  CHECK(r.status == Status::migrated && r.ok());
  CHECK(g.a == 41 && g.b == 42);
  auto saved = reg.save_all();
  CHECK(saved.size() == 1 && saved[0].version == 2);
  g = {};
  CHECK(reg.load(saved[0].id, saved[0].version, saved[0].payload).status == Status::loaded);
  CHECK(g.a == 41 && g.b == 42);  // save -> load -> equal
}

void refusals_are_readable_and_reset() {
  Registry reg;
  CHECK(reg.add(test_family({})));  // version 2 with no migration from 1
  g = {7, 8, 0};
  Report r = reg.load(cosave::fourcc("TEST"), 1, v1(41));
  CHECK(r.status == Status::refused_no_migration && !r.ok());
  CHECK(contains(r.message, "TEST") && contains(r.message, "no migration from version 1 to 2"));
  CHECK(g.a == 0 && g.resets == 1);  // never half-loaded: reset
  r = reg.load(cosave::fourcc("TEST"), 3, v1(1));
  CHECK(r.status == Status::refused_newer && contains(r.message, "newer build"));
  r = reg.load(cosave::fourcc("TEST"), 0, v1(1));
  CHECK(r.status == Status::refused_bad_version);
  r = reg.load(cosave::fourcc("TEST"), 2, v1(1));  // a v2 record with a v1 payload
  CHECK(r.status == Status::refused_malformed);
  r = reg.load(cosave::fourcc("NOPE"), 1, {});
  CHECK(r.status == Status::refused_unknown_family && contains(r.message, "NOPE"));

  Registry reg2;
  CHECK(reg2.add(test_family()));
  Bytes broken{1, 2, 3};
  Bytes before = broken;
  Family f = test_family();
  CHECK(migrate(f, 1, broken).status == Status::refused_malformed);
  CHECK(broken == before);  // the bytes are unchanged on refusal
}

void registration_rules() {
  Registry reg;
  std::string why;
  CHECK(reg.add(test_family()));
  CHECK(!reg.add(test_family(), &why) && contains(why, "already registered"));  // S10a: the second is refused
  Family zero = test_family(); zero.id = cosave::fourcc("ZERO"); zero.version = 0;
  CHECK(!reg.add(zero, &why) && contains(why, "version 0"));
  Family bad = test_family({{2, lift_1_to_2}}); bad.id = cosave::fourcc("BADS");
  CHECK(!reg.add(bad, &why));  // a step from the current version
  Family twice = test_family({{1, lift_1_to_2}, {1, lift_1_to_2}}); twice.id = cosave::fourcc("TWIC");
  CHECK(!reg.add(twice, &why) && contains(why, "two migrations"));
  Family nocb = test_family(); nocb.id = cosave::fourcc("NOCB"); nocb.reset = nullptr;
  CHECK(!reg.add(nocb, &why));
  CHECK(reg.ids().size() == 1);
  CHECK(fourcc_name(cosave::fourcc("STAT")) == "STAT");
}

// Every family this tree defines, round-tripped through one registry: save -> reset -> load -> compare.
void every_family_round_trips() {
  Sheet sheet = argonia::test::marsh_hand();
  progression::Progress prog; prog.vastei = 77; prog.pending_levels = 1;
  disposition::Table disp{{5, 20}, {6, 80}};
  journal::Log log; journal::append(log, 9, 10, {201, 8, 17, 9});
  items::Table items{{3, {42, 100, std::nullopt}}};
  death::State dth{death::Pile{{1, 2, 3, 4}, 120}, death::Pos{0, 0, 0, 4}};

  struct Live { Sheet sheet; progression::Progress prog; disposition::Table disp; journal::Log log;
                items::Table items; death::State dth; } live{sheet, prog, disp, log, items, dth};
  auto fam = [](std::uint32_t id, std::function<Bytes()> save, std::function<bool(std::span<const std::uint8_t>)> load,
                std::function<void()> reset) { return Family{id, 1, {}, std::move(save), std::move(load), std::move(reset)}; };
  Registry reg;
  CHECK(reg.add(fam(progression::kStatsType, [&] { return progression::encode(live.sheet, live.prog); },
                    [&](auto b) { return progression::decode(b, live.sheet, live.prog); },
                    [&] { live.sheet = {}; live.prog = {}; })));
  CHECK(reg.add(fam(disposition::kDispositionsType, [&] { return disposition::encode(live.disp); },
                    [&](auto b) { auto t = disposition::decode(b); if (t) live.disp = *t; return t.has_value(); },
                    [&] { live.disp.clear(); })));
  CHECK(reg.add(fam(journal::kJournalType, [&] { return journal::encode(live.log); },
                    [&](auto b) { auto t = journal::decode(b); if (t) live.log = *t; return t.has_value(); },
                    [&] { live.log = {}; })));
  CHECK(reg.add(fam(items::kItemsType, [&] { return items::encode(live.items); },
                    [&](auto b) { auto t = items::decode(b); if (t) live.items = *t; return t.has_value(); },
                    [&] { live.items.clear(); })));
  CHECK(reg.add(fam(death::kDeathType, [&] { return death::encode(live.dth); },
                    [&](auto b) { auto t = death::decode(b); if (t) live.dth = *t; return t.has_value(); },
                    [&] { live.dth = {}; })));
  auto saved = reg.save_all();
  CHECK(saved.size() == 5);
  reg.reset_all();  // the scene reset leaves nothing behind
  CHECK(live.disp.empty() && live.log.entries.empty() && live.items.empty() && !live.dth.pile && live.prog.vastei == 0);
  for (const auto& rec : saved) CHECK(reg.load(rec.id, rec.version, rec.payload).status == Status::loaded);
  CHECK(live.sheet == sheet && live.prog == prog && live.disp == disp && live.log == log && live.items == items &&
        live.dth == dth);
}

}  // namespace

int main() {
  two_versions_and_a_migration();
  refusals_are_readable_and_reset();
  registration_rules();
  every_family_round_trips();
  return TEST_MAIN_RESULT("core.families");
}
