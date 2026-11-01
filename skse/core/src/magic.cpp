#include "argonia/core/magic.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <format>

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

std::optional<msg::MagicSchool> school_of(const ModFormRow* row, std::string_view av) {
  if (row && row->school) {
    const auto name = gen::kSkillIdNames[std::size_t(*row->school)];
    for (std::size_t i = 0; i < msg::kMagicSchoolNames.size(); ++i)
      if (msg::kMagicSchoolNames[i] == name) return msg::MagicSchool(i);
  }
  for (std::size_t i = 0; i < msg::kMagicSchoolNames.size(); ++i)
    if (iequals(msg::kMagicSchoolNames[i], av)) return msg::MagicSchool(i);
  return std::nullopt;
}

std::string_view school_heading(msg::MagicSchool s) {
  static constexpr std::array<std::string_view, 6> kHeadings{"Alteration", "Conjuration", "Destruction", "Illusion",
                                                             "Mysticism", "Restoration"};
  return kHeadings[std::size_t(s)];
}

namespace {
std::string lower(std::string_view s) {
  std::string out(s);
  for (auto& c : out) c = char(std::tolower(static_cast<unsigned char>(c)));
  return out;
}
bool by_name(const Known& a, const Known& b) {
  const auto x = lower(a.name), y = lower(b.name);
  return x != y ? x < y : lower(a.id) < lower(b.id);
}
}  // namespace

msg::MagicState pane_state(std::vector<Known> known, std::vector<msg::MagicActive> effects,
                           std::optional<std::string> notice) {
  std::sort(known.begin(), known.end(), by_name);
  known.erase(std::unique(known.begin(), known.end(), [](const Known& a, const Known& b) { return iequals(a.id, b.id); }),
              known.end());
  msg::MagicState s;
  for (std::size_t i = 0; i < msg::kMagicSchoolNames.size(); ++i)
    s.groups.push_back({msg::MagicSchool(i), std::string(school_heading(msg::MagicSchool(i))), {}});
  for (const auto& k : known) {
    if (k.power) {
      s.powers.push_back({k.id, k.name, k.voice});
      continue;
    }
    s.groups[std::size_t(k.school.value_or(kNoSchool))].spells.push_back({k.id, k.name, k.cost, std::nullopt, k.left, k.right});
  }
  s.effects = std::move(effects);
  s.notice = std::move(notice);
  return s;
}

std::optional<std::string> active_detail(double magnitude, double seconds_left) {
  std::string out;
  if (magnitude > 1.5) out = std::format("{} pts", std::lround(magnitude));  // a flag effect (Waterbreathing) carries 1
  if (seconds_left >= 0.5) out += (out.empty() ? "" : ", ") + std::format("{} s", std::lround(seconds_left));
  return out.empty() ? std::nullopt : std::optional{out};
}

std::optional<std::string> equip_refusal(const Known& k, msg::Hand hand) {
  if (k.power && hand != msg::Hand::voice) return k.name + " is a power: it is readied, not held in a hand.";
  if (!k.power && hand == msg::Hand::voice) return k.name + " is a spell: ready it in a hand.";
  return std::nullopt;
}

const Known* find_known(const std::vector<Known>& known, std::string_view id) {
  for (const auto& k : known)
    if (iequals(k.id, id)) return &k;
  return nullptr;
}

std::vector<const gen::ModStockRow*> stock_of(std::string_view npc) {
  std::vector<const gen::ModStockRow*> out;
  for (const auto& r : gen::kModStock)
    if (r.npc == npc) out.push_back(&r);
  return out;
}

}  // namespace argonia::core::magic
