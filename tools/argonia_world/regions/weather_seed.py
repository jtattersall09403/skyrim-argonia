"""1.15 §d's authored weather set, written once into the world database by `migrate.py --weathers-1-15`; afterwards
the rows are the source (decision 0030) and this module is the record of the first authoring.

Every colour is authored by hand per slot and time of day (owner 2026-11-01: every slot authored, never derived; the
yellow-green tint goes). Sources, in order (0032, 0033): Black Marsh & Valenwood's own look, which has no WTHR or
IMGS of its own (Black Marsh.esm's 5,0x130762 BlackMarshClimate draws Skyrim.esm's SkyrimFog 40, SkyrimStormRain 20,
SkyrimOvercastRain 20, SkyrimCloudy 10, SkyrimClear 10, read 2026-11-01 with terrain/esm.py), so its weathers are kept
by reference to those forms (Tropical Skyrim's restyles) in the group lists; then the climatology
(docs/design/research/world-terrain/black-marsh-climatology.md §2–§4: two fog regimes, the dry NW pole, the
montane belt, the interior bayou's dawn mist) and 55-light-sky-time.md §97–98 (humid golden low-sun air, a night
that is green not blue, fog lit by the real light). No vanilla or Tropical Skyrim number is copied (decision 0003).

Palette rows: slot -> (sunrise, day, sunset, night) as RGB hex. Drafted by hand per weather; each slot then given its
own hue character (the zenith bluer, the horizon warmer, the ground bounce browner, the canopy ambient greener, the
water tannin-green), and the few colours still on a copy path nudged a few units off it, so no slot is a scaled or
mixed copy of another (checks.weather_slots). The slots' whys are per weather (WHY_SLOT) over the
general role of each slot (ROLE).
"""
from __future__ import annotations

TOD = ("sunrise", "day", "sunset", "night")

ROLE = {
    "skyUpper": "the zenith", "skyLower": "the sky below the cloud deck", "horizon": "the horizon band",
    "fogNear": "fog colour at the near distance", "fogFar": "fog colour at the far distance",
    "ambient": "the ambient light", "unknown": "the engine's second ambient term (kept just under ambient's hue)",
    "sunlight": "the directional light on the ground", "sun": "the sun disc", "stars": "the stars (night only)",
    "effectLighting": "light on spell and particle effects", "cloudLodDiffuse": "distant clouds, lit side",
    "cloudLodAmbient": "distant clouds, shade side", "skyStatics": "sky statics (distant silhouettes)",
    "waterMultiplier": "the water's reflection and colour multiplier", "sunGlare": "the glare around the sun",
    "moonGlare": "the glare around the moons (night only)", "dalcUp": "directional ambient from above",
    "dalcSide": "directional ambient from the four sides", "dalcDown": "directional ambient from below (the bounce "
    "off the ground and water)",
}

# id -> (EditorID, template weather id (references only), state, fog m: day near, day far, night near, night far,
#        image day, image dawn, image night, why)
# Fog distances sit inside Skyrim.esm's measured ranges for the weather's class and time of day
# (skyrim-does-it-this-way §7; checks.weather_fog): far at least the class's vanilla median, near above 0, fog max at
# most SkyrimFog's 0.95 so the sky is never fully hidden (owner play test 3 finding 18; lane-1.15-r4-light).
WEATHERS = {
    "clear-dry": ("ARG_Weather_clear_dry", "clear-ff", "clear-humid", 15, 1400, 5, 714, "day", "dawn", "night",
                  "dry-season subsidence clear: the NW dry pole's best visibility, a pale hot sky over olive haze "
                  "(climatology §4 NW border; 55 §98 cloudless days belong to dry spells)"),
    "monsoon-overcast": ("ARG_Weather_monsoon_overcast", "cloudy-ma", "monsoon-downpour", 15, 700, 10, 480,
                         "overcast", "overcast", "night",
                         "a monsoon break day under a full deck: flat bright light, no rain (55 §98 coverage ladder)"),
    "wet-rain": ("ARG_Weather_wet_rain", "rain-ma", "monsoon-downpour", 15, 400, 10, 280, "rain", "rain", "night",
                 "wet-season rain: a wall of grey-green water over the interior (55 §98; climatology §2 monsoon)"),
    "mist": ("ARG_Weather_mist", "fog-ma", "ground-mist", 2, 700, 2, 430, "mist", "mist", "night",
             "radiation mist: pooled over inland water and wet ground after a clear calm night, burning off after "
             "dawn (climatology §2, §4 interior basins; 55 §97)"),
    "sea-fog": ("ARG_Weather_sea_fog", "fog-co", "ground-mist", 4, 450, 2, 430, "seafog", "seafog", "night",
                "advection sea fog on the open coast and up the estuaries (climatology §2, §3 exp(-dCoast/8))"),
    "montane-haze": ("ARG_Weather_montane_haze", "cloudy-ff", "ground-mist", 15, 700, 10, 480, "montane", "dawn",
                     "night", "the montane cloud-forest belt's haze on the border ranges, summits clear above it "
                     "(climatology §2 altitude, §4 border mountains; 55 §97)"),
    "tannin-haze": ("ARG_Weather_tannin_haze", "clear-ma", "dry-haze", 15, 700, 10, 480, "haze", "dawn", "night",
                    "dry-season tannin haze: a brown-gold air over peat water (climatology §4 dry haze)"),
    "squall": ("ARG_Weather_squall", "storm-rain", "sea-squall", 10, 450, 5, 280, "storm", "storm", "night",
               "a sea squall on the Padomaic coast and the delta (climatology §3 storm exposure, §4)"),
    "storm": ("ARG_Weather_storm", "storm-rain", "storm", 8, 380, 5, 250, "storm", "storm", "night",
              "the marsh thunderstorm: afternoon convection, lightning, green-black (55 §98)"),
}

# the sky's behaviour: classification, wind, cloud speed, sun glare, sun damage, precip fade in/out, thunder,
# fog power day/night, fog max day/night, why
SKY = {
    "clear-dry": ("Pleasant", 0.12, 0.015, 0.9, 1.0, 0.0, 0.0, 0.0, 1.2, 1.0, 0.55, 0.7,
                  "still dry air; a soft fog curve that never closes the view"),
    "monsoon-overcast": ("Cloudy", 0.3, 0.03, 0.1, 0.2, 0.0, 0.0, 0.0, 1.0, 1.0, 0.8, 0.85,
                         "a moving deck, no direct sun; fog builds evenly"),
    "wet-rain": ("Rainy", 0.55, 0.05, 0.0, 0.0, 0.2, 0.9, 0.0, 0.9, 0.9, 0.95, 0.95,
                 "rain thick enough to close the middle distance"),
    "mist": ("Cloudy", 0.03, 0.005, 0.3, 0.0, 0.0, 0.0, 0.0, 0.6, 0.6, 0.95, 0.95,
             "calm air (radiation mist needs it); fog starts 2 m out; its far opens from 430 m at night "
             "(vanilla's cloudy median, 30,000 u) to day 700 m through sunrise, the burn-off inside one weather (vanilla's FogMA: 35,000 to 50,000 u)"),
    "sea-fog": ("Cloudy", 0.2, 0.02, 0.15, 0.0, 0.0, 0.0, 0.0, 0.7, 0.7, 0.95, 0.95,
                "a sea breeze carries the bank in; dense but not at the eye"),
    "montane-haze": ("Cloudy", 0.25, 0.025, 0.4, 0.3, 0.0, 0.0, 0.0, 1.1, 1.0, 0.85, 0.9,
                     "upslope wind feeds the belt; haze not whiteout"),
    "tannin-haze": ("Cloudy", 0.2, 0.02, 0.5, 0.5, 0.0, 0.0, 0.0, 1.3, 1.1, 0.8, 0.85,
                    "dry warm air holding fine particles; a long soft fog ramp"),
    "squall": ("Rainy", 0.8, 0.08, 0.0, 0.0, 0.1, 0.9, 0.3, 0.8, 0.8, 0.95, 0.95,
               "the one fast arrival (55 §98: 6 min); wind and rain bands"),
    "storm": ("Rainy", 0.7, 0.07, 0.0, 0.0, 0.1, 0.9, 0.6, 0.8, 0.8, 0.95, 0.95,
              "convective storm: thunder often, rain heavy"),
}

# image spaces: id, EditorID, template (references and HDR), saturation, brightness, contrast, why; tint off
IMAGES = (
    ("day", "ARG_ImageSpace_marsh_day", "10A1BF:Skyrim.esm", 1.06, 1.0, 1.05,
     "dry clear day: a little saturation for the hot greens, contrast for hard sun; colour from the slots"),
    ("dawn", "ARG_ImageSpace_marsh_dawn", "10A1C0:Skyrim.esm", 1.04, 0.98, 1.02,
     "low sun through humid air: the gold is in the sunlight slot, not a screen wash"),
    ("night", "ARG_ImageSpace_marsh_night", "10A1C2:Skyrim.esm", 0.88, 0.92, 1.0,
     "night: saturation down so the green-black slots read as dark, not tinted"),
    ("mist", "ARG_ImageSpace_marsh_mist", "10A1C7:Skyrim.esm", 0.9, 1.0, 0.94,
     "mist flattens: contrast down, saturation down a step"),
    ("haze", "ARG_ImageSpace_marsh_haze", "10A1BF:Skyrim.esm", 0.98, 1.02, 0.97,
     "tannin haze: soft contrast; the brown-gold is in the fog slots"),
    ("storm", "ARG_ImageSpace_marsh_storm", "10A1CB:Skyrim.esm", 0.86, 0.92, 1.08,
     "storm: desaturated, hard contrast for lightning"),
    ("overcast", "ARG_ImageSpace_overcast", "10A1BF:Skyrim.esm", 0.95, 1.0, 0.98,
     "overcast: flat light, saturation a little down"),
    ("rain", "ARG_ImageSpace_rain", "10A1CB:Skyrim.esm", 0.9, 0.96, 1.02,
     "rain: wet surfaces darken; saturation down"),
    ("seafog", "ARG_ImageSpace_sea_fog", "10A1C7:Skyrim.esm", 0.88, 1.02, 0.92,
     "sea fog: the flattest of the set, bright and soft"),
    ("montane", "ARG_ImageSpace_montane", "10A1BF:Skyrim.esm", 0.96, 1.0, 1.0,
     "montane haze: crisper than the lowland, a little cool"),
)

# per weather: why the palette is what it is (applied to every slot row with the slot's role)
WHY_SLOT = {
    "clear-dry": "dry clear: pale hot blue-green sky, olive horizon haze, white-gold sun; night green-black",
    "monsoon-overcast": "overcast: grey-green deck lit from above, soft shadowless ambient, damp horizon",
    "wet-rain": "rain: slate green-grey, dim cool ambient, water dark; night near-black green",
    "mist": "radiation mist: milky green-white near, sun a diffuse pale disc, dawn pink-gold through it",
    "sea-fog": "sea fog: cool salt grey-white with a sea-green cast, sun barely through",
    "montane-haze": "montane haze: cool mossy grey belt, clearer blue above, mist-grey crag light",
    "tannin-haze": "tannin haze: brown-gold air over peat water, a copper sun",
    "squall": "squall: slate sea-green under a racing deck, cold flat light",
    "storm": "storm: green-black deck, bruised horizon, lightning-ready dark ambient",
}

P = {}  # weather -> slot -> (sunrise, day, sunset, night)
P["clear-dry"] = {
    "skyUpper": ("577FAC", "4B86C8", "676E9E", "0C1A1F"),
    "skyLower": ("C99A6A", "91B5CD", "C38057", "1E2723"),
    "horizon": ("E4B174", "CDD2A5", "DF8E4B", "2F3029"),
    "fogNear": ("9F8664", "8D9A7F", "AC805D", "202E21"),
    "fogFar": ("A08667", "BCC4A5", "AF8060", "2C342C"),
    "ambient": ("6C6351", "7A8367", "685745", "1A281F"),
    "unknown": ("655A4E", "717664", "614C42", "181E23"),
    "sunlight": ("F4BA73", "F9ECC1", "F09C53", "465643"),
    "sun": ("FFCB85", "FFFCDD", "FFAB5E", "58665E"),
    "stars": ("000000", "000000", "000000", "C6D6C2"),
    "effectLighting": ("E8CCA2", "F4F5E2", "E4B48E", "5E7360"),
    "cloudLodDiffuse": ("DBAA79", "ECEBD9", "D38C61", "303435"),
    "cloudLodAmbient": ("78695F", "9AA198", "72574D", "121B1D"),
    "skyStatics": ("C9A27A", "D9D9C0", "C38A64", "383940"),
    "waterMultiplier": ("B5AA84", "BFCEAC", "B19674", "3B4A44"),
    "sunGlare": ("FFD498", "FFF4CF", "FFB470", "000000"),
    "moonGlare": ("000000", "000000", "000000", "89A292"),
    "dalcUp": ("5E554A", "7D8465", "685447", "2C3F38"),
    "dalcSide": ("605746", "6E7158", "5C4A3A", "1F2719"),
    "dalcDown": ("4D4332", "5D5D40", "49392B", "161B10"),
}
P["monsoon-overcast"] = {
    "skyUpper": ("6A7379", "879695", "726A62", "0C1A1F"),
    "skyLower": ("8D8880", "AFAFA6", "8E7B71", "1E1F1A"),
    "horizon": ("A99B8A", "B9BCAC", "A58C75", "242622"),
    "fogNear": ("898A7B", "8E9888", "867F73", "162321"),
    "fogFar": ("8D8B7B", "ABB4A2", "99876F", "242D23"),
    "ambient": ("5E6153", "788573", "5C594F", "142019"),
    "unknown": ("59564E", "6E756F", "5A4C4C", "17171A"),
    "sunlight": ("AF9C81", "C8CAAF", "AB8C75", "514F4D"),
    "sun": ("CDBB95", "E1E3CC", "C9AB8A", "3D5040"),
    "stars": ("000000", "000000", "000000", "6D796B"),
    "effectLighting": ("B4B09A", "D0D8C6", "B0A08E", "4C5B4E"),
    "cloudLodDiffuse": ("989588", "BBC1B1", "94857A", "262B2E"),
    "cloudLodAmbient": ("5A5B57", "757978", "585351", "0F1616"),
    "skyStatics": ("897F76", "9FA48D", "837A69", "242B2C"),
    "waterMultiplier": ("898D7A", "9DAA94", "857F6E", "2D3E36"),
    "sunGlare": ("B4A482", "CFCAB6", "AE9274", "000000"),
    "moonGlare": ("000000", "000000", "000000", "576F60"),
    "dalcUp": ("5A554F", "7A8377", "5C574D", "263F42"),
    "dalcSide": ("585748", "707764", "564E44", "161E16"),
    "dalcDown": ("494536", "5D5F4A", "4A3B35", "131111"),
}
P["wet-rain"] = {
    "skyUpper": ("4D5258", "5E666C", "564C55", "081411"),
    "skyLower": ("66635B", "787D77", "685955", "131913"),
    "horizon": ("777361", "8A8F80", "75675C", "131F1C"),
    "fogNear": ("606755", "6E7D6B", "5F5A52", "0F1E14"),
    "fogFar": ("696C60", "7C847C", "6E6357", "1C2316"),
    "ambient": ("434B44", "586759", "48463F", "12181B"),
    "unknown": ("43423E", "535F4F", "453C3C", "0D1A15"),
    "sunlight": ("9F9578", "959881", "80695A", "4D534A"),
    "sun": ("988D6E", "ADB398", "988168", "2F3735"),
    "stars": ("000000", "000000", "000000", "3B453E"),
    "effectLighting": ("8A8A77", "A2AE9C", "8A8071", "3A473C"),
    "cloudLodDiffuse": ("6A6B62", "7C8980", "72605B", "1A1D22"),
    "cloudLodAmbient": ("3E413B", "4C5751", "403B39", "060E12"),
    "skyStatics": ("5F5F50", "6A796B", "5C5352", "1F241C"),
    "waterMultiplier": ("545E54", "62746A", "59554B", "273224"),
    "sunGlare": ("847866", "9CA08A", "836E5F", "000000"),
    "moonGlare": ("000000", "000000", "000000", "384842"),
    "dalcUp": ("4C5450", "5D6F68", "514D49", "243F44"),
    "dalcSide": ("44463A", "545D4E", "464038", "141B10"),
    "dalcDown": ("39372B", "48473E", "3B3129", "0F0D0D"),
}
P["mist"] = {
    "skyUpper": ("97A0A5", "B1C0BF", "A3969F", "182223"),
    "skyLower": ("CDBCAE", "D1D9C3", "C8B5A0", "262927"),
    "horizon": ("E1C8B1", "DBDFC8", "DABAA0", "2B3229"),
    "fogNear": ("8A887F", "92968F", "A69C8C", "283533"),
    "fogFar": ("8F887F", "BBC2BB", "958976", "27302C"),
    "ambient": ("8A8777", "95A295", "837C72", "1C2821"),
    "unknown": ("897972", "90968F", "81726A", "1E1E22"),
    "sunlight": ("ECCA9F", "E9E6CC", "E6BA93", "4C534B"),
    "sun": ("FAE0BD", "F8F6E1", "F5D0AD", "4C5553"),
    "stars": ("000000", "000000", "000000", "6F7D73"),
    "effectLighting": ("DCD0BA", "E6EFE0", "D8C4B0", "546558"),
    "cloudLodDiffuse": ("D0C6B6", "E0E8D2", "CFB7A5", "2A2F32"),
    "cloudLodAmbient": ("85827F", "A3A5A2", "847974", "12191B"),
    "skyStatics": ("BCB0A5", "C7C9B7", "BDA693", "2C382F"),
    "waterMultiplier": ("B1B09C", "B6C5B5", "AAA193", "36453E"),
    "sunGlare": ("FDE2C1", "FBF6E5", "FCD0B3", "000000"),
    "moonGlare": ("000000", "000000", "000000", "697C72"),
    "dalcUp": ("5B544F", "7B827A", "5E564F", "2D3E3A"),
    "dalcSide": ("847F6C", "909786", "807364", "1E261E"),
    "dalcDown": ("736E5A", "808172", "6F5F54", "191D17"),
}
P["sea-fog"] = {
    "skyUpper": ("89969D", "A3B2B7", "8B8A99", "151A21"),
    "skyLower": ("B3AEA6", "C3C5C4", "AE9FA1", "202325"),
    "horizon": ("C5BAB0", "CDD0CD", "C1AEA1", "222B29"),
    "fogNear": ("838C85", "8D9893", "A29C97", "1E2D2D"),
    "fogFar": ("8F8881", "B6C0C2", "8D8388", "1F2A28"),
    "ambient": ("747D73", "88978E", "72736B", "16221E"),
    "unknown": ("6F706E", "838A8A", "6D6666", "101924"),
    "sunlight": ("CCBEA3", "D9DCC8", "C8AE97", "4B5350"),
    "sun": ("E1D4B9", "EAECDD", "DAC2B0", "445045"),
    "stars": ("000000", "000000", "000000", "576361"),
    "effectLighting": ("BFC1B7", "D8E3D5", "BEB4AA", "48574D"),
    "cloudLodDiffuse": ("B2B3AE", "CAD1CB", "AFA99F", "22292D"),
    "cloudLodAmbient": ("6B7274", "869194", "6C6969", "0A1319"),
    "skyStatics": ("A3A295", "B9B5B3", "9F9988", "292B33"),
    "waterMultiplier": ("959E92", "A5B6AC", "919086", "2E4035"),
    "sunGlare": ("E7D6BD", "EFEEE1", "E2C6B0", "000000"),
    "moonGlare": ("000000", "000000", "000000", "536661"),
    "dalcUp": ("535752", "76867D", "575756", "2B3E3E"),
    "dalcSide": ("6E7368", "828D7F", "6C6960", "18201B"),
    "dalcDown": ("5F5F56", "6D786C", "5D554E", "151516"),
}
P["montane-haze"] = {
    "skyUpper": ("6782A4", "6994C1", "6F789C", "0E1A21"),
    "skyLower": ("A9A49A", "A6BABA", "A89486", "192023"),
    "horizon": ("C1B69F", "BDC4BE", "BDA28D", "212727"),
    "fogNear": ("868783", "8B9890", "9C968A", "182724"),
    "fogFar": ("8A8A7F", "B3BDB7", "91867D", "213027"),
    "ambient": ("687161", "78897B", "666559", "15221A"),
    "unknown": ("67615C", "717A74", "615854", "141A19"),
    "sunlight": ("D8BE93", "EBEACE", "D4AA83", "415743"),
    "sun": ("EDD4A7", "FAF8E1", "E9BF95", "455551"),
    "stars": ("000000", "000000", "000000", "A2B4AB"),
    "effectLighting": ("CEC4AA", "E0EBDC", "CAB49E", "51624F"),
    "cloudLodDiffuse": ("BFB6A5", "D6DBD1", "BBA695", "262F31"),
    "cloudLodAmbient": ("686F6A", "889390", "68635F", "101918"),
    "skyStatics": ("9D9B84", "A6AAA6", "94897D", "2F3629"),
    "waterMultiplier": ("949D8F", "A5B6A8", "938E7E", "394137"),
    "sunGlare": ("F1D6AD", "FBF6E5", "ECC49E", "000000"),
    "moonGlare": ("000000", "000000", "000000", "778C82"),
    "dalcUp": ("55574F", "76837F", "5B5850", "2A3F39"),
    "dalcSide": ("646958", "748174", "625D50", "172417"),
    "dalcDown": ("555546", "61695E", "51473E", "131711"),
}
P["tannin-haze"] = {
    "skyUpper": ("777A8A", "7992A9", "7B6E7C", "101A1B"),
    "skyLower": ("C4A070", "B6AD8F", "C08965", "232123"),
    "horizon": ("DBA976", "CDBA85", "D7985D", "282C24"),
    "fogNear": ("A08662", "9C9673", "AE8355", "1B2822"),
    "fogFar": ("A58560", "B8A88B", "AF8255", "282F21"),
    "ambient": ("6C6149", "7A795F", "685741", "15231E"),
    "unknown": ("67564A", "736E5C", "634C40", "172115"),
    "sunlight": ("F0B067", "F9DEA5", "EC9855", "455642"),
    "sun": ("FDBF71", "FFECBB", "F9A55E", "4E5D4E"),
    "stars": ("000000", "000000", "000000", "A2AC95"),
    "effectLighting": ("DEC094", "ECE1BE", "DAAC82", "56654F"),
    "cloudLodDiffuse": ("CFA679", "D2CDA6", "CB9065", "2C312D"),
    "cloudLodAmbient": ("766551", "8A8574", "705949", "141819"),
    "skyStatics": ("B99870", "C1B289", "B88463", "2E3437"),
    "waterMultiplier": ("A3946E", "ABA884", "9F8362", "3D403E"),
    "sunGlare": ("FFC886", "FFEEC7", "FCAC6C", "000000"),
    "moonGlare": ("000000", "000000", "000000", "899682"),
    "dalcUp": ("605544", "85816B", "665445", "28412E"),
    "dalcSide": ("685942", "797458", "64523C", "1C2417"),
    "dalcDown": ("584334", "665744", "513D2C", "161910"),
}
P["squall"] = {
    "skyUpper": ("3C4A50", "4B5C62", "40404A", "081015"),
    "skyLower": ("56575B", "66746A", "584F4F", "0F121A"),
    "horizon": ("686B5F", "788182", "6A5D5A", "191F10"),
    "fogNear": ("4C595D", "5B6C6A", "54554B", "0B161A"),
    "fogFar": ("5C6364", "657479", "5D5A58", "17171F"),
    "ambient": ("3C4843", "4A5B55", "3E403B", "0D1810"),
    "unknown": ("393C40", "454E50", "3B3638", "0B1113"),
    "sunlight": ("969684", "859087", "6D6356", "4F5156"),
    "sun": ("848378", "9BA79E", "84796A", "2B3135"),
    "stars": ("000000", "000000", "000000", "293834"),
    "effectLighting": ("7C847B", "94A49E", "7C786F", "36433C"),
    "cloudLodDiffuse": ("5B605F", "6A797A", "5A5758", "111520"),
    "cloudLodAmbient": ("32393D", "404D4F", "343335", "050F0D"),
    "skyStatics": ("4A5651", "5D6567", "4C474A", "191E1A"),
    "waterMultiplier": ("46584F", "536761", "474A48", "1E2B22"),
    "sunGlare": ("777469", "919692", "776A5F", "000000"),
    "moonGlare": ("000000", "000000", "000000", "2E3E3E"),
    "dalcUp": ("45514A", "53665C", "454545", "283F3B"),
    "dalcSide": ("3C4237", "48524C", "3C3A34", "131A0D"),
    "dalcDown": ("2D342B", "3B3F3B", "342929", "0D0A0D"),
}
P["storm"] = {
    "skyUpper": ("35403B", "424E48", "3E3437", "060E10"),
    "skyLower": ("504D43", "595E56", "524A3A", "150F0C"),
    "horizon": ("62594C", "71705D", "61534A", "111B0B"),
    "fogNear": ("464D43", "51614C", "4B463C", "0C1615"),
    "fogFar": ("56544A", "62685A", "584A46", "131B08"),
    "ambient": ("363E31", "44503C", "38362F", "09100A"),
    "unknown": ("33342E", "3F443C", "352C2C", "060A0D"),
    "sunlight": ("9F9671", "8E8F71", "685346", "555240"),
    "sun": ("7A7356", "8C9376", "7A6750", "252925"),
    "stars": ("000000", "000000", "000000", "272F23"),
    "effectLighting": ("74735C", "86947D", "726759", "2E392D"),
    "cloudLodDiffuse": ("4F5348", "66655E", "514944", "101013"),
    "cloudLodAmbient": ("2F2F2D", "384137", "2E2929", "08070A"),
    "skyStatics": ("47433B", "585845", "493B39", "161B0B"),
    "waterMultiplier": ("404735", "4C5745", "443F2E", "1B2414"),
    "sunGlare": ("6F664F", "82836F", "6F5C49", "000000"),
    "moonGlare": ("000000", "000000", "000000", "28342C"),
    "dalcUp": ("3D4339", "495549", "3F3B37", "1F4234"),
    "dalcSide": ("363A2C", "434B3A", "3A3427", "091307"),
    "dalcDown": ("2B2B1F", "38352D", "2D231D", "080803"),
}

# Every group holds our sunny dry-season clear-dry (the dossiers' dry season; a visible sun for the god rays), and no
# plain Skyrim.esm weather: SkyrimClear 0x081A and SkyrimCloudy 0x012F89 (Tropical Skyrim leaves both vanilla) left the
# jungle group, so the climate's fallback list is ours too (decision 0012).
# the realisations of each group's synoptic states after 1.15: at most five weathers a group, so with the region's
# mist weather a list holds 1-6 entries as vanilla's do (skyrim-does-it-this-way §7: p50 3, max 6). The ground-mist
# state is realised by the region's mist regime (REGIMES), not here. Group -> state -> [weather ids].
REALISE = {
    "coastal": {"clear-humid": ["clear-dry", "cloudy-co"], "monsoon-downpour": ["wet-rain"], "sea-squall": ["squall"],
                "storm": ["storm-rain"]},
    "marsh": {"clear-humid": ["cloudy-ma", "clear-dry"], "monsoon-downpour": ["wet-rain", "monsoon-overcast"],
              "storm": ["storm"]},
    "jungle": {"clear-humid": ["cloudy-ma", "clear-dry"], "monsoon-downpour": ["wet-rain", "monsoon-overcast"],
               "storm": ["storm"]},
    "uplands": {"clear-humid": ["clear-ff", "cloudy-ff", "clear-dry"], "dry-haze": ["tannin-haze"],
                "storm": ["storm-rain"]},
    "lowland": {"clear-humid": ["clear-ff", "cloudy-ma", "clear-dry"], "dry-haze": ["tannin-haze"],
                "monsoon-downpour": ["wet-rain"]},
}

# the mist regimes: id -> (weather, why, {season: (chance, why)}). The chance is the fog weather's share of the
# region's list in that season, ungated by hour: vanilla gates no entry by hour and its fog weather carries its own
# time-of-day fog (skyrim-does-it-this-way §7); marsh lists hold fog at 28-35 % as WeatherTundraMarshNoPrecip's
# FogMA 28 and Falkreath's Fog 35 do (§7). Only the seasonal shift rides a global (seasons are new to vanilla, §7).
REGIMES = {
    "radiation": ("mist",
                  "radiation mist forms on clear calm nights over wet ground and burns off after dawn (climatology §2); "
                  "its fog curve (thick at night and dawn, lifting by day) does the dawn work",
                  {"dry": (35, "peaks in the dry/recession season (climatology §2, §3 'heaviest dawn mist'); "
                                "Falkreath's Fog 35 is vanilla's top (skyrim-does-it-this-way §7)"),
                   "hatching": (32, "the turn: nights still often clear"),
                   "wet": (28, "monsoon nights are cloudy; vanilla's marsh FogMA 28 is the floor (§7)")}),
    "sea_fog": ("sea-fog",
                "advection fog rolls in on the sea breeze's reversal (climatology §2, §3 exp(-dCoast/8))",
                {"dry": (30, "warm air over cooler shelf water in the dry season"),
                 "hatching": (25, "the transition"),
                 "wet": (20, "rain and squalls mix the air")}),
    "montane": ("montane-haze",
                "the cloud-forest belt clings to the massif, thick in rain, clear on settled days "
                "(climatology §2 altitude, §4; 55 §97)",
                {"dry": (20, "subsidence clears the belt on settled days"),
                 "hatching": (30, "convection returns"),
                 "wet": (35, "windward mid-slope rain maximum")}),
}

# land region -> regime rule (1.15 §d.3): mountains and hills at least half the region's cells: montane; a coastal
# weather group: sea fog; a misty ecological class: radiation; else none (the NW dry pole, climatology §4).
MOUNTAIN_CLASSES = ("border-mountains", "upland-hills")


# The Community Shaders Exponential Height Fog (owner play test 3 finding 9: mist banks below the eye). Its density is
# fogDensity/1000 * 2^(-falloff/1000 * (z - fogHeight)) (ExponentialHeightFog.hlsli), so the bank's top, a tenth of its
# density, is BANK_TOP_U above fogHeight. Falloff 30 is beyond the CS menu's 2.0 slider (a falloff of 2 tops out
# 1,661 u, 24 m, up: a slab, never a bank), which is why each mist weather's own file carries all three values.
HEIGHT_FOG = {"fogHeightFalloff": 30.0, "fogDensity": 0.5}
BANK_TOP_U = 3321.93 / HEIGHT_FOG["fogHeightFalloff"]  # log2(10) * 1000 / falloff
BAND_SPAN_M = 1.6  # a band's water levels lie within this, so one height keeps every region's bank top under its eye


def band_fog_height_u(lo_m: float, hi_m: float) -> float:
    """The fog height (u) for a band of regions whose median water lies at lo_m..hi_m: the middle of the heights that put
    the bank top at or above the highest water and at or below the lowest water's eye."""
    from tools.argonia_world import skyrim_units as su
    a = su.metres_to_units(hi_m) - BANK_TOP_U
    b = su.metres_to_units(lo_m) + su.EYE_HEIGHT_UNITS - BANK_TOP_U
    return round((a + b) / 2, 1)

