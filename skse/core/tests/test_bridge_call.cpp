// L2: the dev bridge's `core` whitelist (1.7): reads, the two view intents and the 1.2 §0 probe's two go; setters,
// form natives and unknown names are refused; each value travels as valid JSON.
#include "check.h"
#include "argonia/core/bridge_call.h"

#include <string>

using namespace argonia::core::bridge_call;
namespace json = argonia::core::json;

int main() {
  CHECK(!refuse("GetVastei", false));
  CHECK(!refuse("KnowsTopic", true));
  CHECK(!refuse("ViewIntent", true));
  CHECK(!refuse("SittingIntent", true));
  CHECK(refuse("KnowsTopic", false));       // missing arg
  CHECK(refuse("GetVastei", true));         // extra arg
  for (auto setter : {"SetVastei", "SetAttribute", "GrantTopic", "SetFlag", "ChangeDisposition", "GiveItem",
                      "RestAt", "TakeVastei", "OpenDialogue", "WatchQuest", "AddJournalEntry", "SuspendSave", ""})
    CHECK(refuse(setter, false) && refuse(setter, true));
  CHECK(natives().size() == 23);  // 21 of ArgoniaCore.psc, plus the bridge-only ViewProbe and Views (1.2 §0)
  CHECK(!refuse("ViewProbe", true) && !refuse("Views", false));
  CHECK(find("Families") && find("Families")->returns == Returns::TextList);

  auto v = json::parse(encode_number("GetVastei", 120));
  CHECK(v && v->find("value") && *v->find("value")->as_number() == 120);
  CHECK(*v->find("native")->as_string() == "GetVastei");
  v = json::parse(encode_list("Families", {"META", "STAT"}));
  CHECK(v && v->find("value")->as_array()->size() == 2);
  v = json::parse(encode_json("ViewState", R"({"type":"dialogue.state","v":1})"));
  CHECK(v && *v->find("value")->find("type")->as_string() == "dialogue.state");
  v = json::parse(encode_json("ViewState", ""));
  CHECK(v && v->find("value")->is_null());
  v = json::parse(encode_json("ViewIntent", "not json \" at all"));  // a bad document travels as a string
  CHECK(v && *v->find("value")->as_string() == "not json \" at all");
  v = json::parse(encode_text("PileState", "1.00 2.00 3.00 0000003C 120"));
  CHECK(v && *v->find("value")->as_string() == "1.00 2.00 3.00 0000003C 120");
  v = json::parse(encode_bool("SittingOpen", true));
  CHECK(v && *v->find("value")->as_bool());
  return TEST_MAIN_RESULT("core.bridge_call");
}
