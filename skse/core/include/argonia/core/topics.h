// The topic store (1.3 §b, route b of decision 0005 C1; native map G18.1-G18.3): Morrowind's dialogue model over
// our records. A speaker answers a topic with the first of its candidate lines whose condition holds: the speaker's
// own lines, then lines anyone may speak, and within each a conditioned line before a plain one (the fallback).
// Disposition bands (< 30, 30-69, >= 70) pick the line's low, mid or high words. The topic list is the learned
// topics the speaker answers, and it grows as the player reads a topic's keyword or a line links it. Essential
// topics (a quest's essentialTopics) never read disposition (old 0145): `lint` names any line that does.
// The learned set is the `topics` co-save family (TOPC).
#pragma once
#include "argonia/core/actions.h"
#include "argonia/core/conditions.h"
#include "argonia/core/cosave.h"
#include "argonia/core/disposition.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <expected>
#include <map>
#include <optional>
#include <set>
#include <span>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

namespace argonia::core::topics {

using conditions::Facts;
using conditions::Pred;
using gen::DispositionBand;

// The stable 32-bit key of a world id (FNV-1a): what the co-save holds for a topic or a person.
std::uint32_t key(std::string_view id);

enum class LineType : std::uint8_t { greeting, dialogue, goodbye };
std::optional<LineType> line_type(std::string_view id);

struct Topic {
  std::string id;
  std::string label;               // the topic list's name and its first keyword form
  std::vector<std::string> forms;  // the glossary forms that also hyperlink it
  bool essential = false;
};

struct Line {
  std::string id;
  LineType type = LineType::dialogue;
  std::string speaker;               // empty: anyone may speak it
  std::string topic;                 // empty for a greeting or goodbye
  std::optional<Pred> available;     // none: always
  std::string words, low, high;      // low/high empty: words serves that band
  std::vector<std::string> links;    // topics the line grants as hyperlinks
  std::vector<actions::Action> on_delivered;
};

class Known;

// One keyword hit in a text: [begin, begin + size) names `topic`.
struct Span {
  std::size_t begin, size;
  std::string_view topic;
  bool known;  // the player knew it before this text
};

class Store {
 public:
  // Refuses (every reason listed): a duplicate or colliding topic id, a line on an unknown topic or link, an invalid
  // condition or action, a greeting with a topic, a dialogue line without one, a line without words.
  static std::expected<Store, std::vector<std::string>> build(std::vector<Topic> topics, std::vector<Line> lines);
  // The content rules a store can hold yet a writer must answer (the L1 gate's to enforce): a line on an essential
  // topic whose condition reads disposition (old 0145 item 2).
  std::vector<std::string> lint() const;

  const Topic* topic(std::string_view id) const;
  const Topic* topic(std::uint32_t k) const;
  std::span<const Topic> all() const { return topics_; }
  std::span<const Line> lines() const { return lines_; }
  // The candidate lines of a speaker for a topic ("" for greetings/goodbyes by type), in first-match order.
  std::vector<const Line*> candidates(std::string_view speaker, std::string_view topic, LineType type) const;
  // Every keyword (label or form) of every topic in `text`: case-insensitive, whole words, longest first, no overlap.
  std::vector<Span> keywords(std::string_view text, const Known& known) const;

 private:
  std::vector<Topic> topics_;
  std::vector<Line> lines_;
  std::map<std::uint32_t, std::size_t> by_key_;
  using Slot = std::tuple<std::uint32_t, LineType, std::uint32_t>;  // key(speaker or ""), type, key(topic or "")
  std::map<Slot, std::vector<std::size_t>> index_;                  // -> line indices in first-match order
  // Lower-cased keyword forms by their first byte, longest first, each with its topic's index.
  std::array<std::vector<std::pair<std::string, std::size_t>>, 256> forms_;
};

// The learned set: each topic the player knows and who told them (topicHeardFrom).
class Known {
 public:
  bool knows(std::string_view topic) const { return knows(key(topic)); }
  bool knows(std::uint32_t topic) const { return heard_.count(topic) != 0; }
  bool heard_from(std::string_view topic, std::string_view npc) const;
  // True when the topic is new. An empty `from` learns it without a teller (grantTopic).
  bool learn(std::string_view topic, std::string_view from = {});
  std::size_t size() const { return heard_.size(); }
  const std::map<std::uint32_t, std::set<std::uint32_t>>& raw() const { return heard_; }
  std::map<std::uint32_t, std::set<std::uint32_t>>& raw() { return heard_; }
  bool operator==(const Known&) const = default;

 private:
  std::map<std::uint32_t, std::set<std::uint32_t>> heard_;
};

struct Speaker {
  std::string id;
  int disposition = 0;  // this conversation's, persuasion included
};

// The facts as the talk sees them: knowsTopic and topicHeardFrom from the learned set, speakerDispositionAtLeast and
// dispositionAtLeast(speaker) from the speaker; everything else from the host (ArgoniaCore).
class TalkFacts : public Facts {
 public:
  TalkFacts(const Speaker& s, const Known& k, const Facts& host) : s_(s), k_(k), host_(host) {}
  std::optional<bool> truth(conditions::Term t, std::span<const conditions::Arg> keys) const override;
  std::optional<double> number(conditions::Term t, std::span<const conditions::Arg> keys) const override;
  std::optional<std::string> state(conditions::Term t, std::span<const conditions::Arg> keys) const override;

 private:
  const Speaker& s_;
  const Known& k_;
  const Facts& host_;
};

struct Answer {
  const Line* line = nullptr;
  DispositionBand band = DispositionBand::mid;
  std::string_view text;
};

// The words a line gives at a disposition.
Answer words_at(const Line& l, int disposition);
// The topic list: the learned topics this speaker answers now, in store order.
std::vector<std::string_view> offered(const Store& s, const Speaker& sp, const Known& k, const Facts& host);
// The first line of this speaker's candidates for the topic whose condition holds (an unknown never holds).
std::optional<Answer> answer(const Store& s, std::string_view topic, const Speaker& sp, const Known& k, const Facts& host);
std::optional<Answer> greeting(const Store& s, const Speaker& sp, const Known& k, const Facts& host);
std::optional<Answer> goodbye(const Store& s, const Speaker& sp, const Known& k, const Facts& host);
// Hyperlinks in a text, against everything the store knows (Morrowind links every topic it finds).
std::vector<Span> keywords(const Store& s, std::string_view text, const Known& k);
// The player has read the answer: its links and every keyword in its words are learned, told by the speaker.
// Returns the topics newly learned, in the order met. The line's on_delivered actions are the caller's to run.
std::vector<std::string_view> deliver(const Store& s, const Answer& a, const Speaker& sp, Known& k);

// The `topics` family (TOPC, version 1): the learned set.
inline constexpr std::uint32_t kTopicsType = cosave::fourcc("TOPC");
cosave::Bytes encode(const Known& k);
std::optional<Known> decode(std::span<const std::uint8_t> b);

}  // namespace argonia::core::topics
