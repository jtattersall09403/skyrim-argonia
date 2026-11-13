using System.Text.Json;
using System.Text.Json.Nodes;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// `questform --selftest`: the generic builder's refusals, proved off game on hand-made forms. The load order is one small
// plugin made here (one interior cell with one persistent person); no game data is read. Each case builds its forms with
// QuestForm.Build into an empty plugin and names the rule it must be refused by; the control case builds clean.
static class QuestFormTest
{
    const string BaseForm = """
    {"version":1,
     "quest":{"id":"quest.t.a","editor_id":"ARG_T_A","name":"Test","kind":"minor","start":{"by":"game","stage":10}},
     "stages":[{"number":10,"shown":true,"journal":"Start.","ending":"none","results":[]},
               {"number":20,"shown":true,"journal":"End.","ending":"completed","results":[]}],
     "objectives":[],
     "refs":[{"id":"p","kind":"person","enabled":true,"placement":{"existing":"PERSON"}}],
     "lines":[{"id":"l","speaker":"p","kind":"topic","prompt":"Hello.","text":"Hello.","written":true,"conditions":[],"results":[],
               "first_stage":10,"last_stage":10,"answers":[]}],
     "triggers":[],"must_live":[]}
    """;

    public static int Run(string[] a)
    {
        if (a.Length != 1 || a[0] != "--selftest") { Console.Error.WriteLine("questform --selftest"); return 2; }
        var ids = Path.GetTempFileName();
        try
        {
            File.WriteAllText(ids, "{\"blocks\":{\"questform\":\"0x800000-0x8FFFFF\"},\"ids\":{}}");
            return Cases(ids);
        }
        finally { File.Delete(ids); }
    }

    static int Cases(string idsPath)
    {
        var bad = 0;
        // the load order: one plugin with one interior cell holding one persistent person; its placed key goes into each form
        var fx = new SkyrimMod(ModKey.FromFileName("Fixture.esm"), SkyrimRelease.SkyrimSE);
        var npc = new Npc(fx) { EditorID = "FxBase" };
        fx.Npcs.Add(npc);
        var cell = new Cell(fx) { EditorID = "FxCell", Flags = Cell.Flag.IsInteriorCell };
        var placed = new PlacedNpc(fx) { Placement = new Placement { Position = new Noggog.P3Float(0, 0, 0) } };
        placed.Base.SetTo(npc);
        cell.Persistent.Add(placed);
        var block = new CellBlock { BlockNumber = (int)(cell.FormKey.ID % 10), GroupType = GroupTypeEnum.InteriorCellBlock };
        block.SubBlocks.Add(new CellSubBlock { BlockNumber = (int)(cell.FormKey.ID / 10 % 10), GroupType = GroupTypeEnum.InteriorCellSubBlock, Cells = { cell } });
        fx.Cells.Records.Add(block);
        var person = placed.FormKey.ToString();
        var spell = new Spell(fx) { EditorID = "FxSpell" };
        fx.Spells.Add(spell);
        var faction = new Faction(fx) { EditorID = "FxFaction" };
        fx.Factions.Add(faction);
        var perk = new Perk(fx) { EditorID = "FxPerk" };
        fx.Perks.Add(perk);
        var mark = new PlacedObject(fx) { Placement = new Placement { Position = new Noggog.P3Float(0, 0, 0) } };
        cell.Persistent.Add(mark);
        string Teach(string w, string key) => $$"""[{"do":"{{w}}","spell":"{{key}}"}]""";

        JsonNode Form(Action<JsonNode>? tweak = null)
        {
            var f = JsonNode.Parse(BaseForm.Replace("PERSON", person))!;
            tweak?.Invoke(f);
            return f;
        }
        // rule null: the forms must build; else they must be refused by that rule
        void T(string name, string? rule, Action<SkyrimMod>? prep, params JsonNode[] forms)
        {
            string got;
            try
            {
                var mod = new SkyrimMod(ModKey.FromFileName("Argonia.esp"), SkyrimRelease.SkyrimSE);
                prep?.Invoke(mod);
                var list = forms.Select((f, i) => ($"case{i}.json", JsonDocument.Parse(f.ToJsonString()).RootElement)).ToList();
                QuestForm.Build(mod, [fx], list, FormIds.Load(idsPath));
                got = "built";
            }
            catch (QuestForm.Refused r) { got = r.Rule; }
            catch (Exception e) { got = "crash " + e.GetType().Name + ": " + e.Message; }
            var ok = got == (rule ?? "built");
            if (!ok) bad++;
            Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {name}: expected {rule ?? "built"}, got {got}");
        }
        void R(string name, string? rule, Action<JsonNode> tweak, Action<SkyrimMod>? prep = null) => T(name, rule, prep, Form(tweak));

        R("control: a clean form builds", null, f => { });
        R("no such result word", "vocabulary", f => f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"conjure"}]"""));
        R("no such condition word", "vocabulary", f => f["lines"]![0]!["conditions"] = JsonNode.Parse("""[{"is":"wearing_green"}]"""));
        R("a start stage that is not a stage", "start", f => f["quest"]!["start"]!["stage"] = 15);
        T("two forms of one quest", "unique", null, Form(), Form());
        R("a quest whose editor id the plugin already holds", "editor-id", f => { }, mod =>
            mod.Quests.Add(new Quest(new FormKey(mod.ModKey, 0x900000), SkyrimRelease.SkyrimSE) { EditorID = "ARG_T_A" }));
        R("a result naming a ref not in the form", "refs-exist", f => f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"switch_on","ref":"nobody"}]"""));
        R("speaker_hostile as a stage's result", "vocabulary", f => f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"speaker_hostile"}]"""));
        R("not on number_compare", "vocabulary", f => f["lines"]![0]!["conditions"] = JsonNode.Parse("""[{"is":"number_compare","number":"n","op":">=","value":1,"not":true}]"""));
        R("a minor quest's who-must-live with main_message", "main-message", f =>
            f["must_live"] = JsonNode.Parse("""[{"ref":"p","fail_stage":20,"main_message":true}]"""));
        R("a must_live message that is not the kind's own", "message", f =>
        {
            f["quest"]!["kind"] = "main";
            f["must_live"] = JsonNode.Parse("""[{"ref":"p","fail_stage":20,"main_message":true,"message":"Some other words."}]""");
        });
        R("a placement with neither anchor nor container", "placement", f =>
            f["refs"]![0]!["placement"] = JsonNode.Parse("""{"base":{"kind":"existing_base","id":"00003B:Skyrim.esm"}}"""));
        R("a hostile existing person", "hostile", f => f["refs"]![0]!["hostile"] = true);
        R("a spell taught under our name", null, f => { f["names"] = JsonNode.Parse($$"""{"{{spell.FormKey}}":"Shadow"}""");
            f["stages"]![0]!["results"] = JsonNode.Parse(Teach("teach_spell", spell.FormKey.ToString())); });
        R("a spell taught with no name", "spell", f => f["stages"]![0]!["results"] = JsonNode.Parse(Teach("teach_spell", spell.FormKey.ToString())));
        R("a spell of no plugin", "form-key", f => { f["names"] = JsonNode.Parse("""{"000001:Nowhere.esm":"Shadow"}""");
            f["stages"]![0]!["results"] = JsonNode.Parse(Teach("forget_spell", "000001:Nowhere.esm")); });
        R("a group turned hostile that is a faction of ours", "faction", f =>
            f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"make_enemy","faction":"faction.ours"}]"""));
        R("a faction of the load order turned hostile", null, f =>
            f["stages"]![0]!["results"] = JsonNode.Parse($$"""[{"do":"make_enemy","faction":"{{faction.FormKey}}"},{"do":"leave_faction","faction":"{{faction.FormKey}}"}]"""));
        R("a perk given under our name", null, f => { f["names"] = JsonNode.Parse($$"""{"{{perk.FormKey}}":"Quiet Step"}""");
            f["stages"]![0]!["results"] = JsonNode.Parse($$"""[{"do":"add_perk","perk":"{{perk.FormKey}}"},{"do":"remove_perk","perk":"{{perk.FormKey}}"}]"""); });
        R("a perk given with no name", "perk", f =>
            f["stages"]![0]!["results"] = JsonNode.Parse($$"""[{"do":"add_perk","perk":"{{perk.FormKey}}"}]"""));
        R("a perk of no plugin", "form-key", f => { f["names"] = JsonNode.Parse("""{"000001:Nowhere.esm":"Quiet Step"}""");
            f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"add_perk","perk":"000001:Nowhere.esm"}]"""); });
        R("a marker put on the map", null, f => { ((JsonArray)f["refs"]!).Add(JsonNode.Parse($$$"""{"id":"m","kind":"marker","enabled":true,"placement":{"existing":"{{{mark.FormKey}}}"}}"""));
            f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"mark_on_map","ref":"m"}]"""); });
        R("a person put on the map", "map-marker", f =>
            f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"mark_on_map","ref":"p"}]"""));
        R("a bounty set on a faction of the load order", null, f =>
            f["stages"]![0]!["results"] = JsonNode.Parse($$"""[{"do":"set_bounty","faction":"{{faction.FormKey}}","amount":0}]"""));
        R("a bounty set on a faction of ours", "faction", f =>
            f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"set_bounty","faction":"faction.ours","amount":100}]"""));
        R("a room made the player's", null, f =>
            f["stages"]![0]!["results"] = JsonNode.Parse($$"""[{"do":"own_room","cell":"{{cell.FormKey}}"}]"""));
        R("a room of no plugin", "form-key", f =>
            f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"own_room","cell":"000001:Nowhere.esm"}]"""));
        R("a skill raised", null, f =>
            f["stages"]![0]!["results"] = JsonNode.Parse("""[{"do":"raise_skill","skill":"Sneak","by":5}]"""));
        Console.WriteLine(bad == 0 ? "questform selftest: PASS" : $"questform selftest: FAIL ({bad} wrong)");
        return bad == 0 ? 0 : 1;
    }
}
