using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// Combat and movement overrides from the owner's walk of 2026-11-07, called last from Generate (after Talk), so the two
// new records here never move an earlier form id.
static class Combat
{
    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        // Run with a weapon drawn: AMMCO.esp (Mern edit) wins NPC_1HM_MT and NPC_2HM_MT with run 170 and 130, a fast walk.
        // The run fields take Dark Souls Movement's run (300 every way), the same speed as the sheathed run
        // (NPC_Default_MT, Dark Souls Movement); walk and turn speeds stay AMMCO's.
        var movts = Survey.Winners<IMovementTypeGetter>(mods);
        foreach (var id in new[] { "NPC_1HM_MT", "NPC_2HM_MT" })
        {
            var (w, from) = movts.Values.Single(v => v.rec.EditorID == id);
            if (from.FileName != "AMMCO.esp") throw new Exception($"{id}: winner is {from}, not AMMCO.esp");
            var t = w.DeepCopy();
            t.LeftRun = t.RightRun = t.ForwardRun = t.BackRun = 300f;
            mod.MovementTypes.Add(t);
        }

        // No health regeneration for the player; magicka and stamina regenerate as before. Bethesda's way for a constant
        // change to a regen rate is an ability whose effect is a Value Modifier on the rate's multiplier (the races'
        // and diseases' regen abilities); HealRateMult at 0 stops health regen, potions and spells still heal.
        var mgef = mod.MagicEffects.AddNew("ARG_NoHealthRegenEffect");
        mgef.Flags = MagicEffect.Flag.Detrimental | MagicEffect.Flag.Recover | MagicEffect.Flag.HideInUI | MagicEffect.Flag.NoArea;
        mgef.Archetype = new MagicEffectArchetype(MagicEffectArchetype.TypeEnum.ValueModifier) { ActorValue = ActorValue.HealRateMult };
        mgef.CastType = CastType.ConstantEffect;
        mgef.TargetType = TargetType.Self;
        mgef.MagicSkill = ActorValue.None;
        mgef.ResistValue = ActorValue.None;
        mgef.SecondActorValue = ActorValue.None;
        var spel = mod.Spells.AddNew("ARG_NoHealthRegen");
        spel.Name = "No Health Regeneration";
        spel.Type = SpellType.Ability;
        spel.CastType = CastType.ConstantEffect;
        spel.TargetType = TargetType.Self;
        spel.EquipmentType.SetTo(FormKey.Factory("013F44:Skyrim.esm")); // EitherHand, as vanilla abilities
        spel.Effects.Add(new Effect { BaseEffect = mgef.ToNullableLink(), Data = new EffectData { Magnitude = 100, Area = 0, Duration = 0 } });
        // On the player's base record, as the player's starting abilities are: holds on every new game, no script.
        var key = FormKey.Factory("000007:Skyrim.esm");
        var player = mod.Npcs.FirstOrDefault(n => n.FormKey == key) ?? (Npc)Survey.Winners<INpcGetter>(mods)[key].rec.DeepCopy();
        player.ActorEffect ??= new();
        player.ActorEffect.Add(spel.ToLink<ISpellRecordGetter>());
        if (!mod.Npcs.Any(n => n.FormKey == key)) mod.Npcs.Add(player);
    }
}
