# Build Helstrom

In its entirety, including NPCs (and their routines) and services and guards (and their patrols) and crime and everything else, but no quests yet.

Do not rebuild LOD at this point.

Flow is: agent has a go at building based on the sourced place, then I edit it, in tooling that you create for me.

Start with the exact Helstrom build from the BM&V mod (including extent of vegetation/ground cover clearance, and all decorative scatter and everything). Aim to replicate it in the chosen spot on our worldspace as faithfully as possible, using all the same assets, keeping the layout as close as possible (adapting as necessary to our specific land/locale and geographical features), seating everything correctly, and tweaking land (as local patches *without* regenerating the whole terrain or anything else) if necessary but as little as possible. Every building must come with its paired interior if the building was designed to be 'enterable' (i.e. to have a door that 'teleports' you to a paired interior). NPCs must also be placed, and all navmesh delivered.

Studio Tooling: I want to access it in a browser so I can use it from my tablet. It must be tablet friendly (I will be using my Huawei Matepad Pro with the stylus primarily). I don't mind whether this is streamed or deployed or browser native or whatever, you decide the best approach. What I want is:
* See and 'navigate' (rotate, zoom, pan etc) the 3D terrain and vegetation and the agent's first draft of the built place
* Simultaneously see and navigate the 'source place' (in this case, BM&V's Helstrom) on *its* original terrain
* Select objects in our place, move them in 3D space, rotate them, manipulate them.
* Select objects in the source place, see info about it, and be able to tap on our place to add one to it. Also be able to remove objects and buildings and NPCs etc from our place.
* Be able to search (text search) through all the assets used in the source place, and choose something to add to our place, then tap where to put it and then be able to manipulate it in 3D space
* Undo, redo, etc, all the usual types of controls
* See all NPC placements in our place and their routine paths and what times they will be at each spot. I want to be able to optionally edit their placements and waypoints and so on if I want to.
* All of this be super modern and user friendly and intuitive and not messy on the screen! Applying UI and UX design best practices for this kind of tooling
* Make minor terrain edits (e.g. levelling or raising small patches of land) that will get implemented as patches without requiring terrain rebuild
* For all edits, the default should be that the change I made is recorded as an agent 'fault' (we'll come back to this later), but I should be able to optionally mark something as a 'taste' call instead (i.e. the agent didn't necessarily do anything wrong, I just have a preference for a different option).
* Save my edits and everything be automatically updated in our database and in all the places that it needs to be such that the build will use my edited version not the agent's original. Navmesh automatically updated.
* An agent looks at the edits I've made and reasons about what they mean for our place builder agent Skill - what did it get wrong and why (that it can infer from the things I changed that were marked as 'faults' rather than 'taste calls'); what should change in the skill's recipe such that the next agent building a place gets it right first time - what is the generalisable pattern/lesson from this set of faults (rather than the hyper-specific lessons); apply those to the skills, leaving the skills reading simply as a clean recipe for how to do the thing correctly (not read as a patchwork or a history referencing feedback and decisions). 


Figure out and implement some smart and super fast way for us to test/prove the core functionality of this tooling, and try it out with me first before we dive into all of the above. I'm pretty confident we can build most of it, so just think about what the riskiest functionalities are and let's prove those as simply and rapidly as possible first before building the rest.
