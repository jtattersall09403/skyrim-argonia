---
name: place-routines
description: Where a place's people sleep, work and walk - beds, households under one roof, guards and their shifts, services and travel-stop operators, actor bases of the place's people, how complete people must be, and the place's law (a jail or the native Owing). Use when a draft's people, beds, guards, services or sentence are judged or changed; who each person is belongs to place-people.
---

# Beds, routines and law

Step 7 of the place path ([place-system](../place-system/SKILL.md)). Stages: `people`, `stations` (the worker's
stop), `jail`. Who each person is (name, household's story, trade, wealth) is `place-people`; the draft gives
placeholder names.

Every promise-list row shown by a `schedule` (a person at a stall, on a watch, asleep at an hour a quest sends
the player) is delivered here: the person's routine puts them there at that hour, and the row turns `built` naming
the person.

## On the source's own furniture

The carried place already holds its people's furniture: beds, the trader's counter, the fire and cook stand, racks,
idle and sit markers. Put each person there by hand, by trade and household: their `bed` on a carried bed, their
`work` stop on the source's own marker or furniture of that trade, a day spot where the source's people stood. A
person whose role the source has no furniture for gets it added beside the place's own (`place-adapt`). Look at
each spot (`look at <person>`); every spot stands on the walking mesh.

## How complete people are

A place's people are as complete as King of the Murkmire's own places, by type of person and place, and no more:

- every named person with a role has a bed (their own, or a shared bunk of their faction), a sleep package and a
  work spot;
- ferrymen and hostiles have none;
- no crowds: the record's population, no more.

## Beds decide the people

1. Every promised service person works; residents fill the homes' remaining beds, then the open beds (a camp's tents
   and bedrolls), until the place holds its record's population, each with a routine. A place short of beds is given
   them (`place-adapt`, then `draft add` and `draft people`).
2. One household per house: a family headed by the working person who lives there, then a partner, then kin;
   never strangers together. A couple shares a double bed owned by their household's faction.
3. An inn that rents a room keeps one bed unowned (`stations.rent_bed`); the innkeeper keeps the inn day and night
   and owns no bed.
4. Guards keep two 12-hour shifts on the streets and sleep in a barracks or their camp's beds, one to a bed, never in
   the inn. A guard whose camp bed the network does not reach sleeps in a home's free bed as its lodger.
5. A place with no watch sets `draft.guards` (0); a free bed the record promises is named in `draft.free_beds`.
6. People follow Skyrim's days (`docs/research/skyrim/town-life.md`); never bend a day to satisfy a check. The
   `people` stage sets every routine's work stop to the person's `work`; a role's spot is set with `draft.roles`
   `{<role>: {space, pos}}`.

## Services and travel stops

- A promise a townsman keeps beside his own life (a rootworm stop's handler, a follower) makes no person: it goes to
  a resident (`place-people` chooses; until then the first resident with no service).
- A `boat-stop`, `coach-stop` or `rootworm-stop` is kept by its operator, working at the landing: a boat's at the
  water's edge or on a deck over it, a coach's at the gate on the major road, a rootworm's where the story places
  its stop. The thing the handler works at carries `stop` (the give kind); the `people` stage sets the work and
  hours there. Destinations and fares are the travel network's (`docs/design/travel-network.md`).
- Traders work where the source's own trader of that trade worked.

## Actor bases

Bases come from the source's own actors. Where the source's people are not the place's, name in
`draft.people_from` the sources whose actors are (`["bmv.helstrom"]` for Argonians). A source with no person to build
on takes Black Marsh's own. The build's `levelled` and `people` checks and `draft check` fail a person built on a
beast, a levelled character or a template that is no fitting base.

## The law

The sentence follows `place_law` (`docs/design/law.md`); the `jail` stage builds it (`draft jail <place_id>`) once the walks and doors stand.

- No law: no sentence; guards speak no arrest lines.
- A foreign law jails, in the copied room holding the jail kit; the tools place the prisoner's bed, the jail marker,
  the release point and the two evidence chests. Look at the cell (`look at`).
- A native law has the Owing (labour served in place of a jail, `docs/design/law.md`): a work spot where the place's labour is done with a bedroll, a return spot at least
  384 units off on a street, the stolen goods chest under the ground, our Owing line and resist line for the
  place's guards, who must share one guard faction (`<place>.guard` in `people.jsonl`). Look at both spots.

Enforced by the checks: a bed for every sleeper, an unowned bed to rent, guards out of the inn, every resident in
one household under one roof, every service given and worked (`draft check`; the build's `people`, `services` and
`jail` checks).
