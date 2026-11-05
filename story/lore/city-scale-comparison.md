# City scale comparison: buildings and named NPCs in Morrowind and Skyrim cities

Purpose: parity numbers for a Helstrom of about 110 or about 85 parcels. Derived from UESP on 2026-10-06 through the MediaWiki API (era policy: these are game-content counts, not era-bound lore).

## Method

- Skyrim buildings: every `[[Skyrim:...]]` link in the `{{City Summary}}` template on the city page (government, inns, shops, guilds/temples, houses, other lists). This counts enterable named places, including farms outside the walls and some ships or mines listed under "other".
- Skyrim named NPCs: names in the `{{People}}` groups of `Skyrim:<City> People`, after removing guard-group rows, service icons, footnote markers and unnamed groups.
- Morrowind buildings: named building groups on `Morrowind:<City> People` (taverns, guilds, temple, manors, council halls, named houses), excluding the generic "Merchants" and "Other" groups. Morrowind city pages carry no building list, so unnamed homes are not counted and the ratio is an upper bound for Morrowind.
- Morrowind named NPCs: names in those `{{People}}` groups, "Merchants" and "Other" included.
- Vivec is the sum of the nine `Morrowind:Vivec ... People` pages (Foreign Quarter, the six cantons, Arena, Ministry of Truth).
- Counts are by script over wikitext and carry a few percent of parsing error. Sadrith Mora's page set is Telvanni Council House, taverns and a few houses only.

## Table

| City | Buildings | Named NPCs | NPCs per building | Source pages |
|---|---:|---:|---:|---|
| Balmora | 9 | 93 | 10.3 | Morrowind:Balmora People |
| Ald'ruhn | 13 | 89 | 6.8 | Morrowind:Ald'ruhn People |
| Sadrith Mora | 7 | 67 | 9.6 | Morrowind:Sadrith Mora People |
| Vivec | 77 | 311 | 4.0 | Morrowind:Vivec Foreign Quarter People, ... Canton People (x6), ... Arena People, ... Ministry of Truth People |
| Whiterun | 27 | 78 | 2.9 | Skyrim:Whiterun, Skyrim:Whiterun People |
| Solitude | 30 | 87 | 2.9 | Skyrim:Solitude, Skyrim:Solitude People |
| Windhelm | 26 | 71 | 2.7 | Skyrim:Windhelm, Skyrim:Windhelm People |
| Riften | 30 | 98 | 3.3 | Skyrim:Riften, Skyrim:Riften People |
| Markarth | 23 | 88 | 3.8 | Skyrim:Markarth, Skyrim:Markarth People |

Medians: Skyrim 2.9, mean 3.1 (range 2.7 to 3.8); Morrowind 8.2 over the four cities, 4.0 for Vivec, the only one with a full building set.

## Derived parity numbers

The Skyrim ratio counts every building in the city summary. The Morrowind ratios leave out unnamed homes, so they run high. Vivec (4.0) is the Morrowind figure that counts every canton.

| Helstrom size | Floor (Skyrim 3.0 per building) | Target (Vivec 4.0) | Skyrim highest ratio (Markarth 3.8) |
|---|---:|---:|---:|
| 110 parcels | 330 | 440 | 418 |
| 85 parcels | 255 | 340 | 323 |

Reading: a 105-door Helstrom already holds more buildings than any Skyrim city (23 to 30) and more than Vivec's named groups (77). At Skyrim's ratio it needs about 320 named NPCs, which is 3.5 times the biggest single Morrowind city page (Balmora 93) and the same order as all of Vivec (311). The roster must therefore be generated, with named slots only for the roles a quest or a service needs and the rest as unnamed residents carrying a home and a trade.

## Pages used

Morrowind:Balmora People, Morrowind:Ald'ruhn People, Morrowind:Sadrith Mora People, the nine Morrowind:Vivec People pages, Skyrim:Whiterun, Skyrim:Solitude, Skyrim:Windhelm, Skyrim:Riften, Skyrim:Markarth and their People pages. Vivec's own page (Morrowind:Vivec) is a disambiguation; the city is Morrowind:Vivec (city).
