<!-- imported unchanged from elder-souls-argonia docs/decisions/0141-one-price-contract-coin-goods-or-a-favour.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0141 One price contract: coin, goods or a favour; money thins inland; every service kind pays the same way

**Decision (owner).** Trade and services share one price
contract. A price is a gold number from the barter band
([world/76](../world/76-stats-progression.md) §124: Mercantile,
disposition, no haggle). It is settled in one of three ways: coin from the
purse; goods, valued at the item record's `value` through the same band;
or a favour, a quest hook on the service record that marks the debt paid
when that quest completes. The purse, the goods and the favour are the
whole of payment in the game; no other medium exists.

Coin is the leftover Imperial gold: "gold" in system text, "drakes" in a
mouth ([style guide](../standards/text/style-guide.md) § Currency), a
septim only where lore text names the stamped coin. Money thins inland by
the purse rule, never by a second economy: a merchant's purse comes from
the place tier (city, town, village, interior); village traders hold
almost no coin and settle in goods, so the player leaves a village with
things, not drakes; the deep interior holds none and a price there is
goods or a favour. The three tiers are the lore's
([settlement-register](../../../world/sources/lore/extrapolation/settlement-register.md) § 7,
extrapolated from canon's "five gold" at the frontier and the interior's
"fresh slugs and sturdy tools").

Each merchant has a trade class (Morrowind's rule): the class sets what
they stock and what they buy; a general trader is broad; a village trader
in kind takes what the village uses. Stock is generated from class and
culture tables with per-person overrides, never hand-written per shop.

Service kinds are data, not code: a kind is a record word, a payload and a
pricing rule, registered in one table that later phases extend. 2.6 makes
barter, train, rest, travel, repair and recharge work end to end. Spells,
blessings and cure disease take the money and record the purchase in 2.6;
their effects are the one effect stack's and land in 2.9. "Stable" is
deleted: boats replace horses, and the boat service (buy, hire, recover) is
a kind 2.15 adds to the table. Ferries are talk, pay, arrive and are
complete without any boat record.

The world clock advances through one primitive, owned by 2.6: advance by N
hours, with the people catch-up. Travel uses it by route length, with a
fade, so a trip can end after dark at a shut shop; wait uses it and is
free; restock runs on it; 2.8 builds the rest sitting on it.

Trainers are existing slice people with a trainer field and a few lines,
added by the layer path ([0140](0140-layers-on-a-built-place-never-rebuild-it.md)).

The boat records and the mooring layer (2.15b) are the first step of 2.15,
after swim and climb, with moorings landing on built places as a layer;
nothing between 2.6 and 2.15 reads a boat or mooring record.

**Why.** One contract means 2.9, 2.10, 2.11 and 2.15 add an effect, a kind
or a favour, never a payment path, and nothing in the slice takes money
for nothing. Settling in goods needs only the value every item already
carries, so the lore's coin-to-barter gradient costs no second economy and
gives the interior its intended feel: the further in, the less money
works. Favours tie the economy to the quest runtime from the first
instance instead of bolting a barter-for-labour system on later. Trade
classes make the choice of shop matter, which is the Morrowind feel the
project rests on. A single clock primitive stops rest, wait, travel and
restock each inventing their own time. Moorings land as a layer, beside the
controller that uses them: one design pass over the network beats two.
