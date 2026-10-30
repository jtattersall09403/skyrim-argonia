// ArgoniaCore's adapter layer (1.1 §a-§d): the only place CommonLibSSE-NG meets skse/core. Every rule is in
// skse/core (seam, talk, quest_runtime, router, families ...) and tested there; these files turn engine events into
// the seam's inputs and write its outputs back (SetStage, SetObjectiveCompleted, actor values, globals, view pushes).
#pragma once
#include "argonia/core/quests.h"
#include "argonia/core/router.h"
#include "argonia/core/seam.h"
#include "argonia/core/talk.h"

#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::plugin {

namespace ac = argonia::core;

struct Core {
  std::recursive_mutex lock;  // natives, events and the co-save callbacks all take it
  ac::seam::State state;
  ac::families::Registry families;
  ac::router::Router router;
  std::vector<std::string> router_log;
  std::vector<ac::quest_runtime::Graph> graphs;
  std::optional<ac::topics::Store> store;
  std::optional<ac::talk::Conversation> talk;
  std::map<std::string, std::string, std::less<>> views;  // the last push per view, as the view received it
  std::optional<ac::weather::Season> season;              // the season the weather globals hold
  RE::ObjectRefHandle pending_speaker;                    // the person the intercept is opening for
  ac::seam::InFlight inflight;                            // quest orders dispatched, not yet run by the VM
};
Core& Get();

// --- engine.cpp: records by world id, the engine reads and writes, the quest orders, the mirrors ------------------
RE::TESForm* Lookup(std::string_view world_id);
template <class T>
T* Lookup(std::string_view world_id) {
  auto* f = Lookup(world_id);
  return f ? f->As<T>() : nullptr;
}
std::optional<std::string> WorldId(const RE::TESForm* form);
inline constexpr RE::FormID kGold = 0x0000000F;  // Skyrim.esm's Gold001, the engine's own currency record
class GameEngine final : public ac::seam::Engine, public ac::seam::EngineWrites {
 public:
  std::optional<int> item_count(std::string_view item) const override;
  std::optional<bool> alive(std::string_view npc) const override;
  std::optional<int> gold() const override;
  std::optional<ac::seam::QuestView> quest(std::string_view quest) const override;
  std::optional<ac::seam::Date> date() const override;
  bool give_item(std::string_view item, int count) override;
  bool take_item(std::string_view item, int count) override;
  bool give_gold(int amount) override;
  bool take_gold(int amount) override;
};
ac::seam::Session Session();
// A fact changed (`why` names it for the log): step the watched quests and apply the orders; check the season.
void FactsChanged(std::string_view why);
void MirrorAttributes();
void EnsurePerk();

// --- dialogue.cpp: the router's handler, the view host, the sinks ---------------------------------------------
bool OpenDialogue(RE::TESObjectREFR* target);
std::string ViewIntent(std::string_view json);
void Push(std::string_view view, std::string json);
void InstallHooks();

// --- natives.cpp ------------------------------------------------------------------------------------------------
bool RegisterNatives(RE::BSScript::IVirtualMachine* vm);

}  // namespace argonia::plugin
