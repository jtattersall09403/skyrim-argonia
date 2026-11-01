#!/usr/bin/env bash
# 1.12-items (owner look 1): our build deployed (base_save.py's new game from the main menu makes argoniabase and
# ArgoniaWalk), then on ArgoniaWalk: the starting kit counted without any additem, each kit weapon equipped in third
# and first person, the Imperial light set worn, and Wind UI's inventory grid with the kit's icons.
#   ARGONIA_LANE=1.12-items tooling/job_guard.sh run --gpu=pick items -- tests/journeys/batches/lane-1.12-items.sh [tag]
set -x
cd "$(dirname "$0")/../../.."
T=${1:-proof}; O=out/items/$T; mkdir -p $O
R=infra/gpu-box/run.sh
PY="$HOME/.argonia/venv/bin/python"
B="$PY tools/bridge.py"
pause() { $PY -c "import time; time.sleep($1)"; }
$R up
[ -n "${NO_DEPLOY:-}" ] || make deploy DEPLOY_ARGS="${DEPLOY_ARGS:-}" || { $R stop; exit 1; }
ready() { for i in $(seq 1 40); do $B console 'getgamesetting fJumpHeightMin' >/dev/null 2>&1 && return 0; done; return 1; }
$B launch && $B load ArgoniaWalk && ready
KIT="ARG_Weap_SteelSword ARG_Weap_SteelMace ARG_Weap_SteelScimitar ARG_Weap_HuntingBow ARG_Ammo_SteelFlightArrow ARG_Armo_Imperial_Cuirass ARG_Armo_Imperial_Boots ARG_Armo_Imperial_Gauntlets ARG_Armo_Imperial_Helm"
for k in $KIT; do echo "KIT $k $($B console "player.GetItemCount $k" | grep -o '>> [0-9.]*')"; done | tee $O/kit-counts.txt
$B pad 'LY=1:500'; ready
shot() { $B screenshot $O/$1.png; }
for a in ARG_Armo_Imperial_Cuirass ARG_Armo_Imperial_Boots ARG_Armo_Imperial_Gauntlets ARG_Armo_Imperial_Helm; do $B console "player.equipitem $a"; done
for w in ARG_Weap_SteelSword ARG_Weap_SteelMace ARG_Weap_SteelScimitar ARG_Weap_HuntingBow; do
  $B console "player.equipitem $w"; [ $w = ARG_Weap_HuntingBow ] && $B console "player.equipitem ARG_Ammo_SteelFlightArrow"
  $B input key R 150 engine; pause 3  # ready the weapon (sheathed after each swap)
  $B console "player.setangle z 180"; pause 1; shot "$w-3p-front"
  $B input key F 300; pause 2; echo "1P $w $($B console IsPC1stPerson | grep -o '>> [0-9.]*')"; shot "$w-1p"; $B input key F 300; pause 2
done
$B input key I 150 engine; pause 3; shot inventory
$B input key Escape 150 engine; pause 1
[ -z "${KEEP:-}" ] && $R stop
true
