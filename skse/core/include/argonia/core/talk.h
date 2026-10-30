// A conversation as the dialogue view sees it (1.3 §b, native map G18.1-G18.3, S18a): the dialogue intercept's
// handler opens one for an Argonia speaker; it greets, lists the topics the speaker answers, answers a topic or a
// clicked keyword with the speaker's first line whose condition holds, learns the line's links and keywords (who
// told them), runs the line's onDelivered actions through the seam's Session, and gives the view a full
// dialogue.state after each change. Views hold no state: ArgoniaCore keeps the conversation here.
#pragma once
#include "argonia/core/cosave.h"
#include "argonia/core/messages.h"
#include "argonia/core/seam.h"
#include "argonia/core/topics.h"

#include <expected>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::talk {

// A text split at its keyword spans into the view's runs (a run with a topic is a hyperlink).
std::vector<msg::TextRun> runs(const topics::Store& store, std::string_view text, const topics::Known& known);

// The in-game store: the generated fixture's written lines only (imported reference lines never reach the game,
// decision 0024 §7). The record loader replaces it when the people land (2.W5). Refusals are the reasons.
std::expected<topics::Store, std::vector<std::string>> fixture_store();

// The fixture's rows as the store's types, through the same validating constructors a loader uses: the one
// conversion fixture_store() and the L2 tests share. `errors` collects any row a constructor refused.
namespace fixture_rows {
std::vector<topics::Topic> topics();
std::expected<conditions::Pred, std::string> condition(std::size_t c);
std::vector<std::expected<actions::Action, std::string>> action_list(std::size_t l);
std::vector<topics::Line> lines(bool written_only, std::vector<std::string>& errors);  // false: every line
}  // namespace fixture_rows

struct Reply {
  std::optional<msg::DialogueState> state;  // the window to show; empty when it closed
  bool closed = false;
  std::vector<std::string> notes;           // refusals and action outcomes, for the SKSE log
};

// Whether the store holds any line for this speaker: an Argonia speaker, whose talk is ours.
bool speaks(const topics::Store& store, std::string_view speaker_id);

class Conversation {
 public:
  // Opens with the greeting. Refused when the store has no line for this speaker at all (not an Argonia speaker).
  static std::expected<Conversation, std::string> open(const topics::Store& store, seam::Session& session,
                                                      std::string speaker_id, std::string speaker_name);
  // A topic from the list or a keyword run: the answer, its learning and its actions.
  Reply ask(std::string_view topic, seam::Session& session);
  Reply on_intent(const msg::Intent& intent, seam::Session& session);
  // A view's intent as JSON text, decoded by the schema twin first (anything off-schema is refused).
  Reply on_intent_text(std::string_view json, seam::Session& session);
  msg::DialogueState view(const seam::Session& session) const;
  const std::string& speaker() const { return id_; }
  // The greeting's learning and action outcomes from open(), for the SKSE log.
  const std::vector<std::string>& greeting_notes() const { return greeting_notes_; }

 private:
  Conversation(const topics::Store& s, std::string id, std::string name) : store_(&s), id_(std::move(id)), name_(std::move(name)) {}
  void add(msg::DialogueEntryKind kind, std::optional<std::string> heading, const topics::Answer& a,
           seam::Session& session, Reply& r);
  const topics::Store* store_;
  std::string id_, name_;
  std::vector<msg::DialogueEntry> entries_;
  std::vector<std::string> greeting_notes_;
};

// The dev bridge's `greeting <speaker id>` (0.3 §e's timed loop): an SKSE message to ArgoniaCore whose data is this
// struct. Its listener opens a conversation with the speaker as the intercept does, without showing it, and writes
// the window (dialogue.state JSON, the greeting first) into `json` before the dispatch returns; `error` otherwise.
inline constexpr std::uint32_t kBridgeGreetingMessage = cosave::fourcc("GRET");
struct BridgeGreeting {
  char speaker[128] = {};
  char json[32768] = {};
  char error[256] = {};
  bool ok = false;
};

}  // namespace argonia::core::talk
