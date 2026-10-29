// The L2 round trip of the save contract (1.1 §b): every family's payload layout is declared once as data
// (skse/core/schema/families.json, generated into generated/argonia/core/family_layouts.h by tools/schema_gen), and
// `check` proves each registered family against it: sampled payloads load and save back byte for byte, a truncated
// or padded payload is refused, the reset state round-trips, each older version either migrates to a payload of
// the current layout or refuses with a readable message, as its schema says.
#pragma once
#include "argonia/core/families.h"

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace argonia::core::roundtrip {

using cosave::Bytes;

enum class Kind : std::uint8_t { u8, u32, u64, i32, f64, str, repeat, list, flag };

// One field of a payload. Numbers are inclusive [lo, hi]; `repeat` is `count` copies of `of` with no prefix; `list`
// is a u32 count (<= count) then that many `of`, and `keyed` lists hold strictly increasing first fields (a map);
// `flag` is a u8 0 or 1, then `of` when 1.
struct Item {
  Kind kind;
  std::string name;
  double lo = 0, hi = 0;
  std::uint32_t count = 0;
  bool keyed = false;
  std::vector<Item> of;
};
using Layout = std::vector<Item>;

Item u8(std::string name, double lo = 0, double hi = 255);
Item u32(std::string name, double lo = 0, double hi = 4294967295.0);
Item u64(std::string name, double lo = 0, double hi = 9007199254740991.0);
Item i32(std::string name, double lo = -2147483648.0, double hi = 2147483647.0);
Item f64(std::string name, double lo = -1e6, double hi = 1e6);
Item str(std::string name);
Item repeat(std::string name, std::size_t count, Layout of);
Item list(std::string name, std::size_t max_count, Layout of, bool keyed = false);
Item flag(std::string name, Layout of);

struct VersionSchema {
  std::uint32_t version;
  bool migrates;  // an older version: true when the family lifts it, false when loading it must be refused
  Layout layout;
};

struct FamilySchema {
  std::uint32_t id;
  std::string module;
  bool test_only;
  std::vector<VersionSchema> versions;  // ascending; the last is the version the build writes
  std::uint32_t current() const { return versions.empty() ? 0 : versions.back().version; }
};

// A payload that fits the layout, the same for the same seed.
Bytes sample(const Layout& layout, std::uint64_t seed);
// nullopt when `bytes` fits the layout exactly, else where and why not.
std::optional<std::string> conforms(const Layout& layout, std::span<const std::uint8_t> bytes);

// Every way the registered family departs from its schema, one readable line each; empty when it holds.
std::vector<std::string> check(families::Registry& reg, const FamilySchema& schema, int samples = 24);

}  // namespace argonia::core::roundtrip
