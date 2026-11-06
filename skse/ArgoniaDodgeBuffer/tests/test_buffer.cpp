#include <cstdio>
#include <cstdlib>

#include "buffer.h"

using namespace argonia::dodgebuffer;

static int failed = 0;
#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "FAIL %s:%d %s\n", __FILE__, __LINE__, #c); ++failed; } } while (0)

static Buffer fresh() { return Buffer(Settings{}); }

int main() {
  const Context ok{};
  CHECK(matches({"TKDR_DodgeEnd", "tailCombatIdle"}, "tailcombatidle"));  // case-insensitive
  CHECK(!matches({"TKDR_DodgeEnd"}, "TKDR_DodgeEnd2"));
  CHECK(matches(Settings{}.end_events, "TKDodgeStop"));

  { // a press during the dodge fires a light attack at the end
    auto b = fresh();
    CHECK(b.on_graph_event("TKDR_DodgeStart", 10.0, ok) == Fire::None && b.dodging());
    b.on_button(true, 10.1); b.on_button(false, 10.2);
    CHECK(b.buffered());
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 10.5, ok) == Fire::Light);
    CHECK(!b.buffered() && !b.dodging());
    CHECK(b.on_graph_event("tailCombatIdle", 10.6, ok) == Fire::None);  // the fallback after the real end: nothing twice
  }
  { // held past fPowerHoldSeconds at fire time: power attack
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok);
    b.on_button(true, 0.1);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.6, ok) == Fire::Power);  // held 0.5 > 0.4
  }
  { // held, but not long enough
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok);
    b.on_button(true, 0.3);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.6, ok) == Fire::Light);
  }
  { // released early: light
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok);
    b.on_button(true, 0.1); b.on_button(false, 0.2);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.65, ok) == Fire::Light);
  }
  { // too old: the window is 0.6 s from the press
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok);
    b.on_button(true, 0.0); b.on_button(false, 0.1);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.7, ok) == Fire::None);
    CHECK(!b.buffered());
  }
  { // the window edge itself is inside
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok);
    b.on_button(true, 0.25); b.on_button(false, 0.3);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.85, ok) == Fire::Light);
  }
  { // no press, or a press outside a dodge, buffers nothing
    auto b = fresh();
    b.on_button(true, 1.0);
    CHECK(!b.buffered());
    b.on_graph_event("TKDR_DodgeStart", 2.0, ok);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 2.3, ok) == Fire::None);
  }
  { // menu open or weapon sheathed: the buffer is cleared, nothing fires
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok); b.on_button(true, 0.1); b.on_button(false, 0.15);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.3, Context{true, true}) == Fire::None && !b.buffered());
    b.on_graph_event("TKDR_DodgeStart", 1.0, ok); b.on_button(true, 1.1); b.on_button(false, 1.15);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 1.3, Context{false, false}) == Fire::None && !b.buffered());
  }
  { // a refused fire is retried once, on the next end event
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok); b.on_button(true, 0.1); b.on_button(false, 0.15);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.3, ok) == Fire::Light);
    b.rejected();
    CHECK(b.on_graph_event("tailCombatIdle", 0.35, ok) == Fire::Light);
    CHECK(b.on_graph_event("tailCombatIdle", 0.4, ok) == Fire::None);  // only once
  }
  { // a retry past the window is dropped
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok); b.on_button(true, 0.1); b.on_button(false, 0.15);
    CHECK(b.on_graph_event("TKDR_DodgeEnd", 0.3, ok) == Fire::Light);
    b.rejected();
    CHECK(b.on_graph_event("tailCombatIdle", 5.0, ok) == Fire::None);
  }
  { // a new dodge clears a stale press; a dodge with no end event stops counting after 3 s
    auto b = fresh();
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok); b.on_button(true, 0.1);
    b.on_graph_event("TKDR_DodgeStart", 1.0, ok);
    CHECK(!b.buffered());
    b.on_button(true, 4.5);
    CHECK(!b.buffered());
  }
  { // disabled: inert
    Settings s; s.enabled = false;
    Buffer b(s);
    b.on_graph_event("TKDR_DodgeStart", 0.0, ok); b.on_button(true, 0.1);
    CHECK(!b.dodging() && !b.buffered());
  }
  { // the ini
    Settings s;
    auto unknown = parse_ini("; c\n[General]\nbEnabled = 0\nfBufferSeconds=0.8\nfPowerHoldSeconds=abc\n"
                             "sDodgeStartEvents= A , B\nsDodgeEndEvents=E\nsAttackEvent=x\nbogus=1\r\nsUserEvent=Right Attack/Block\n", s);
    CHECK(!s.enabled);
    CHECK(s.buffer_seconds == 0.8);
    CHECK(s.power_hold_seconds == 0.4);  // unreadable: the default stays
    CHECK((s.start_events == std::vector<std::string>{"A", "B"}));
    CHECK((s.end_events == std::vector<std::string>{"E"}));
    CHECK(s.attack_event == "x" && s.power_event == "attackPowerStartInPlace");
    CHECK(unknown.size() == 1 && unknown[0] == "bogus");
    Settings d; parse_ini("bEnabled=1\nfBufferSeconds=-1\n", d);
    CHECK(d.enabled && d.buffer_seconds == 0.6);
  }
  if (failed) return 1;
  std::puts("dodgebuffer: all tests passed");
  return 0;
}
