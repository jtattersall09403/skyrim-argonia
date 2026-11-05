<!-- The worked example for the writer packet (section 12). A real slice person, every answer, proved GREEN by
`dialogue_rewrite check --place place.mercantile-coast.chasepoint --plan` (tests/test_dialogue_packet.py re-proves
it from the answers below whenever the gates change). -->
**Prices-It-Fairly**, Chasepoint (a salvage stage on the mercantile coast). Argonian, male, a net-mender; chatter
rambling; quirk: says a price once and will not repeat it; his own view: the rope-stable family hides salvage from
the count. The plan makes him a carrier on four topics (the place, its people, its danger, salvage) and the
explainer of salvage. Argonian contractions: the plan allows him one contracted answer. He uses it once
("won't"); every other answer says "do not", "it is", "will not". Lengths 38, 23, 61, 18, 48, 59: no 20-word band
holds more than half.

**Chasepoint (local; he carries one fact)** (38 words)

> Legion soldiers laid these walls as a stop for the couriers who carried word. The horses stood where my ropes hang now. I come out before the light with a tarred needle and mend against the old plaster.

*Why:* The plan deals him only the Legion-built fact on this topic. He opens on his own sight of the walls, not on the pool line's order, and ends on his own work. One long sentence beside short ones keeps the spread.

**work at Chasepoint (local; not his to carry)** (23 words)

> Torn net comes to my rack on the stage at dusk. I look it over and name one price. I won't say it twice, whoever haggles.

*Why:* His own work, not the families' timber run (another speaker carries it). His quirk, a price said once, shows in how the answer is built and nowhere else. His one contraction is here.

**the people of Chasepoint (local; his deviation)** (61 words)

> Two families want that office. I do not care who holds it. I watch the sacks that the rope-stable people carry past my rack at dusk. The tally board never grows with them, however the clerks chalk it in the morning when the water has gone out. I told the clerk so at his own table. He writes what he likes.

*Why:* The pool fact the plan allots him comes first, the two claims, then his own view (bitter: the grievance once, as evidence). The keeper-claim fact is left to others. He gives what he saw, not a verdict, and none of the sheet's words.

**danger near Chasepoint (local)** (18 words)

> I do not cross the shingle below the stage without boots, for the water leaves nails. Fellrunners hunt the scrub.

*Why:* The short answer every speaker owes. The pool's danger as one practical instruction from his own beach, the way Morrowind's R11 does it. The Argonian marker is the full uncontracted clause, and it carries a fact of its own (the nails).

**the way from Chasepoint (local; not his to carry)** (48 words)

> West along the track the town begins before a net is half mended. East the road runs on to Fourth Stage. Did you come along the shore? Then you have seen what I read before I read a road: the boats and what they leave on our sand.

*Why:* The road comes first, from the pool line's facts but in his order and nouns. The port upbringing is audible mid-answer ("I read the boats before I read a road") as a deed of his own day and not a saying. He asks one real question and answers it himself.

**salvage (role; he explains it)** (59 words)

> You do not lift timber off a neighbour's stretch. Do that and the yard remembers it for a generation. Each family guards its own sand with sticks if it must, on any stretch where the sea has thrown a plank this week. I weigh every plank twice on the shed floor before I chalk the number on the beam.

*Why:* The plan leaves wreckage and the hereditary right to others, so he gives the two facts dealt to him, the guarded stretch and the ban on foreign timber, each with its cue word (guard, timber). The region mark ("I weigh every plank twice") is the coast's own oath turned into his deed at the shed, with a fact of its own.

His sample (the result's `sample`, written before any answer): "I was at the rack before the light. The knots came easier in the cold. The boats come in when I am done, never before. My fingers have done their thinking by then."

His devices (the result's `devices`, each quoted in the sample and in three answers, in no more than four): the hour of the day opening a sentence; the work of his hands closing one.

```json devices
[{"name": "hour of the day", "sample": "before the light", "answers": {"override.chasepoint-n1-4.chasepoint": "before the light", "override.chasepoint-n1-4.chasepoint-work": "at dusk", "override.chasepoint-n1-4.chasepoint-people": "at dusk"}},
 {"name": "his hands", "sample": "My fingers", "answers": {"override.chasepoint-n1-4.chasepoint": "tarred needle", "override.chasepoint-n1-4.chasepoint-directions": "a net is half mended", "override.chasepoint-n1-4.role-salvage": "chalk the number on the beam"}}]
```

His marks (the result's `marks` table; `check` reads each quoted words in the answer it names):

```json
{"race": {"answer": "override.chasepoint-n1-4.chasepoint-danger", "words": "I do not cross the shingle below the stage without boots, for the water leaves nails"},
 "upbringing": {"answer": "override.chasepoint-n1-4.chasepoint-directions", "words": "what I read before I read a road: the boats and what they leave on our sand"},
 "office": "none: he holds no office",
 "quirk": {"answer": "override.chasepoint-n1-4.chasepoint-work", "words": "I won't say it twice, whoever haggles"},
 "sore": "none: nothing recorded",
 "deviation": {"answer": "override.chasepoint-n1-4.chasepoint-people", "words": "I watch the sacks that the rope-stable people carry past my rack at dusk"},
 "wander": "none: his favourite subject is the yard and every answer already sits in it",
 "region": {"answer": "override.chasepoint-n1-4.role-salvage", "words": "I weigh every plank twice on the shed floor before I chalk the number on the beam"}}
```

What he never does: explain ojel or the Hist (others in the region do), send anyone elsewhere, use an address term
mid-answer, end on a quip, or share a sentence with Buys-Cheap, who carries the topics he does not.
