// Our inventory and character sheet (1.12 r4, the "Argonia custom UI" card): the rules ArgoniaCore's glue needs to
// fill inventory.state and charsheet.state from the engine, kept here so they are unit-tested. No engine type: the
// glue reads the player's stacks and perks into these plain rows and pushes what comes back.
#pragma once
#include "argonia/core/sheet.h"
#include "argonia/core/messages.h"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace argonia::core::panes {

// The engine's item kinds that reach the inventory (FormType, read by the glue).
enum class Kind : std::uint8_t { weapon, ammo, armor, potion, ingredient, scroll, book, key, light, misc, soulGem };

msg::InventoryCategory category(Kind k, bool food);
// What the pad's A does, as the player reads it.
std::string action(Kind k, bool food, bool equipped);
// The stack's key: 8 hex digits of the form id (the views' id; the intent names it back).
std::string key(std::uint32_t form_id);
std::optional<std::uint32_t> form_of(std::string_view key);
// The order the view lists: by category, equipped first within one, then by name, then key.
void order(std::vector<msg::InventoryItem>& items);

struct Pools { double health, health_max, magicka, magicka_max, stamina, stamina_max; };

// The sheet: the seven attributes and 27 skills from the `stats` family (each skill's progress is the fraction of
// its base value toward the next whole rank), grouped by the class's major, minor and miscellaneous; the perks as
// the glue read them (already in tree order).
msg::CharsheetState charsheet(const Sheet& sh, std::string name, std::string race, const Pools& p, int perk_points,
                              std::vector<msg::CharPerk> perks);
std::string display_name(std::string_view id);  // "handToHand" -> "Hand to Hand", "longBlade" -> "Long Blade"

// Taking a perk: the refusal, as the sheet's notice words it, or nothing when it may be taken.
std::optional<std::string> perk_refusal(const msg::CharPerk* p, int perk_points);

// The engine menus whose opening the card replaces (router: inventoryMenu, statsMenu); the module the custom card's
// detection reads: Wind UI's DLL absent means the custom card.
inline constexpr std::string_view kWindUiModule = "WindUI.dll";

}  // namespace argonia::core::panes
