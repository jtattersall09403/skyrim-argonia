// Dependency mods' forms restated at data load (1.12; docs/research/2026-10-31/lane-1.12-magic.md): each mod_form
// row (core/magic over tables_magic.h) is looked up in its plugin and given our name, our description, or for a magic
// effect the magic skill of its Morrowind school. The mod's plugin is never edited or mastered (0003, 0012); a row
// whose plugin is not loaded is skipped with one log line.
#include "core.h"
#include "argonia/core/magic.h"

namespace argonia::plugin {

void MagicDataLoaded() {
  auto* dh = RE::TESDataHandler::GetSingleton();
  if (!dh) return;
  int named = 0, described = 0, moved = 0, missing = 0;
  for (const auto& r : ac::gen::kModForms) {
    if (!dh->LookupLoadedModByName(r.plugin) && !dh->LookupLoadedLightModByName(r.plugin)) {
      ++missing;
      continue;
    }
    auto* form = dh->LookupForm(r.local_id, r.plugin);
    if (!form) {
      SKSE::log::warn("magic: {:06X}:{} not found", r.local_id, r.plugin);
      ++missing;
      continue;
    }
    if (auto n = ac::magic::rename(r)) {
      if (auto* full = form->As<RE::TESFullName>()) {
        full->fullName = std::string(*n);
        ++named;
      }
    }
    if (auto* mgef = form->As<RE::EffectSetting>()) {
      if (auto d = ac::magic::redescribe(r)) {
        mgef->magicItemDescription = std::string(*d);
        ++described;
      }
      const std::string_view current = RE::ActorValueList::GetActorValueName(mgef->GetMagickSkill());
      if (auto av = ac::magic::school_av(r, current)) {
        const auto value = RE::ActorValueList::LookupActorValueByName(std::string(*av).c_str());
        if (value != RE::ActorValue::kNone) {
          mgef->data.associatedSkill = value;
          ++moved;
        }
      }
    }
  }
  SKSE::log::info("magic: {} renamed, {} described, {} moved school, {} missing; {} effects of a school with no "
                  "Skyrim actor value stay under their mod's",
                  named, described, moved, missing, ac::magic::unshown_schools().size());
}

}  // namespace argonia::plugin
