#include "argonia/core/seam.h"

#include <algorithm>
#include <array>
#include <cstdio>

namespace argonia::core::seam {

namespace {

using conditions::Arg;
using conditions::Term;

// seasonIs's values are the weather calendar's season ids (the enum's names in tables_weather.h).
static_assert(gen::kSeasons == 3, "a season was added to tables_weather.h: name it here");
std::string_view season_name(weather::Season s) {
  switch (s) {
    case weather::Season::dry: return "dry";
    case weather::Season::hatching: return "hatching";
    case weather::Season::wet: return "wet";
  }
  return {};
}

// The STAT family's stored range for an attribute (schema/families.json): an encoding bound, not a rule.
constexpr double kAttributeMin = 0, kAttributeMax = 255;

const std::string* text(std::span<const Arg> keys, std::size_t i) {
  return i < keys.size() ? std::get_if<std::string>(&keys[i]) : nullptr;
}

template <class T, class Dec>
std::function<bool(std::span<const std::uint8_t>)> into(T& slot, Dec dec) {
  return [&slot, dec](std::span<const std::uint8_t> b) {
    auto t = dec(b);
    if (t) slot = std::move(*t);
    return t.has_value();
  };
}

families::Family fam(std::uint32_t id, std::uint32_t version, std::function<cosave::Bytes()> save,
                     std::function<bool(std::span<const std::uint8_t>)> load, std::function<void()> reset) {
  return families::Family{id, version, {}, std::move(save), std::move(load), std::move(reset)};
}

}  // namespace

const gen::FormRow* form(std::string_view id) {
  auto it = std::lower_bound(gen::kForms.begin(), gen::kForms.end(), id,
                             [](const gen::FormRow& r, std::string_view v) { return r.id < v; });
  return it != gen::kForms.end() && it->id == id ? &*it : nullptr;
}

namespace {
constexpr char ascii_lower(char c) { return c >= 'A' && c <= 'Z' ? char(c - 'A' + 'a') : c; }
}  // namespace

const gen::FormRow* form_at(std::string_view plugin, std::uint32_t local) {
  for (const auto& r : gen::kForms)
    if (r.local == local && r.plugin.size() == plugin.size() &&
        std::equal(r.plugin.begin(), r.plugin.end(), plugin.begin(),
                   [](char a, char b) { return ascii_lower(a) == ascii_lower(b); }))  // Skyrim's file names ignore case
      return &r;
  return nullptr;
}

cosave::Bytes encode(const Watch& w) {
  cosave::Writer out;
  out.u32(std::uint32_t(w.quests.size()));
  for (Key k : w.quests) out.u32(k);
  return out.take();
}

std::optional<Watch> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  auto n = r.u32();
  if (!n) return std::nullopt;
  Watch w;
  std::optional<Key> last;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto k = r.u32();
    if (!k || (last && *k <= *last)) return std::nullopt;  // keys rise: a set, never a repeat
    w.quests.insert(*k);
    last = k;
  }
  if (!r.done()) return std::nullopt;
  return w;
}

std::vector<std::string> bind(families::Registry& reg, State& s) {
  std::vector<std::string> refused;
  auto add = [&](families::Family f) {
    std::string why;
    if (!reg.add(std::move(f), &why)) refused.push_back(why);
  };
  add(fam(cosave::kMetaType, cosave::kMetaSpec.current, [&s] { return cosave::encode(s.meta); },
          into(s.meta, cosave::decode_meta), [&s] { s.meta = {}; }));
  add(fam(progression::kStatsType, 1, [&s] { return progression::encode(s.sheet, s.prog); },
          [&s](std::span<const std::uint8_t> b) {
            Sheet sh;
            progression::Progress p;
            if (!progression::decode(b, sh, p)) return false;
            s.sheet = std::move(sh);
            s.prog = p;
            return true;
          },
          [&s] { s.sheet = {}; s.prog = {}; }));
  add(fam(disposition::kDispositionsType, 1, [&s] { return disposition::encode(s.disp); },
          into(s.disp, disposition::decode), [&s] { s.disp.clear(); }));
  add(fam(journal::kJournalType, 1, [&s] { return journal::encode(s.log); }, into(s.log, journal::decode),
          [&s] { s.log = {}; }));
  add(fam(items::kItemsType, 1, [&s] { return items::encode(s.items); }, into(s.items, items::decode),
          [&s] { s.items.clear(); }));
  add(fam(death::kDeathType, 1, [&s] { return death::encode(s.death); }, into(s.death, death::decode),
          [&s] { s.death = {}; }));
  add(fam(quest_state::kQuestStateType, 1, [&s] { return quest_state::encode(s.quests); },
          into(s.quests, quest_state::decode), [&s] { s.quests = {}; }));
  add(fam(topics::kTopicsType, 1, [&s] { return topics::encode(s.known); }, into(s.known, topics::decode),
          [&s] { s.known = {}; }));
  add(fam(kWatchType, 1, [&s] { return encode(s.watch); }, into(s.watch, [](auto b) { return decode(b); }),
          [&s] { s.watch = {}; }));
  add(families::Family{chart::kChartType, chart::kChartVersion, chart::migrations(),
                       [&s] { return chart::encode(s.chart); }, into(s.chart, chart::decode), [&s] { s.chart = {}; }});
  return refused;
}

void on_save(State& s) {
  ++s.meta.save_count;
  s.meta.written_by = cosave::packed_build_version();
}

std::string digest(const families::Registry& reg, std::uint32_t id) {
  const families::Family* f = reg.find(id);
  if (!f) return {};
  std::uint64_t h = 1469598103934665603ull;
  for (std::uint8_t b : f->save()) h = (h ^ b) * 1099511628211ull;
  char buf[17];
  std::snprintf(buf, sizeof buf, "%016llx", static_cast<unsigned long long>(h));
  return buf;
}

std::optional<weather::Season> season(const Date& d) {
  auto doy = weather::day_of_year(d.month, d.day);
  if (!doy) return std::nullopt;
  return weather::season_of(*doy);
}

int disposition_of(const State& s, std::string_view npc) {
  if (auto it = s.disp.find(key(npc)); it != s.disp.end()) return it->second;
  disposition::Priors p;
  p.personality = s.sheet.a[AttrId::personality];
  return disposition::base({}, p);
}

std::string variant_flag(std::string_view place, std::string_view variant) {
  return std::string(place) + "#" + std::string(variant);
}
std::string price_counter(std::string_view service) { return "price#" + std::string(service); }

// --- WorldFacts ---------------------------------------------------------------------------------------------

std::optional<bool> WorldFacts::truth(Term t, std::span<const Arg> keys) const {
  const std::string* a = text(keys, 0);
  const std::string* b = text(keys, 1);
  switch (t) {
    case Term::knowsTopic:
      if (a) return s_.known.knows(*a);
      break;
    case Term::topicHeardFrom:
      if (a && b) return s_.known.heard_from(*a, *b);
      break;
    case Term::flag:
      if (a) return quest_state::flag(s_.quests, *a);
      break;
    case Term::localVariantActive:
      if (a && b) return quest_state::flag(s_.quests, variant_flag(*a, *b));
      break;
    case Term::npcAlive:
      if (a) return e_.alive(*a);
      break;
    case Term::objectiveComplete:
      if (a && b) {
        auto view = e_.quest(*a);
        const quest_runtime::Graph* g = nullptr;
        for (const auto& x : graphs_)
          if (x.id == *a) g = &x;
        if (!view || !g) break;
        for (const auto& st : g->stages)
          for (const auto& o : st.objectives)
            if (o.id == *b) return std::find(view->done.begin(), view->done.end(), o.index) != view->done.end();
      }
      break;
    default:
      break;
  }
  return std::nullopt;
}

std::optional<double> WorldFacts::number(Term t, std::span<const Arg> keys) const {
  const std::string* a = text(keys, 0);
  const std::string* b = text(keys, 1);
  switch (t) {
    case Term::counterAtLeast:
      if (a) return quest_state::counter(s_.quests, *a);
      break;
    case Term::settlementStandingAtLeast:
      if (a) return quest_state::counter(s_.quests, *a);
      break;
    case Term::deedCountAtLeast:
      if (a && b) return quest_state::deeds(s_.quests, *a, *b);
      break;
    case Term::dispositionAtLeast:
      if (a) return disposition_of(s_, *a);
      break;
    case Term::levelAtLeast:
      return s_.sheet.level;
    case Term::attributeAtLeast:
      if (a)
        if (auto at = attribute_named(*a)) return s_.sheet.a[*at];
      break;
    case Term::skillAtLeast:
      if (a)
        for (std::size_t i = 0; i < gen::kSkillIdNames.size(); ++i)
          if (gen::kSkillIdNames[i] == *a) return s_.sheet.s.v[i];
      break;
    case Term::hasItem:
      if (a)
        if (auto n = e_.item_count(*a)) return *n;
      break;
    case Term::goldAtLeast:
      if (auto g = e_.gold()) return *g;
      break;
    case Term::questStage:
      if (a)
        if (auto v = e_.quest(*a)) return v->stage;
      break;
    default:
      break;
  }
  return std::nullopt;
}

std::optional<std::string> WorldFacts::state(Term t, std::span<const Arg>) const {
  if (t == Term::seasonIs)
    if (auto d = e_.date())
      if (auto se = season(*d)) return std::string(season_name(*se));
  return std::nullopt;
}

// --- Session ------------------------------------------------------------------------------------------------

namespace {

// The action verbs over the state and the engine writes.
class Fx : public actions::Effects {
 public:
  Fx(State& s, EngineWrites& w) : s_(s), w_(w) {}
  bool takeGold(int n) override { return w_.take_gold(n); }
  bool giveGold(int n) override { return w_.give_gold(n); }
  bool takeItem(std::string_view i, int n) override { return w_.take_item(i, n); }
  bool giveItem(std::string_view i, int n) override { return w_.give_item(i, n); }
  bool setFlag(std::string_view f, bool v) override { quest_state::set_flag(s_.quests, f, v); return true; }
  bool grantTopic(std::string_view t) override { s_.known.learn(t); return true; }
  bool applyLocalVariant(std::string_view place, std::string_view variant) override {
    quest_state::set_flag(s_.quests, variant_flag(place, variant), true);
    return true;
  }
  bool setPrice(std::string_view service, int price) override {
    const auto c = price_counter(service);
    quest_state::add_counter(s_.quests, c, price - quest_state::counter(s_.quests, c));
    return true;
  }
  bool changeDisposition(std::string_view npc, int delta) override {
    s_.disp[key(npc)] = disposition::apply(disposition_of(s_, npc), {delta});
    return true;
  }
  bool changeSettlementStanding(std::string_view settlement, int delta) override {
    quest_state::add_counter(s_.quests, settlement, delta);
    return true;
  }
  bool other(const actions::Action&) override { return false; }  // its chunk gives it an entry (2.5, 2.12)

 private:
  State& s_;
  EngineWrites& w_;
};

}  // namespace

const quest_runtime::Graph* Session::graph(std::string_view quest) const {
  for (const auto& g : graphs_)
    if (g.id == quest) return &g;
  return nullptr;
}

bool Session::watch(std::string_view quest, std::string* why) {
  if (!graph(quest)) {
    if (why) *why = "WatchQuest: " + std::string(quest) + " has no stage graph (quests.h)";
    return false;
  }
  s_.watch.quests.insert(key(quest));
  return true;
}

bool Session::unwatch(std::string_view quest) { return s_.watch.quests.erase(key(quest)) != 0; }

bool Session::add_journal_entry(std::string_view quest, std::int32_t stage, int kind, const Date& at, std::string* why) {
  if (kind < 0 || kind > int(journal::Kind::fail) || stage < 0) {
    if (why) *why = "AddJournalEntry: kind " + std::to_string(kind) + " or stage " + std::to_string(stage) + " out of range";
    return false;
  }
  const journal::GameDate d{at.year, at.month + 1, at.day, at.hour};
  if (!journal::append(s_.log, key(quest), std::uint32_t(stage), d, journal::Kind(kind))) {
    if (why) *why = "AddJournalEntry: " + std::string(quest) + " stage " + std::to_string(stage) + " already logged or the quest has ended";
    return false;
  }
  return true;
}

actions::Outcome Session::act(std::string_view verb, std::vector<conditions::Arg> args) {
  auto a = actions::make(verb, std::move(args));
  if (!a) return actions::Outcome{false, 0, {a.error()}};
  const actions::Action list[] = {*a};
  return act(list);
}

actions::Outcome Session::act(std::span<const actions::Action> list) {
  Fx fx(s_, w_);
  return actions::run(list, facts(), fx);
}

std::vector<Order> Session::step() const {
  std::vector<Order> out;
  const WorldFacts f = facts();
  for (const auto& g : graphs_) {
    if (!s_.watch.quests.count(key(g.id))) continue;
    auto view = e_.quest(g.id);
    if (!view) continue;
    auto st = quest_runtime::step(g, {view->stage, view->done}, f);
    if (st.completed.empty() && !st.set_stage) continue;
    out.push_back({g.id, std::move(st.completed), st.set_stage});
  }
  return out;
}

std::vector<Order> InFlight::filter(std::vector<Order> orders) {
  std::vector<Order> out;
  for (auto& o : orders) {
    auto& sent = sent_[o.quest];
    std::vector<std::uint16_t> fresh;
    for (auto i : o.completed)
      if (sent.done.insert(i).second) fresh.push_back(i);
    o.completed = std::move(fresh);
    if (o.set_stage && sent.stage == o.set_stage) o.set_stage.reset();
    else if (o.set_stage) sent.stage = o.set_stage;
    if (!o.completed.empty() || o.set_stage) out.push_back(std::move(o));
  }
  return out;
}

void InFlight::forget(std::string_view quest) {
  if (auto it = sent_.find(quest); it != sent_.end()) sent_.erase(it);
}

// --- Router -------------------------------------------------------------------------------------------------

std::vector<std::string> install(router::Router& r, router::Handler on_dialogue) {
  std::vector<std::string> log;
  std::string why;
  for (auto h : {router::HookId::menuOpenClose, router::HookId::dialogueIntercept})
    if (!r.install(h, &why)) log.push_back("refused: " + why);
  if (!r.handle(router::SurfaceId::dialogueMenu, std::move(on_dialogue), &why)) log.push_back("refused: " + why);
  auto lines = r.load_log();
  lines.insert(lines.end(), log.begin(), log.end());
  if (r.install(router::HookId::dialogueIntercept, &why))
    lines.push_back("ERROR: a second dialogueIntercept install was accepted");
  else
    lines.push_back("second registration refused: " + why);
  return lines;
}

// --- Attributes ---------------------------------------------------------------------------------------------

std::span<const Mirror> attribute_mirrors() {
  // av-audit.md's recommendation (2026-10-30): seven obsolete actor values no plugin or script in the stack reads.
  static constexpr std::array<Mirror, gen::kAttrIdCount> kMirrors{{
      {AttrId::strength, "Fame"},
      {AttrId::intelligence, "Infamy"},
      {AttrId::willpower, "LastFlattered"},
      {AttrId::agility, "FavorPointsBonus"},
      {AttrId::speed, "FavorsPerDay"},
      {AttrId::endurance, "FavorsPerDayTimer"},
      {AttrId::personality, "IgnoreCrippledLimbs"},
  }};
  return kMirrors;
}

std::optional<AttrId> attribute_named(std::string_view name) {
  for (std::size_t i = 0; i < gen::kAttrIdNames.size(); ++i)
    if (gen::kAttrIdNames[i] == name) return AttrId(i);
  return std::nullopt;
}

double attribute(const State& s, AttrId a) { return s.sheet.a[a]; }

double set_attribute(State& s, AttrId a, double v) {
  s.sheet.a[a] = std::clamp(v, kAttributeMin, kAttributeMax);
  return s.sheet.a[a];
}

double set_skill(State& s, SkillId k, double v) {
  s.sheet.s[k] = std::clamp(v, 0.0, gen::progression::skill_cap);
  return s.sheet.s[k];
}

}  // namespace argonia::core::seam
