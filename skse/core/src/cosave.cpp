#include "argonia/core/cosave.h"

#include "argonia/core/version.h"

namespace argonia::core::cosave {

LoadResult upgrade(const FamilySpec& spec, std::uint32_t stored_version, Bytes& payload) {
  if (stored_version > spec.current) return LoadResult::from_future;
  if (stored_version == 0 || spec.lifts.size() + 1 != spec.current) return LoadResult::unknown_version;
  if (stored_version == spec.current) return LoadResult::ok;
  Bytes work = payload;
  for (std::uint32_t v = stored_version; v < spec.current; ++v) {
    if (!spec.lifts[v - 1](work)) return LoadResult::malformed;
  }
  payload = std::move(work);
  return LoadResult::migrated;
}

const char* to_string(LoadResult r) {
  switch (r) {
    case LoadResult::ok: return "ok";
    case LoadResult::migrated: return "migrated";
    case LoadResult::from_future: return "from a newer build";
    case LoadResult::unknown_version: return "unknown version";
    case LoadResult::malformed: return "malformed";
  }
  return "?";
}

void Writer::u32(std::uint32_t v) {
  for (int i = 0; i < 4; ++i) bytes_.push_back(std::uint8_t(v >> (8 * i)));
}

std::optional<std::uint32_t> Reader::u32() {
  if (bytes_.size() - pos_ < 4) return std::nullopt;
  std::uint32_t v = 0;
  for (int i = 0; i < 4; ++i) v |= std::uint32_t(bytes_[pos_ + i]) << (8 * i);
  pos_ += 4;
  return v;
}

// META has had one version; its lift list is empty until version 2 exists.
const FamilySpec kMetaSpec{kMetaType, 1, {}};

Bytes encode(const Meta& m) {
  Writer w;
  w.u32(m.save_count);
  w.u32(m.written_by);
  return w.take();
}

std::optional<Meta> decode_meta(std::span<const std::uint8_t> payload) {
  Reader r(payload);
  auto count = r.u32();
  auto by = r.u32();
  if (!count || !by || !r.done()) return std::nullopt;
  return Meta{*count, *by};
}

std::uint32_t packed_build_version() { return kVersionMajor << 16 | kVersionMinor << 8 | kVersionPatch; }

}  // namespace argonia::core::cosave
