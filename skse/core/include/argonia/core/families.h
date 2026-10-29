// The save contract (1.1 §b, native map §6.1 `families`): each system registers one co-save family with an id, a
// version, save, load and reset, and a migration table. Loading an older version runs its migrations in order; a
// version with no migration, a newer version or a broken payload refuses the load with a readable message and
// leaves the family at its reset state, never half-loaded.
#pragma once
#include "argonia/core/cosave.h"

#include <cstdint>
#include <functional>
#include <span>
#include <string>
#include <vector>

namespace argonia::core::families {

using cosave::Bytes;
using cosave::Migration;

// Lifts a payload from version `from` to `from + 1`.
struct Step { std::uint32_t from; Migration lift; };

struct Family {
  std::uint32_t id = 0;              // the record type, fourcc
  std::uint32_t version = 0;         // the version this build writes, >= 1
  std::vector<Step> migrations;      // any order; at most one step per `from`
  std::function<Bytes()> save;
  std::function<bool(std::span<const std::uint8_t>)> load;  // a version-current payload; false when malformed
  std::function<void()> reset;
};

enum class Status { loaded, migrated, refused_newer, refused_no_migration, refused_malformed, refused_unknown_family,
                    refused_bad_version };
struct Report {
  Status status;
  std::string message;  // one line for the SKSE log and the player-facing notice
  bool ok() const { return status == Status::loaded || status == Status::migrated; }
};

std::string fourcc_name(std::uint32_t id);  // 'STAT' -> "STAT"

// Brings a payload of version `from` to the family's version. On refusal the bytes are unchanged.
Report migrate(const Family& f, std::uint32_t from, Bytes& payload);

class Registry {
 public:
  // Refuses a duplicate id, version 0, missing callbacks, a step outside 1..version-1 or two steps from one version.
  bool add(Family f, std::string* why = nullptr);
  const Family* find(std::uint32_t id) const;
  std::vector<std::uint32_t> ids() const;

  struct Record { std::uint32_t id; std::uint32_t version; Bytes payload; };
  std::vector<Record> save_all() const;
  // Migrates then loads one record; on any refusal the family is reset.
  Report load(std::uint32_t id, std::uint32_t version, Bytes payload);
  // Resets every family (the studio's scene reset, and new game).
  void reset_all();

 private:
  std::vector<Family> families_;
};

}  // namespace argonia::core::families
