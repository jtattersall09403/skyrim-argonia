#include "argonia/core/families.h"

#include <algorithm>

namespace argonia::core::families {

std::string fourcc_name(std::uint32_t id) {
  std::string s;
  for (int shift = 24; shift >= 0; shift -= 8) {
    const char ch = char((id >> shift) & 0xFF);
    s += (ch >= ' ' && ch <= '~') ? ch : '?';
  }
  return s;
}

namespace {

const Step* step_from(const Family& f, std::uint32_t v) {
  for (const auto& s : f.migrations)
    if (s.from == v) return &s;
  return nullptr;
}

std::string head(const Family& f, std::uint32_t from) {
  return "co-save family " + fourcc_name(f.id) + ": saved at version " + std::to_string(from) +
         ", this build reads version " + std::to_string(f.version);
}

}  // namespace

Report migrate(const Family& f, std::uint32_t from, Bytes& payload) {
  if (from == 0) return {Status::refused_bad_version, head(f, from) + "; version 0 is never written, load refused"};
  if (from > f.version)
    return {Status::refused_newer, head(f, from) + "; the save is from a newer build, load refused"};
  if (from == f.version) return {Status::loaded, head(f, from) + "; loaded"};
  Bytes work = payload;
  for (std::uint32_t v = from; v < f.version; ++v) {
    const Step* s = step_from(f, v);
    if (!s)
      return {Status::refused_no_migration, head(f, from) + " and has no migration from version " + std::to_string(v) +
                                                " to " + std::to_string(v + 1) + "; load refused, the family is reset"};
    if (!s->lift(work))
      return {Status::refused_malformed, head(f, from) + "; the version " + std::to_string(v) +
                                             " payload is broken, load refused, the family is reset"};
  }
  payload = std::move(work);
  return {Status::migrated, head(f, from) + "; migrated and loaded"};
}

bool Registry::add(Family f, std::string* why) {
  auto refuse = [&](std::string m) {
    if (why) *why = "co-save family " + fourcc_name(f.id) + ": " + m;
    return false;
  };
  if (find(f.id)) return refuse("already registered");
  if (f.version == 0) return refuse("version 0");
  if (!f.save || !f.load || !f.reset) return refuse("save, load and reset are all required");
  for (const auto& s : f.migrations) {
    if (s.from == 0 || s.from >= f.version || !s.lift) return refuse("a migration outside 1.." + std::to_string(f.version));
    if (std::count_if(f.migrations.begin(), f.migrations.end(), [&](const Step& o) { return o.from == s.from; }) > 1)
      return refuse("two migrations from version " + std::to_string(s.from));
  }
  families_.push_back(std::move(f));
  return true;
}

const Family* Registry::find(std::uint32_t id) const {
  for (const auto& f : families_)
    if (f.id == id) return &f;
  return nullptr;
}

std::vector<std::uint32_t> Registry::ids() const {
  std::vector<std::uint32_t> out;
  for (const auto& f : families_) out.push_back(f.id);
  return out;
}

std::vector<Registry::Record> Registry::save_all() const {
  std::vector<Record> out;
  for (const auto& f : families_) out.push_back({f.id, f.version, f.save()});
  return out;
}

Report Registry::load(std::uint32_t id, std::uint32_t version, Bytes payload) {
  const Family* f = find(id);
  if (!f) return {Status::refused_unknown_family, "co-save record " + fourcc_name(id) + ": no such family, skipped"};
  Report r = migrate(*f, version, payload);
  if (r.ok() && !f->load(payload)) {
    r = {Status::refused_malformed, head(*f, version) + "; the payload is broken, load refused, the family is reset"};
  }
  if (!r.ok()) f->reset();
  return r;
}

void Registry::reset_all() {
  for (const auto& f : families_) f.reset();
}

}  // namespace argonia::core::families
