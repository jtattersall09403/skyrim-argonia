// Travel: a stop operator's passage (boat, coach, rootworm) as vanilla's carriages do it (tools/places/build.py plan_travel says how and why): a quest of
// ours, per operator a top-level topic whose line links one topic per destination, each destination's INFO gated on the
// operator's faction and the player's gold and running the one compiled fragment script TIF_ARG_BoatTravel.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

static class Boat
{
    static TranslatedString T(string s) => new(Language.English, s);
    static string Str(JsonElement e, string k) => e.GetProperty(k).GetString()!;

    static ConditionFloat Cond(ConditionData d, CompareOperator op, float v) => new() { CompareOperator = op, ComparisonValue = v, Data = d };

    static DialogResponses Info(Write.Ctx ctx, string fk, string prompt, string reply, FormKey faction, int? fare)
    {
        var info = new DialogResponses(C.Fk(fk), C.Rel) { Flags = new DialogResponseFlags(), Prompt = T(prompt) };
        info.Responses.Add(new DialogResponse { Text = T(reply), ResponseNumber = 1, Emotion = Emotion.Neutral });
        var inFaction = new GetInFactionConditionData();
        inFaction.Faction.Link.SetTo(faction);
        info.Conditions.Add(Cond(inFaction, CompareOperator.EqualTo, 1));
        if (fare is { } f)
        {   // vanilla's carriage gates on GetGold against the fare, run on the target (the player)
            var gold = new GetGoldConditionData { RunOnType = Condition.RunOnType.Target };
            info.Conditions.Add(Cond(gold, CompareOperator.GreaterThanOrEqualTo, f));
        }
        return info;
    }

    public static void Build(Write.Ctx ctx, JsonElement boats)
    {
        var mod = ctx.Mod;
        foreach (var b in boats.EnumerateArray())
        {
            var script = Str(b, "script");
            var q = b.GetProperty("quest");
            mod.Quests.Add(new Quest(C.Fk(Str(q, "fk")), C.Rel)
            {
                EditorID = Str(q, "edid"), Name = T(Str(q, "name")), Flags = Quest.Flag.StartGameEnabled, Priority = 50, Type = Quest.TypeEnum.Misc,
            });
            var quest = C.Fk(Str(q, "fk"));
            foreach (var m in b.GetProperty("boatmen").EnumerateArray())
            {
                var faction = C.Fk(Str(m, "faction"));
                var hub = m.GetProperty("hub");
                var branch = new DialogBranch(C.Fk(Str(m, "branch")), C.Rel)
                {
                    EditorID = Str(m, "branch_edid"), Category = DialogBranch.CategoryType.Player, Flags = DialogBranch.Flag.TopLevel,
                };
                branch.Quest.SetTo(quest);
                branch.StartingTopic.SetTo(C.Fk(Str(hub, "topic")));
                mod.DialogBranches.Add(branch);

                DialogTopic Topic(JsonElement t, string prompt, DialogResponses info, int priority)
                {
                    var d = new DialogTopic(C.Fk(Str(t, "topic")), C.Rel)
                    {
                        EditorID = Str(t, "edid"), Name = T(prompt), Priority = (byte)priority, Category = DialogTopic.CategoryEnum.Topic,
                        Subtype = DialogTopic.SubtypeEnum.Custom, SubtypeName = new RecordType("CUST"),
                    };
                    d.Quest.SetTo(quest);
                    d.Branch.SetTo(branch.FormKey);
                    d.Responses.Add(info);
                    mod.DialogTopics.Add(d);
                    return d;
                }

                var hubInfo = Info(ctx, Str(hub, "info"), Str(hub, "prompt"), Str(hub, "reply"), faction, null);
                Topic(hub, Str(hub, "prompt"), hubInfo, 50);
                foreach (var d in m.GetProperty("dests").EnumerateArray())
                {
                    var info = Info(ctx, Str(d, "info"), Str(d, "prompt"), Str(d, "reply"), faction, d.GetProperty("fare").GetInt32());
                    var props = JsonSerializer.SerializeToElement(new[] { new Dictionary<string, object> { ["name"] = script, ["props"] = new object[]
                    {
                        new { name = "Destination", type = "object", value = Str(d, "marker") },
                        new { name = "Fare", type = "int", value = d.GetProperty("fare").GetInt32() },
                        new { name = "Gold001", type = "object", value = Str(b, "gold") },
                    } } });
                    var vm = C.Vmad(props);
                    var ad = new DialogResponsesAdapter { Version = vm.Version, ObjectFormat = vm.ObjectFormat };
                    ad.Scripts.AddRange(vm.Scripts);
                    ad.ScriptFragments = new ScriptFragments { FileName = script, OnEnd = new ScriptFragment { ScriptName = script, FragmentName = "Fragment_0" } };
                    info.VirtualMachineAdapter = ad;
                    Topic(d, Str(d, "prompt"), info, 50);
                    hubInfo.LinkTo.Add(new FormLink<IDialogTopicGetter>(C.Fk(Str(d, "topic"))));
                }
            }
        }
    }
}
