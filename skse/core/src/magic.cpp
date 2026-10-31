#include "argonia/core/magic.h"

#include <algorithm>
#include <cctype>

namespace argonia::core::magic {

namespace {

bool iequals(std::string_view a, std::string_view b) {
  return a.size() == b.size() && std::equal(a.begin(), a.end(), b.begin(), [](char x, char y) {
           return std::tolower(static_cast<unsigned char>(x)) == std::tolower(static_cast<unsigned char>(y));
         });
}

}  // namespace

std::vector<const ModFormRow*> rows_of(std::string_view plugin) {
  std::vector<const ModFormRow*> out;
  for (const auto& r : gen::kModForms)
    if (iequals(r.plugin, plugin)) out.push_back(&r);
  return out;
}

const ModFormRow* find(std::string_view plugin, std::uint32_t local_id) {
  for (const auto& r : gen::kModForms)
    if (r.local_id == local_id && iequals(r.plugin, plugin)) return &r;
  return nullptr;
}

std::optional<std::string_view> rename(const ModFormRow& r) {
  return r.name.empty() ? std::nullopt : std::optional{r.name};
}

std::optional<std::string_view> redescribe(const ModFormRow& r) {
  if (r.description.empty() || (r.form_type != "MGEF" && r.form_type != "MESG")) return std::nullopt;
  return r.description;
}

std::optional<std::string_view> school_av(const ModFormRow& r, std::string_view current) {
  if (r.form_type != "MGEF" || !r.school || r.school_av.empty() || iequals(r.school_av, current)) return std::nullopt;
  return r.school_av;
}

std::vector<const ModFormRow*> unshown_schools() {
  std::vector<const ModFormRow*> out;
  for (const auto& r : gen::kModForms)
    if (r.school && r.school_av.empty()) out.push_back(&r);
  return out;
}

}  // namespace argonia::core::magic
