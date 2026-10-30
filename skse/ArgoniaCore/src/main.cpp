// ArgoniaCore (PLAN §3; 1.1): loads through SKSE on the pinned runtime by Address Library, owns every co-save family
// through skse/core's families registry (META included), registers the Papyrus natives, installs the router's hooks
// once and gives the player the dialogue intercept's perk. The families' encodings and migrations live in core/ and
// are tested there; the callbacks here only move bytes.
#include "core.h"
#include "argonia/core/version.h"

namespace plugin = argonia::plugin;
namespace ac = argonia::core;

namespace {

void OnSave(SKSE::SerializationInterface* ser) {
  auto& c = plugin::Get();
  std::lock_guard l(c.lock);
  ac::seam::on_save(c.state);
  std::size_t written = 0;
  for (const auto& rec : c.families.save_all()) {
    if (!ser->OpenRecord(rec.id, rec.version) ||
        !ser->WriteRecordData(rec.payload.data(), static_cast<std::uint32_t>(rec.payload.size()))) {
      SKSE::log::error("co-save: {} v{} not written", ac::families::fourcc_name(rec.id), rec.version);
      continue;
    }
    ++written;
  }
  SKSE::log::info("co-save: {} families written, save_count {}", written, c.state.meta.save_count);
}

void OnLoad(SKSE::SerializationInterface* ser) {
  auto& c = plugin::Get();
  std::lock_guard l(c.lock);
  c.inflight.clear();
  std::uint32_t type = 0, version = 0, length = 0;
  while (ser->GetNextRecordInfo(type, version, length)) {
    ac::cosave::Bytes bytes(length);
    if (length && ser->ReadRecordData(bytes.data(), length) != length) {
      SKSE::log::error("co-save: record {} short read", ac::families::fourcc_name(type));
      continue;
    }
    const auto r = c.families.load(type, version, std::move(bytes));
    if (r.ok()) SKSE::log::info("{}", r.message);
    else SKSE::log::error("{}", r.message);
  }
  SKSE::log::info("co-save: loaded, save_count {}", c.state.meta.save_count);
}

void OnRevert(SKSE::SerializationInterface*) {
  auto& c = plugin::Get();
  std::lock_guard l(c.lock);
  c.families.reset_all();
  c.inflight.clear();
  c.talk.reset();
  plugin::CloseAllViews();
  c.season.reset();
  c.sitting.reset();
  c.health.clear();
}

void OnDataLoaded() {
  auto& c = plugin::Get();
  std::lock_guard l(c.lock);
  c.graphs = ac::gen::quest_graphs();
  for (const auto& g : c.graphs)
    for (const auto& why : ac::quest_runtime::check(g)) SKSE::log::error("quests: {}: {}", g.id, why);
  auto store = ac::talk::fixture_store();
  if (store) {
    c.store = std::move(*store);
    SKSE::log::info("dialogue: topic store {} topics, {} lines", c.store->all().size(), c.store->lines().size());
  } else {
    for (const auto& why : store.error()) SKSE::log::error("dialogue: {}", why);
  }
  plugin::InstallHooks();
  plugin::ViewsDataLoaded();
  plugin::LifeDataLoaded();
  plugin::CombatDataLoaded();
}

void OnGameReady(const char* how) {
  plugin::NewCharacter();  // a no-op once the sheet exists; a `coc` start from the main menu sends no kNewGame
  plugin::EnsurePerks();
  plugin::MirrorAttributes();
  plugin::LifeGameReady();
  plugin::WriteCombat(how);
  plugin::FactsChanged(how);
  plugin::ViewsGameReady();
}

void OnMessage(SKSE::MessagingInterface::Message* m) {
  switch (m->type) {
    case SKSE::MessagingInterface::kPostLoad: plugin::ViewsPostLoad(); break;
    case SKSE::MessagingInterface::kDataLoaded: OnDataLoaded(); break;
    case SKSE::MessagingInterface::kPostLoadGame: OnGameReady("game loaded"); break;
    case SKSE::MessagingInterface::kNewGame:
      OnGameReady("new game");
      break;
    default: break;
  }
}

// The dev bridge's hands (ArgoniaBridge's `core-suspend`): an SKSE message from the plugin "ArgoniaBridge". The
// bridge waits for the dispatch to return, so `written` is the answer it reads (the save itself runs as a task).
void OnBridgeMessage(SKSE::MessagingInterface::Message* m) {
  if (plugin::HandleBridgeCore(m)) return;
  if (m && m->type == ac::talk::kBridgeGreetingMessage && m->data && m->dataLen == sizeof(ac::talk::BridgeGreeting)) {
    auto* req = static_cast<ac::talk::BridgeGreeting*>(m->data);
    req->speaker[sizeof(req->speaker) - 1] = '\0';
    auto r = plugin::GreetingFor(req->speaker);
    const std::string& text = r ? *r : r.error();
    char* into = r ? req->json : req->error;
    const std::size_t cap = r ? sizeof(req->json) : sizeof(req->error);
    req->ok = r.has_value() && text.size() < cap;
    text.copy(into, (std::min)(text.size(), cap - 1));  // (std::min): windows.h defines min
    return;
  }
  if (!m || m->type != ac::life::kBridgeSuspendMessage || !m->data || m->dataLen != sizeof(ac::life::BridgeSuspend))
    return;
  auto* req = static_cast<ac::life::BridgeSuspend*>(m->data);
  req->why[sizeof(req->why) - 1] = '\0';
  req->written = plugin::SuspendSaveFor(req->why);
}

}  // namespace

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* skse) {
  SKSE::Init(skse);
  SKSE::log::info("ArgoniaCore {} loading on runtime {}", ac::kVersionString, skse->RuntimeVersion().string("."));

  auto& c = plugin::Get();
  for (const auto& why : ac::seam::bind(c.families, c.state)) SKSE::log::critical("{}", why);
  std::string ids;
  for (auto id : c.families.ids()) ids += (ids.empty() ? "" : " ") + ac::families::fourcc_name(id);

  auto* ser = SKSE::GetSerializationInterface();
  ser->SetUniqueID(ac::cosave::kUniqueId);
  ser->SetSaveCallback(OnSave);
  ser->SetLoadCallback(OnLoad);
  ser->SetRevertCallback(OnRevert);

  if (!SKSE::GetPapyrusInterface()->Register(plugin::RegisterNatives)) {
    SKSE::log::critical("Papyrus natives not registered");
    return false;
  }
  if (!SKSE::GetMessagingInterface()->RegisterListener(OnMessage)) {
    SKSE::log::critical("SKSE messaging listener not registered");
    return false;
  }
  // The bridge is dev only (absent in a release), so a refused listener is a warning, never a load failure.
  if (!SKSE::GetMessagingInterface()->RegisterListener("ArgoniaBridge", OnBridgeMessage))
    SKSE::log::warn("no listener for ArgoniaBridge's messages (the dev bridge cannot call SuspendSave)");
  SKSE::log::info("ArgoniaCore loaded: co-save ARGN families {}", ids);
  return true;
}
