#include "argonia/core/topics.h"

#include <algorithm>
#include <cctype>

namespace argonia::core::topics {

using conditions::Arg;
using conditions::Term;

std::uint32_t key(std::string_view id) {
  std::uint32_t h = 2166136261u;  // FNV-1a's offset basis and prime (the algorithm, not a rule's number)
  for (unsigned char c : id) h = (h ^ c) * 16777619u;
  return h;
}

std::optional<LineType> line_type(std::string_view id) {
  if (id == "greeting") return LineType::greeting;
  if (id == "dialogue") return LineType::dialogue;
  if (id == "goodbye") return LineType::goodbye;
  return std::nullopt;
}

namespace {

std::string lower(std::string_view s) {
  std::string out(s);
  for (auto& c : out) c = char(std::tolower(static_cast<unsigned char>(c)));
  return out;
}

// A letter or digit; an apostrophe ends a word, so a possessive ("Claywater's") still links its topic.
bool word_char(char c) { return std::isalnum(static_cast<unsigned char>(c)) != 0; }

bool reads_disposition(const Pred& p) {
  if (p.term == Term::dispositionAtLeast || p.term == Term::speakerDispositionAtLeast) return true;
  return std::any_of(p.children.begin(), p.children.end(), reads_disposition);
}

std::optional<Answer> first(const Store& s, std::string_view topic, LineType t, const Speaker& sp, const Known& k,
                            const Facts& host) {
  TalkFacts f(sp, k, host);
  for (const Line* l : s.candidates(sp.id, topic, t))
    if (!l->available || conditions::evaluate_valid(*l->available, f).holds()) return words_at(*l, sp.disposition);
  return std::nullopt;
}

}  // namespace

std::expected<Store, std::vector<std::string>> Store::build(std::vector<Topic> topics, std::vector<Line> lines) {
  Store s;
  std::vector<std::string> err;
  s.topics_ = std::move(topics);
  s.lines_ = std::move(lines);
  for (std::size_t i = 0; i < s.topics_.size(); ++i) {
    const auto& t = s.topics_[i];
    auto [it, fresh] = s.by_key_.emplace(key(t.id), i);
    if (!fresh) err.push_back(t.id + ": its key collides with " + s.topics_[it->second].id);
    if (t.label.empty()) err.push_back(t.id + ": no label");
    auto add = [&](std::string f) {
      if (!f.empty()) s.forms_[static_cast<unsigned char>(f[0])].emplace_back(std::move(f), i);
    };
    add(lower(t.label));
    for (const auto& f : t.forms) add(lower(f));
  }
  for (auto& bucket : s.forms_)
    std::stable_sort(bucket.begin(), bucket.end(),
                     [](const auto& a, const auto& b) { return a.first.size() > b.first.size(); });
  for (std::size_t i = 0; i < s.lines_.size(); ++i) {
    const Line& l = s.lines_[i];
    const bool has_topic = !l.topic.empty();
    if ((l.type == LineType::dialogue) != has_topic)
      err.push_back(l.id + (has_topic ? ": only a dialogue line answers a topic" : ": a dialogue line needs a topic"));
    const Topic* t = has_topic ? s.topic(l.topic) : nullptr;
    if (has_topic && !t) err.push_back(l.id + ": unknown topic " + l.topic);
    for (const auto& ln : l.links)
      if (!s.topic(ln)) err.push_back(l.id + ": links unknown topic " + ln);
    if (l.available) {
      if (auto e = conditions::check(*l.available)) err.push_back(l.id + ": " + *e);
    }
    for (const auto& a : l.on_delivered)
      if (auto e = actions::check(a)) err.push_back(l.id + ": " + *e);
    if (l.words.empty()) err.push_back(l.id + ": no words");
    s.index_[Slot{key(l.speaker), l.type, key(l.topic)}].push_back(i);
  }
  // Lines carry no authored order (a person's lines file is a set), so within a slot a conditioned line comes before
  // an unconditioned one, the store's order kept otherwise: the plain line is the fallback, as Morrowind authors it.
  for (auto& [slot_key, ix] : s.index_)
    std::stable_partition(ix.begin(), ix.end(), [&](std::size_t i) { return s.lines_[i].available.has_value(); });
  if (!err.empty()) return std::unexpected(err);
  return s;
}

std::vector<std::string> Store::lint() const {
  std::vector<std::string> out;
  for (const auto& l : lines_) {
    const Topic* t = l.topic.empty() ? nullptr : topic(l.topic);
    if (t && t->essential && l.available && reads_disposition(*l.available))
      out.push_back(l.id + ": a line on essential " + t->id + " reads disposition (old 0145)");
  }
  return out;
}

const Topic* Store::topic(std::string_view id) const {
  const Topic* t = topic(key(id));
  return t && t->id == id ? t : nullptr;
}

const Topic* Store::topic(std::uint32_t k) const {
  auto it = by_key_.find(k);
  return it == by_key_.end() ? nullptr : &topics_[it->second];
}

std::vector<const Line*> Store::candidates(std::string_view speaker, std::string_view topic, LineType type) const {
  std::vector<const Line*> out;
  auto add = [&](std::string_view who) {
    auto it = index_.find(Slot{key(who), type, key(topic)});
    if (it != index_.end())
      for (auto i : it->second) out.push_back(&lines_[i]);
  };
  if (!speaker.empty()) add(speaker);  // the speaker's own lines first
  add({});                             // then the lines anyone may speak
  return out;
}

std::vector<Span> Store::keywords(std::string_view text, const Known& known) const {
  std::vector<Span> out;
  const std::string low = lower(text);
  for (std::size_t i = 0; i < low.size();) {
    if (i > 0 && word_char(low[i - 1])) { ++i; continue; }
    bool hit = false;
    for (const auto& [form, t] : forms_[static_cast<unsigned char>(low[i])]) {
      const std::size_t end = i + form.size();
      if (end > low.size() || low.compare(i, form.size(), form) != 0) continue;
      if (end < low.size() && word_char(low[end]) && word_char(form.back())) continue;
      out.push_back({i, form.size(), topics_[t].id, known.knows(topics_[t].id)});
      i = end;
      hit = true;
      break;
    }
    if (!hit) ++i;
  }
  return out;
}

bool Known::heard_from(std::string_view topic, std::string_view npc) const {
  auto it = heard_.find(key(topic));
  return it != heard_.end() && it->second.count(key(npc)) != 0;
}

bool Known::learn(std::string_view topic, std::string_view from) {
  auto [it, fresh] = heard_.try_emplace(key(topic));
  if (!from.empty()) it->second.insert(key(from));
  return fresh;
}

std::optional<bool> TalkFacts::truth(Term t, std::span<const Arg> keys) const {
  auto text = [&](std::size_t i) -> std::string_view {
    auto s = i < keys.size() ? std::get_if<std::string>(&keys[i]) : nullptr;
    return s ? std::string_view(*s) : std::string_view{};
  };
  if (t == Term::knowsTopic) return k_.knows(text(0));
  if (t == Term::topicHeardFrom) return k_.heard_from(text(0), text(1));
  return host_.truth(t, keys);
}

std::optional<double> TalkFacts::number(Term t, std::span<const Arg> keys) const {
  if (t == Term::speakerDispositionAtLeast) return double(s_.disposition);
  if (t == Term::dispositionAtLeast && !keys.empty()) {
    auto who = std::get_if<std::string>(&keys[0]);
    if (who && *who == s_.id) return double(s_.disposition);
  }
  return host_.number(t, keys);
}

std::optional<std::string> TalkFacts::state(Term t, std::span<const Arg> keys) const { return host_.state(t, keys); }

Answer words_at(const Line& l, int d) {
  const DispositionBand b = disposition::band(d);
  std::string_view text = l.words;
  if (b == DispositionBand::low && !l.low.empty()) text = l.low;
  if (b == DispositionBand::high && !l.high.empty()) text = l.high;
  return {&l, b, text};
}

std::vector<std::string_view> offered(const Store& s, const Speaker& sp, const Known& k, const Facts& host) {
  std::vector<std::string_view> out;
  for (const auto& t : s.all())
    if (k.knows(t.id) && first(s, t.id, LineType::dialogue, sp, k, host)) out.push_back(t.id);
  return out;
}

std::optional<Answer> answer(const Store& s, std::string_view topic, const Speaker& sp, const Known& k,
                             const Facts& host) {
  return first(s, topic, LineType::dialogue, sp, k, host);
}

std::optional<Answer> greeting(const Store& s, const Speaker& sp, const Known& k, const Facts& host) {
  return first(s, {}, LineType::greeting, sp, k, host);
}

std::optional<Answer> goodbye(const Store& s, const Speaker& sp, const Known& k, const Facts& host) {
  return first(s, {}, LineType::goodbye, sp, k, host);
}

std::vector<Span> keywords(const Store& s, std::string_view text, const Known& k) { return s.keywords(text, k); }

std::vector<std::string_view> deliver(const Store& s, const Answer& a, const Speaker& sp, Known& k) {
  std::vector<std::string_view> fresh;
  auto learn = [&](std::string_view id) {
    const Topic* t = s.topic(id);
    if (t && k.learn(t->id, sp.id)) fresh.push_back(t->id);
  };
  if (a.line && !a.line->topic.empty()) learn(a.line->topic);  // asked of this speaker: now heard from them too
  for (const auto& sp_ : s.keywords(a.text, k)) learn(sp_.topic);
  if (a.line)
    for (const auto& l : a.line->links) learn(l);
  return fresh;
}

cosave::Bytes encode(const Known& k) {
  cosave::Writer w;
  w.u32(std::uint32_t(k.raw().size()));
  for (const auto& [t, from] : k.raw()) {
    w.u32(t);
    w.u32(std::uint32_t(from.size()));
    for (auto n : from) w.u32(n);
  }
  return w.take();
}

std::optional<Known> decode(std::span<const std::uint8_t> b) {
  cosave::Reader r(b);
  Known k;
  auto n = r.u32();
  if (!n) return std::nullopt;
  std::optional<std::uint32_t> prev;
  for (std::uint32_t i = 0; i < *n; ++i) {
    auto t = r.u32();
    auto m = r.u32();
    if (!t || !m || (prev && *t <= *prev)) return std::nullopt;
    prev = t;
    auto& from = k.raw()[*t];
    std::optional<std::uint32_t> pf;
    for (std::uint32_t j = 0; j < *m; ++j) {
      auto f = r.u32();
      if (!f || (pf && *f <= *pf)) return std::nullopt;
      pf = f;
      from.insert(*f);
    }
  }
  if (!r.done()) return std::nullopt;
  return k;
}

}  // namespace argonia::core::topics
