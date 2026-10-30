// The parchment chart's revealed cells (1.2 §e): the exterior cells of the province the player has entered, as the
// `chart` co-save family (CHRT). ArgoniaCore marks the player's cell on every cell change in ARG_Province; the
// chart view masks its revealed layer by the set (views::chart_state). The set only grows.
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/families.h"

#include <compare>
#include <cstdint>
#include <map>
#include <optional>
#include <set>
#include <span>
#include <string_view>
#include <vector>

namespace argonia::core::chart {

// One exterior cell of the worldspace grid (Skyrim's cell coordinates).
struct Cell {
  std::int32_t x = 0, y = 0;
  auto operator<=>(const Cell&) const = default;
};

// The worldspace whose exterior cells reveal (tools/argonia_world/terrain/world.py's EDID).
inline constexpr std::string_view kWorldspace = "ARG_Province";

// The stored range of a cell coordinate (schema/families.json): an encoding bound, wider than any worldspace.
inline constexpr std::int32_t kCellMin = -32768, kCellMax = 32767;

// Columns by x, each the rows (y) revealed in it. A column read from a save with no rows is kept as it came, so a
// load and a save give the same bytes.
struct Discovered {
  std::map<std::int32_t, std::set<std::int32_t>> columns;
  bool operator==(const Discovered&) const = default;
};

// Marks the cell revealed; true when it was not before. A cell outside the stored range is refused (false).
bool reveal(Discovered& d, Cell c);
bool revealed(const Discovered& d, Cell c);
std::size_t count(const Discovered& d);
std::vector<Cell> cells(const Discovered& d);  // x then y, rising

inline constexpr std::uint32_t kChartType = cosave::fourcc("CHRT");
inline constexpr std::uint32_t kChartVersion = 1;
// The migration hook: the steps that lift an older CHRT payload to kChartVersion (one per older version, appended
// with the version that needs it). Version 1 is the first, so there are none yet.
std::vector<families::Step> migrations();

cosave::Bytes encode(const Discovered& d);
std::optional<Discovered> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::chart
