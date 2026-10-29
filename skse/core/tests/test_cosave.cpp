// L2: the co-save family contract (round trip, refusal of newer and broken payloads, the migration chain).
#include "check.h"
#include "argonia/core/cosave.h"
#include "argonia/core/version.h"

#include <array>
#include <cstring>

using namespace argonia::core;
using namespace argonia::core::cosave;

namespace {

void meta_round_trip() {
  Meta m{41, packed_build_version()};
  Bytes b = encode(m);
  CHECK(b.size() == 8);
  CHECK(b[0] == 41 && b[1] == 0);  // little-endian on every host
  auto back = decode_meta(b);
  CHECK(back.has_value() && *back == m);
}

void meta_refuses_wrong_lengths() {
  Bytes b = encode(Meta{1, 2});
  Bytes short_b(b.begin(), b.end() - 1);
  CHECK(!decode_meta(short_b));
  b.push_back(0);
  CHECK(!decode_meta(b));
}

void meta_current_version_loads_unchanged() {
  Bytes b = encode(Meta{7, 3});
  Bytes before = b;
  CHECK(upgrade(kMetaSpec, kMetaSpec.current, b) == LoadResult::ok);
  CHECK(b == before);
}

void newer_and_zero_versions_are_refused() {
  Bytes b = encode(Meta{7, 3});
  Bytes before = b;
  CHECK(upgrade(kMetaSpec, kMetaSpec.current + 1, b) == LoadResult::from_future);
  CHECK(upgrade(kMetaSpec, 0, b) == LoadResult::unknown_version);
  CHECK(b == before);
}

// A three-version family exercises the hook the way META's version 2 will: v1 {a}, v2 {a, b = a * 2},
// v3 {a, b, c = 9}. A broken v1 payload stops the chain and leaves the bytes untouched.
bool lift_1_to_2(Bytes& b) {
  Reader r(b);
  auto a = r.u32();
  if (!a || !r.done()) return false;
  Writer w;
  w.u32(*a);
  w.u32(*a * 2);
  b = w.take();
  return true;
}
bool lift_2_to_3(Bytes& b) {
  if (b.size() != 8) return false;
  Writer w;
  w.u32(9);
  Bytes tail = w.take();
  b.insert(b.end(), tail.begin(), tail.end());
  return true;
}
constexpr std::array<Migration, 2> kLifts{lift_1_to_2, lift_2_to_3};
const FamilySpec kTest{fourcc("TEST"), 3, kLifts};

void migration_chain_runs_in_order() {
  Writer w;
  w.u32(5);
  Bytes b = w.take();
  CHECK(upgrade(kTest, 1, b) == LoadResult::migrated);
  Reader r(b);
  CHECK(r.u32() == 5u);
  CHECK(r.u32() == 10u);
  CHECK(r.u32() == 9u);
  CHECK(r.done());
}

void migration_from_middle_version() {
  Writer w;
  w.u32(5);
  w.u32(10);
  Bytes b = w.take();
  CHECK(upgrade(kTest, 2, b) == LoadResult::migrated);
  CHECK(b.size() == 12);
}

void broken_payload_stops_and_keeps_bytes() {
  Bytes b{1, 2, 3};
  Bytes before = b;
  CHECK(upgrade(kTest, 1, b) == LoadResult::malformed);
  CHECK(b == before);
}

void spec_with_missing_lift_is_refused() {
  const FamilySpec gap{fourcc("GAPS"), 3, std::span<const Migration>(kLifts).first(1)};
  Bytes b{0, 0, 0, 0};
  CHECK(upgrade(gap, 1, b) == LoadResult::unknown_version);
}

void fourcc_and_version() {
  CHECK(fourcc("ARGN") == 0x4152474Eu);
  CHECK(fourcc("TOO LONG") == 0u);
  CHECK(kUniqueId == fourcc("ARGN"));
  CHECK(packed_build_version() == (kVersionMajor << 16 | kVersionMinor << 8 | kVersionPatch));
  CHECK(std::strlen(kVersionString) >= 5);
}

}  // namespace

int main() {
  meta_round_trip();
  meta_refuses_wrong_lengths();
  meta_current_version_loads_unchanged();
  newer_and_zero_versions_are_refused();
  migration_chain_runs_in_order();
  migration_from_middle_version();
  broken_payload_stops_and_keeps_bytes();
  spec_with_missing_lift_is_refused();
  fourcc_and_version();
  return TEST_MAIN_RESULT("core.cosave");
}
