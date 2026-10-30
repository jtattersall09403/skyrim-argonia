#include "argonia/core/talk.h"

#include "argonia/core/fixture_topics.h"

#include <algorithm>

namespace argonia::core::talk {

namespace fx = gen::fixture;

std::vector<msg::TextRun> runs(const topics::Store& store, std::string_view text, const topics::Known& known) {
  std::vector<msg::TextRun> out;
  std::size_t at = 0;
  for (const auto& sp : topics::keywords(store, text, known)) {
    if (sp.begin > at) out.push_back({std::string(text.substr(at, sp.begin - at)), std::nullopt});
    out.push_back({std::string(text.substr(sp.begin, sp.size)), std::string(sp.topic)});
    at = sp.begin + sp.size;
  }
  if (at < text.size() || out.empty()) out.push_back({std::string(text.substr(at)), std::nullopt});
  return out;
}

namespace {

conditions::Arg arg(const fx::FxArg& a) {
  if (a.kind == fx::FxArg::is_text) return std::string(a.text);
  return a.number;
}

bool written(std::string_view speaker) {
  for (const auto& s : fx::kSpeakers)
    if (s.id == speaker) return s.status == "written";
  return speaker.empty();  // a line anyone may speak
}

msg::DispositionBand band_of(int d) {
  return msg::DispositionBand(std::size_t(disposition::band(d)));
}

}  // namespace

namespace fixture_rows {

std::vector<topics::Topic> topics() {
  std::vector<topics::Topic> out;
  for (const auto& t : fx::kTopics) {
    topics::Topic x{std::string(t.id), std::string(t.label), {}, t.essential};
    for (std::size_t i = 0; i < t.form_count; ++i) x.forms.emplace_back(fx::kForms[t.first_form + i]);
    out.push_back(std::move(x));
  }
  return out;
}

std::expected<conditions::Pred, std::string> condition(std::size_t c) {
  const auto& fc = fx::kConds[c];
  std::vector<conditions::FlatNode> nodes;
  for (std::size_t i = 0; i < fc.node_count; ++i) {
    const auto& n = fx::kNodes[fc.first_node + i];
    std::vector<conditions::Arg> args;
    for (std::size_t j = 0; j < n.arg_count; ++j) args.push_back(arg(fx::kArgs[n.first_arg + j]));
    nodes.push_back({n.parent, n.term, std::move(args)});
  }
  return conditions::from_flat(nodes);
}

std::vector<std::expected<actions::Action, std::string>> action_list(std::size_t l) {
  std::vector<std::expected<actions::Action, std::string>> out;
  const auto& al = fx::kActionLists[l];
  for (std::size_t i = 0; i < al.count; ++i) {
    const auto& a = fx::kActions[al.first + i];
    std::vector<conditions::Arg> args;
    for (std::size_t j = 0; j < a.arg_count; ++j) args.push_back(arg(fx::kActionArgs[a.first_arg + j]));
    out.push_back(actions::make(a.verb, std::move(args)));
  }
  return out;
}

std::vector<topics::Line> lines(bool written_only, std::vector<std::string>& errors) {
  std::vector<topics::Line> out;
  for (const auto& l : fx::kLines) {
    if (written_only && !written(l.speaker)) continue;
    topics::Line x;
    x.id = l.id;
    auto ty = topics::line_type(l.type);
    if (!ty) { errors.push_back(x.id + ": type " + std::string(l.type)); continue; }
    x.type = *ty;
    x.speaker = l.speaker;
    x.topic = l.topic;
    x.words = l.words;
    x.low = l.low;
    x.high = l.high;
    if (l.cond >= 0) {
      auto c = condition(std::size_t(l.cond));
      if (c) x.available = *c; else errors.push_back(x.id + ": " + c.error());
    }
    for (std::size_t i = 0; i < l.link_count; ++i) x.links.emplace_back(fx::kLinks[l.first_link + i]);
    if (l.actions >= 0)
      for (auto& a : action_list(std::size_t(l.actions))) {
        if (a) x.on_delivered.push_back(*a); else errors.push_back(x.id + ": " + a.error());
      }
    out.push_back(std::move(x));
  }
  return out;
}

}  // namespace fixture_rows

std::expected<topics::Store, std::vector<std::string>> fixture_store() {
  std::vector<std::string> errors;
  auto ls = fixture_rows::lines(true, errors);
  if (!errors.empty()) return std::unexpected(errors);
  return topics::Store::build(fixture_rows::topics(), std::move(ls));
}

bool speaks(const topics::Store& store, std::string_view speaker_id) {
  const auto lines = store.lines();
  return std::any_of(lines.begin(), lines.end(), [&](const topics::Line& l) { return l.speaker == speaker_id; });
}

std::expected<Conversation, std::string> Conversation::open(const topics::Store& store, seam::Session& session,
                                                            std::string speaker_id, std::string speaker_name) {
  if (!speaks(store, speaker_id))
    return std::unexpected("dialogue: " + speaker_id + " has no lines in the topic store; not an Argonia speaker");
  Conversation c(store, std::move(speaker_id), std::move(speaker_name));
  const topics::Speaker sp{c.id_, seam::disposition_of(session.state(), c.id_)};
  const auto host = session.facts();
  if (auto g = topics::greeting(store, sp, session.state().known, host)) {
    Reply r;
    c.add(msg::DialogueEntryKind::greeting, std::nullopt, *g, session, r);
    c.greeting_notes_ = std::move(r.notes);
  }
  return c;
}

void Conversation::add(msg::DialogueEntryKind kind, std::optional<std::string> heading, const topics::Answer& a,
                       seam::Session& session, Reply& r) {
  auto& st = session.state();
  // Runs are found against what the player knew before reading; then the reading teaches (deliver).
  entries_.push_back({kind, std::move(heading), runs(*store_, a.text, st.known)});
  const topics::Speaker sp{id_, seam::disposition_of(st, id_)};
  for (auto t : topics::deliver(*store_, a, sp, st.known)) r.notes.push_back("learned " + std::string(t) + " from " + id_);
  if (a.line && !a.line->on_delivered.empty()) {
    auto out = session.act(a.line->on_delivered);
    for (auto& why : out.refused) r.notes.push_back(a.line->id + ": " + why);
    if (out.done) r.notes.push_back(a.line->id + ": " + std::to_string(out.applied) + " action(s) applied");
  }
}

Reply Conversation::ask(std::string_view topic, seam::Session& session) {
  Reply r;
  const topics::Topic* t = store_->topic(topic);
  if (!t) {
    r.notes.push_back("dialogue: no topic " + std::string(topic));
  } else {
    const topics::Speaker sp{id_, seam::disposition_of(session.state(), id_)};
    const auto host = session.facts();
    if (auto a = topics::answer(*store_, topic, sp, session.state().known, host))
      add(msg::DialogueEntryKind::answer, t->label, *a, session, r);
    else
      r.notes.push_back("dialogue: " + id_ + " has no line for " + std::string(topic) + " now");
  }
  r.state = view(session);
  return r;
}

Reply Conversation::on_intent(const msg::Intent& intent, seam::Session& session) {
  if (const auto* t = std::get_if<msg::DialogueTopic>(&intent)) return ask(t->topic, session);
  if (const auto* k = std::get_if<msg::DialogueKeyword>(&intent)) return ask(k->topic, session);
  if (std::holds_alternative<msg::DialogueGoodbye>(intent)) return Reply{std::nullopt, true, {}};
  if (const auto* c = std::get_if<msg::ViewClose>(&intent); c && c->view == msg::ViewId::dialogue)
    return Reply{std::nullopt, true, {}};
  Reply r;
  r.notes.push_back(std::holds_alternative<msg::DialoguePersuade>(intent)
                        ? "dialogue: persuasion is 2.5's; refused"
                        : "dialogue: an intent for another view; refused");
  r.state = view(session);
  return r;
}

Reply Conversation::on_intent_text(std::string_view json, seam::Session& session) {
  auto in = msg::decode_intent(json);
  if (!in) {
    Reply r;
    r.notes.push_back("dialogue: intent refused: " + in.error());
    r.state = view(session);
    return r;
  }
  return on_intent(*in, session);
}

msg::DialogueState Conversation::view(const seam::Session& session) const {
  msg::DialogueState s;
  s.speaker = {id_, name_};
  s.entries = entries_;
  const int d = seam::disposition_of(session.state(), id_);
  const topics::Speaker sp{id_, d};
  const auto host = session.facts();
  for (auto id : topics::offered(*store_, sp, session.state().known, host))
    if (const auto* t = store_->topic(id)) s.topics.push_back({t->id, t->label});
  s.disposition = {d, band_of(d)};
  s.persuasion = {false, {}};  // 2.5
  s.can_leave = true;
  return s;
}

}  // namespace argonia::core::talk
