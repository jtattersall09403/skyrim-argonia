// ArgoniaCore stub (0.3 §b): loads through SKSE on the pinned runtime by Address Library, registers the Papyrus
// natives ArgoniaCore.Version() and ArgoniaCore.SaveCount(), and keeps the META co-save family. The family's
// encoding and migration rules live in core/ and are tested there; this file only moves bytes.
#include "argonia/core/cosave.h"
#include "argonia/core/version.h"

namespace cosave = argonia::core::cosave;

namespace {

std::mutex g_lock;
cosave::Meta g_meta;  // guarded by g_lock: callbacks run on the main thread, natives on VM threads

void OnSave(SKSE::SerializationInterface* ser) {
  cosave::Bytes bytes;
  {
    std::lock_guard l(g_lock);
    ++g_meta.save_count;
    g_meta.written_by = cosave::packed_build_version();
    bytes = cosave::encode(g_meta);
  }
  if (!ser->OpenRecord(cosave::kMetaType, cosave::kMetaSpec.current) ||
      !ser->WriteRecordData(bytes.data(), static_cast<std::uint32_t>(bytes.size()))) {
    SKSE::log::error("co-save: META not written");
    return;
  }
  SKSE::log::info("co-save: META v{} written, save_count {}", cosave::kMetaSpec.current, g_meta.save_count);
}

void OnLoad(SKSE::SerializationInterface* ser) {
  std::uint32_t type = 0, version = 0, length = 0;
  while (ser->GetNextRecordInfo(type, version, length)) {
    cosave::Bytes bytes(length);
    if (length && ser->ReadRecordData(bytes.data(), length) != length) {
      SKSE::log::error("co-save: record {:08X} short read", type);
      continue;
    }
    if (type != cosave::kMetaType) {
      SKSE::log::warn("co-save: unknown record {:08X} v{} skipped", type, version);
      continue;
    }
    auto result = cosave::upgrade(cosave::kMetaSpec, version, bytes);
    auto meta = (result == cosave::LoadResult::ok || result == cosave::LoadResult::migrated)
                    ? cosave::decode_meta(bytes)
                    : std::nullopt;
    if (!meta) {
      SKSE::log::error("co-save: META v{} not loaded ({})", version, cosave::to_string(result));
      continue;
    }
    std::lock_guard l(g_lock);
    g_meta = *meta;
    SKSE::log::info("co-save: META v{} loaded ({}), save_count {}", version, cosave::to_string(result), g_meta.save_count);
  }
}

void OnRevert(SKSE::SerializationInterface*) {
  std::lock_guard l(g_lock);
  g_meta = {};
}

RE::BSFixedString Version(RE::StaticFunctionTag*) { return argonia::core::kVersionString; }

std::int32_t SaveCount(RE::StaticFunctionTag*) {
  std::lock_guard l(g_lock);
  return static_cast<std::int32_t>(g_meta.save_count);
}

bool RegisterNatives(RE::BSScript::IVirtualMachine* vm) {
  vm->RegisterFunction("Version"sv, "ArgoniaCore"sv, Version);
  vm->RegisterFunction("SaveCount"sv, "ArgoniaCore"sv, SaveCount);
  return true;
}

}  // namespace

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* skse) {
  SKSE::Init(skse);
  SKSE::log::info("ArgoniaCore {} loading on runtime {}", argonia::core::kVersionString, skse->RuntimeVersion().string("."));

  auto* ser = SKSE::GetSerializationInterface();
  ser->SetUniqueID(cosave::kUniqueId);
  ser->SetSaveCallback(OnSave);
  ser->SetLoadCallback(OnLoad);
  ser->SetRevertCallback(OnRevert);

  if (!SKSE::GetPapyrusInterface()->Register(RegisterNatives)) {
    SKSE::log::critical("Papyrus natives not registered");
    return false;
  }
  SKSE::log::info("ArgoniaCore loaded: natives ArgoniaCore.Version, ArgoniaCore.SaveCount; co-save ARGN/META v{}",
                  cosave::kMetaSpec.current);
  return true;
}
