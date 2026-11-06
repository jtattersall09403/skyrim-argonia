Nothing waits on this. It is the read of the first story slice, fitted to Black Marsh & Valenwood as it stands (your ruling of 6 November). The detail is in story/design/quests/adaptation.md, section 5.

**What is in the slice (11 quests)**

- **The opening act of the main quest (MQ01, MQ03, MQ04, MQ05)**, with the new-game start: a new game opens in the hold of a debt-labour broker's barge at Lilmoth's Dock1. Character creation is the gang's processing, with the roll read aloud. The gang is marched along the shore to its camp at the edge of Hereguard's paddies. There the Unbound Root's cell strikes, the camp's Hist withdraws and its clutch dies. Then comes the Veiled Reed's offer in an unmarked Lilmoth house, the first turned Hist at a village east of Lilmoth, and BM&V's own ship to Helstrom and the empty seat of the Scalded Throne.
  - Kept: every beat of the authored act.
  - Changed: the barge is a broker's, not the state's (your Q7). The camp's tree is the gang families' cutting from Nine Bends, because the lore gives Hereguard no Hist. The Reed's station is an unmarked Lilmoth house, because Lilmoth denies the state.
- **Night-Reed (TG01, TG02):** Tilts-The-Jug's desk at Soulrest (BM&V's "Docks", renamed), a thief's round to watch, the Chapter under Pusbottom in Lilmoth, then a dive for a lockbox.
- **Chainbreakers (BC01 to BC03):** the Owing is the heart of this line.
  - BC01: a hearing at an ex-Archein estate just north of Blackrose, where every line of an account is true and still unjust.
  - BC02: a fire in the cells under the Rose's outer post at the town's edge.
  - BC03: a broker's barge at Soulrest.
  - Each choice costs the player something.
- **Two local quests in Act I's towns:** a river-beast at Helstrom's landing that ends in an arbitration, and a youth's walk-out into the basin.

**What waits, and why**

- The other 706 quests wait until you have tried the slice.
- The Marsh Charter was in the first draft and came out. BM&V's Gideon has only an unfurnished, doorless room and no living people, and its village is in another worldspace.
- Lines whose seats BM&V cannot yet host also wait: the Shadowscales, Nisswo, Umbriel, Sunken Archive, Many-Root, Thorn Ash-Reed, League and Reed-Sail. The detectives have no quests yet.

**Edits to BM&V (all minor)**

- 63 edits in all. People are placed at fixed levels. Doors are added or locked, six places are named, and the Rose's cell room and Lilmoth's pier get navmesh.
- One clean-up per place: every Nord, Thalmor, Imperial soldier, skeleton, draugr-style walker, Dwemer construct and levelled actor in the slice's places is switched off. That includes BM&V's "New Order" soldiers, who are in no lore. Every templated actor that stays gets a fixed level.
- Nothing is levelled against you, and no Nordic element is added.

**How it was checked**

- A checker now runs in `make check`. It checks that every place resolves and that no edit undoes another's need. It also checks prerequisites, danger order, capacity, lore citations, Nordic elements and levelling.
- Seven review rounds by fresh, independent reviewers each round (Act I, each line, cross-line, lore, vibe and society). Round 7 raised nothing blocking.
- Act I's four quest records are rewritten from this plan and reviewed the same way: ROUNDS (fill when MQ03 and MQ04 are clean).

**Calls I made (record, not questions)**

- Soulrest, Gideon and the other missing cities sit on unnamed BM&V settlements, or are named in talk only.
- The Lost City of Act IV is not BM&V's Dwemer pyramid ruins as they stand (the lore reviewer ruled no Dwemer in Black Marsh). Its home is chosen when Act IV is fitted.
- Valenwood hosts nothing in the slice. Its own two start quests wait until you first enter Valenwood.
- New extrapolations are in the lore's gap register (QA1 to QA5 and those the record writer adds).

**Left for the build to measure:** whether Pusbottom's canal is deep enough to dive, whether the camp's water holds an islet, the Rose cell's shape (a borrowed vanilla room behind the same door is the fallback), and the exact BM&V statics named in the edits.

To reply, comment on this issue. Nothing here needs an answer. Cost: no AWS time was used for this work.
