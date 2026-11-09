# Controls

Current truth for the play stack (`mods/dependencies.json`). The keyboard is a Mac keyboard over Moonlight. The pad is
the GameSir X2 in Xbox layout (Skyrim reads it as an Xbox pad), laid out like Dark Souls by owner ruling #51
(2026-11-06). The pad layout is Skyrim's own control map with its gameplay pad column changed by
`infra/gpu-box/controlmap.py`; `C:\argonia\controls\controlmap.txt` on the play machine is laid loose in Data by
`stack.ps1 on`, and `deploy.sh` re-applies it. The same file moves three keyboard keys (ruling 2026-11-09: Option/Alt is awkward on a Mac): sprint and dodge on Space, jump on Left Shift, and the walk/run hold that Left Shift held now on Alt. Other keyboard and mouse bindings are Skyrim's defaults plus the mods' own.

## Moonlight on a Mac

- Option is sent as Alt, Command as the Windows key (avoid Command: it can pull Windows' Start menu over the game).
- Console: the key left of `1` (`§` on a UK Mac keyboard). If that types nothing, try the `` ` `` key beside left Shift.
- Right click: a two-finger click on the trackpad, or a mouse. Blocking means holding it, so a mouse is far easier.
- Moonlight's own keys: Ctrl+Option+Shift+Q leaves the stream, Ctrl+Option+Shift+Z frees the mouse.

## The table

| Action | Mac keyboard | GameSir X2 (Xbox layout) | Notes |
|---|---|---|---|
| Move | W A S D | left stick | 8-way (True Directional Movement) |
| Walk / run toggle | Caps Lock (hold Option (Alt) to walk) | push stick part way | |
| Sprint | hold Space | hold B | hold longer than half a second |
| Dodge: backstep | tap Space, standing still | tap B, stick centred | TK Dodge RE: tap under 0.5 s; costs 15 stamina; i-frames |
| Dodge: roll | tap Space while moving | tap B with the stick held | rolls the way you move (Dynamic Dodge, 8-way) |
| Light attack (right hand) | left click | RB | |
| Heavy (power) attack | hold left click | RT (one press) | One Click Power Attack (`iKeycode 281`); RT is also bound to the right attack so the attack handler sees it |
| Block | hold right click | hold LB | needs an empty left hand, a shield or a two-hander |
| Parry | hold right click, tap left click as the blow lands | hold LB, tap RB as the blow lands | Elden Parry: the light bash is the parry, window 0.02 to 0.2 s into it; costs no stamina |
| Riposte | left click after a parry | RB after a parry | Rim Parry And Execution with its One Parry patch: one parry makes a human or draugr kneel; lock on first; stand within 120 degrees in front |
| Backstab | locked on behind the enemy: hold right click, tap left click, then left click | LB+RB, then RB | Rim Parry And Execution, within 60 degrees behind |
| Guard counter | block a hit, then power attack within 1.5 s | block a hit (LB), then RT within 1.5 s | Elden Counter; kept beside the parry (they key on different moves: a block versus a bash) |
| Lock on | tap F | click right stick | hold F switches first/third person |
| Switch locked target | mouse flick / scroll wheel | flick right stick | |
| Jump | Left Shift | Y | |
| Climb | W + Left Shift at a wall | Y at a wall | FreeClimb; drop off with Left Shift / Y again |
| Draw / sheathe | R | X | |
| Activate / talk / take | E | A | |
| Sneak | Ctrl | click left stick | |
| Cast left hand | right click with a spell in the left hand | LB | |
| Cast right hand | left click with a spell in the right hand | RB | |
| Shout / power | Z (hold for full shout) | LT | |
| Favourites | Q | d-pad up or down | |
| Tween menu (skills, items, map, magic) | Tab | d-pad left or right | |
| Inventory / magic / map / skills | I / P / M / / (slash) | d-pad left or right, then the stick | |
| Journal and system menu | J (journal), Esc (system) | Start (≡) | save, load, settings |
| Wait | T | Back (⧉) | |
| Change view | hold F | hold right stick click | |
| Console | key left of 1 (see above) | none: needs a keyboard | |
| Mod settings (MCM) | Esc, then Mod Configuration | Start, then Mod Configuration | |

## What moved on the pad (ruling #51)

| Input | Skyrim's default | Now | Default moved to |
|---|---|---|---|
| B | Tween menu | sprint and dodge | d-pad left or right |
| LB | sprint (and dodge) | block | B |
| RB | shout | light attack | LT |
| RT | right attack | power attack (and right attack) | |
| LT | left attack / block | shout | LB |
| d-pad left / right | favourite hotkeys 1 and 2 | Tween menu | none: the favourites menu (d-pad up or down) does the same job |

## Known gaps

- Attack queued during a dodge: our own SKSE plugin ArgoniaDodgeBuffer (skse/ArgoniaDodgeBuffer, owner ruling #51) is
  built but not yet laid on the play machine; until it is, an attack pressed during a roll is dropped.

- Parry and riposte work on humans and draugr only (Rim Parry And Execution's own scope), and in third person only.
- Precision gives melee real hit shapes; its camera shake on hits is off (`precision` row).
