// L1/L2: the C++ twin of ui/schema (1.1 §c). Every mock fixture of 1.2's four screens decodes and re-encodes to the
// same JSON; a message not in the schema is refused with a readable path (unknown type, wrong version, wrong
// direction, missing, extra or mistyped field, value out of its set or range); encode refuses what decode would; the
// TS twin was generated from the same schema (one hash).
#include "check.h"
#include "argonia/core/messages.h"
#include "argonia/core/tables_conditions.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <limits>
#include <sstream>
#include <string>

using namespace argonia::core;

namespace {

const std::filesystem::path kRepo = std::filesystem::path(__FILE__).parent_path() / ".." / ".." / "..";

std::string slurp(const std::filesystem::path& p) {
  std::ifstream in(p, std::ios::binary);
  std::stringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

bool contains(const std::string& s, std::string_view part) { return s.find(part) != std::string::npos; }

template <class R>
bool refused(const R& r, std::string_view why) {
  if (r) return false;
  if (!contains(r.error(), why)) std::fprintf(stderr, "  refusal was: %s\n", r.error().c_str());
  return contains(r.error(), why);
}

int fixtures_checked = 0;

void fixture(const char* screen) {
  const std::string text = slurp(kRepo / "ui" / "fixtures" / (std::string(screen) + ".json"));
  auto doc = json::parse(text);
  CHECK(doc.has_value());
  if (!doc) return;
  for (const char* group : {"states", "intents"}) {
    const json::Value* g = doc->find(group);
    CHECK(g && g->as_object());
    if (!g || !g->as_object()) continue;
    const bool is_push = std::string_view(group) == "states";
    for (const auto& [name, env] : *g->as_object()) {
      const std::string wire = json::dump(env);
      auto m = msg::decode(wire);
      if (!m) std::fprintf(stderr, "  %s.%s: %s\n", screen, name.c_str(), m.error().c_str());
      CHECK(m.has_value());
      if (!m) continue;
      auto out = std::visit([](const auto& x) { return msg::encode(x); }, *m);
      CHECK(out.has_value() && *json::parse(*out) == env);  // decode -> encode -> the same JSON
      CHECK(msg::decode(*out) == m);
      CHECK(bool(msg::decode_push(wire)) == is_push);
      CHECK(bool(msg::decode_intent(wire)) == !is_push);
      ++fixtures_checked;
    }
  }
}

void every_screen_has_a_fixture() {
  // The game machine builds a tree holding only skse/; the fixtures live in ui/ and are checked by the Linux gate.
  if (!std::filesystem::exists(kRepo / "ui" / "fixtures")) {
    std::puts("skip: ui/fixtures not in this tree (the build VM's make check runs them)");
    return;
  }
  for (const char* s : {"dialogue", "journal", "hud", "chart"}) fixture(s);
  CHECK(fixtures_checked >= 30);
  // Every message type in the schema appears in some fixture.
  std::string all;
  for (const char* s : {"dialogue", "journal", "hud", "chart"}) all += slurp(kRepo / "ui" / "fixtures" / (std::string(s) + ".json"));
  for (const auto& info : msg::kMessages) CHECK(contains(all, "\"" + std::string(info.type) + "\""));
}

void refusals() {
  using msg::decode;
  CHECK(refused(decode(R"({"type":"dialogue.shout","v":1,"body":{}})"), "message type 'dialogue.shout' is not in the schema"));
  CHECK(refused(decode(R"({"type":"dialogue.goodbye","v":2,"body":{}})"), "dialogue.goodbye version 2: this build speaks version 1"));
  CHECK(refused(decode(R"({"type":"dialogue.goodbye","v":1,"body":{},"x":0})"), "message.x: not in the schema"));
  CHECK(refused(decode(R"({"type":"dialogue.goodbye","body":{}})"), "message.v: missing"));
  CHECK(refused(decode(R"({"type":"dialogue.goodbye","v":1,"body":{"now":true}})"), "dialogue.goodbye body.now: not in the schema"));
  CHECK(refused(decode(R"({"type":"dialogue.topic","v":1,"body":{}})"), "dialogue.topic body.topic: missing"));
  CHECK(refused(decode(R"({"type":"dialogue.topic","v":1,"body":{"topic":7}})"), "dialogue.topic body.topic: want a string"));
  CHECK(refused(decode(R"({"type":"view.close","v":1,"body":{"view":"hud"}})"),
                "view.close body.view: 'hud' is not one of dialogue, journal, chart"));
  CHECK(refused(decode(R"({"type":"journal.page","v":1,"body":{"tab":"entries","page":-1}})"),
                "journal.page body.page: -1 is outside 0.."));
  CHECK(refused(decode(R"({"type":"journal.page","v":1,"body":{"tab":"entries","page":1.5}})"), "want a whole number"));
  CHECK(refused(decode(R"({"type":"journal.page","v":1,"body":{"tab":"entries","page":1,"questFilter":null}})"),
                "journal.page body.questFilter: want a string"));
  CHECK(refused(decode(R"({"type":"chart.pan","v":1,"body":{"view":{"centreX":0,"centreY":0,"zoom":0}}})"),
                "chart.pan body.view.zoom: 0 is outside 0.05..64"));
  CHECK(refused(decode(R"({"type":"hud.bars","v":1,"body":{"bars":[{"kind":"health","current":1,"max":2}]}})"),
                "hud.bars body.bars[0].shown: missing"));
  CHECK(refused(decode("[]"), "message: want an object"));
  CHECK(refused(decode("{"), "message: JSON error"));
  // Direction: ArgoniaCore takes intents only; a view takes pushes only.
  CHECK(refused(msg::decode_intent(R"({"type":"hud.bars","v":1,"body":{"bars":[]}})"), "ArgoniaCore accepts intents only"));
  CHECK(refused(msg::decode_push(R"({"type":"dialogue.goodbye","v":1,"body":{}})"), "an intent is never pushed to a view"));
  CHECK(msg::decode_intent(R"({"type":"dialogue.goodbye","v":1,"body":{}})").has_value());
}

void encode_refuses_what_decode_would() {
  msg::HudBars bars;
  bars.bars.push_back({msg::BarKind::health, 10, 20, true});
  CHECK(msg::encode(bars).has_value());
  bars.bars[0].current = -1;
  CHECK(refused(msg::encode(bars), "hud.bars body.bars[0].current: -1 is outside 0.."));
  bars.bars[0].current = std::numeric_limits<double>::quiet_NaN();
  CHECK(refused(msg::encode(bars), "want a number"));
  msg::DialogueState d;
  d.disposition.value = 101;
  CHECK(refused(msg::encode(d), "dialogue.state body.disposition.value: 101 is outside 0..100"));
  d.disposition.value = 50;
  auto ok = msg::encode(d);
  CHECK(ok.has_value() && contains(*ok, R"("type":"dialogue.state","v":1)"));
  // An absent optional is omitted, never null.
  msg::JournalPage page{msg::JournalTab::quests, 2, std::nullopt};
  CHECK(*msg::encode(page) == R"({"type":"journal.page","v":1,"body":{"tab":"quests","page":2}})");
  page.quest_filter = "quest.local.lf83";
  auto back = msg::decode_intent(*msg::encode(page));
  CHECK(back && std::get<msg::JournalPage>(*back) == page);
}

void twins_and_vocabularies_agree() {
  const std::string ts = slurp(kRepo / "ui" / "schema" / "generated" / "messages.ts");
  CHECK(contains(ts, "export const schemaHash = \"" + std::string(msg::kSchemaHash) + "\";"));
  // The message vocabularies that mirror skse/core's own.
  CHECK(msg::kDispositionBandNames.size() == gen::kDispositionBandNames.size());
  for (std::size_t i = 0; i < gen::kDispositionBandNames.size(); ++i)
    CHECK(msg::kDispositionBandNames[i] == gen::kDispositionBandNames[i]);
  CHECK(msg::kJournalEntryKindNames.size() == 3 && msg::kQuestStatusNames.size() == 3);
}

}  // namespace

int main() {
  every_screen_has_a_fixture();
  refusals();
  encode_refuses_what_decode_would();
  twins_and_vocabularies_agree();
  return TEST_MAIN_RESULT("core.messages");
}
