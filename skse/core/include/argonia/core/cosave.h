// Versioned co-save families (CLAUDE.md: "new state lives in ArgoniaCore's versioned co-save families"; the
// seam's seed for 1.1 §b). A family is one SKSE record type with a version and a byte payload. This header is
// the whole contract: encoding, decoding and the migration chain, with no SKSE type, so it is tested on Linux.
//
// Adding a family version: bump the family's `current`, append one Migration that lifts the previous version's
// payload to the new one, and add a test with a payload of the previous version. Migrations are never removed.
#pragma once
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::cosave {

using Bytes = std::vector<std::uint8_t>;

// SKSE's record types and unique ids are four characters packed big-end first ('ARGN').
constexpr std::uint32_t fourcc(std::string_view s) {
  return s.size() == 4 ? (std::uint32_t(std::uint8_t(s[0])) << 24) | (std::uint32_t(std::uint8_t(s[1])) << 16) |
                             (std::uint32_t(std::uint8_t(s[2])) << 8) | std::uint32_t(std::uint8_t(s[3]))
                       : 0;
}

inline constexpr std::uint32_t kUniqueId = fourcc("ARGN");  // ArgoniaCore's co-save id

// Lifts a payload from version v to v + 1 in place; false when the bytes are not a valid version-v payload.
using Migration = bool (*)(Bytes&);

struct FamilySpec {
  std::uint32_t type;                  // record type, fourcc
  std::uint32_t current;               // the version this build writes, >= 1
  std::span<const Migration> lifts;    // lifts[i] takes version i + 1 to i + 2; size() == current - 1
};

enum class LoadResult { ok, migrated, from_future, unknown_version, malformed };

// Brings a stored payload to spec.current. The payload is changed only on ok or migrated.
LoadResult upgrade(const FamilySpec& spec, std::uint32_t stored_version, Bytes& payload);

const char* to_string(LoadResult r);

// Little-endian field writer and reader, so a payload never depends on a struct's layout.
class Writer {
 public:
  void u8(std::uint8_t v);
  void u32(std::uint32_t v);
  void u64(std::uint64_t v);
  void i32(std::int32_t v);
  void f64(double v);
  void str(std::string_view s);  // a u32 length, then the bytes
  Bytes take() { return std::move(bytes_); }

 private:
  Bytes bytes_;
};

class Reader {
 public:
  explicit Reader(std::span<const std::uint8_t> b) : bytes_(b) {}
  std::optional<std::uint8_t> u8();
  std::optional<std::uint32_t> u32();
  std::optional<std::uint64_t> u64();
  std::optional<std::int32_t> i32();
  std::optional<double> f64();
  std::optional<std::string> str();
  bool done() const { return pos_ == bytes_.size(); }

 private:
  std::span<const std::uint8_t> bytes_;
  std::size_t pos_ = 0;
};

// The first family, META: what ArgoniaCore knows about the save itself. Version 1.
struct Meta {
  std::uint32_t save_count = 0;  // saves this playthrough has written with ArgoniaCore loaded
  std::uint32_t written_by = 0;  // packed build version (major << 16 | minor << 8 | patch) of the last writer
  bool operator==(const Meta&) const = default;
};

inline constexpr std::uint32_t kMetaType = fourcc("META");
extern const FamilySpec kMetaSpec;

Bytes encode(const Meta& m);
std::optional<Meta> decode_meta(std::span<const std::uint8_t> payload);  // a version-current payload

std::uint32_t packed_build_version();

}  // namespace argonia::core::cosave
