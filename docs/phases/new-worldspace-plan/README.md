# Project Tamriel Worldspace

Goal: Create a new worldspace in parallel with our main work in this repo (which focuses on building out quests, factions, NPCs and dialogue in the BM&V worldspace).

The current project will prove that we can we can adapt our story and quest plan to an existing worldspace and build it into that world, on top of a preferred mod stack. The limit with that world is that it is only a certain amount of world space as created by the Black Marsh and Valenwood mod and doesn't cover the whole of Black Marsh.

 So the second stage of our work would be about creating our own new world space and then adapting our quest system and story to it. We will know by that point that we can do that adaptation, so we should be able to take all the lessons learned from this current repo in doing so (creating reusable agent skills for core components/recipes where appropriate)

 I want to start work on that now, in parallel with the BM&V work.

We will ultimately want to be able to release the new worldspace (with its quests and story and mod stack and everything) as its own mod (with dependencies) separate from our BM&V adaptation.

During testing, I will want to be able to easily choose between which of the two I play in Moonlight (via separate cards).

 The phase docs in this folder set out the plan.

 *Throughout*, for anything that will be done more than once, we should develop and iterate a set of agent skills for doing those things. i.e. every time I give feedback or correct something, we should be correcting and improving the relevant agent skills so that the next time they are used, that thing is right first time. But we *must* do this in a way that does not bloat them. The skills should not read as a patchwork or a history referencing feedback and decisions. They must always read simply as a clean recipe for how to do the thing correctly.

 # Previous attempts
 Previous attempts at generating a skyrim worldspace were unsuccessful overall. However, do not overreact to this. A big part of that was because we were trying to adapt a threejs worldspace with complex water systems and some poor texture work and shoehorn it into Skyrim in a way that was always doomed. The previous generating approach did have a lot of strengths, and some weaknesses that we will resolve this time around.

 World generation methods from earlier version of this repo was good at:
• Land/terrain, starting from our previous threejs version and/or the all Tamriel Heightmap and turning it into a Skyrim worldspace
• Mountains, slopes, cliffs the native Skyrim way
• Vegetation and trees, variation between regions and local level variety within regions (so regions feel varied internally and consistently different to each other), consistent with ecology research
• Creating realistic and nicely transitioning areas of forest and more open sections 
• Rocks and scatter
• navmesh
• authoring and placing NPCs, and I think setting their daily routines and paths (after a few goes at this but we should be able to resurrect from git history)
• LOD
• spawning rules for creatures between places, and riving bandits, with type and difficulty and loot and gear derived logically from region danger band and ecology (and with variation between regions, and within region by micro level geography and habitat)
• and before that the threejs repo was good at generating nice looking mountains (which then this repo turned into nice Skyrim native style terrain)

What it was bad at:
• Complicated water placement. So we will just have one water height for whole province.
• authoring and placing water types and direction of flow for rivers and streams, vs still water like lakes and ponds. So I would like to be able to draw on/directly edit myself which bodies should flow (and in what direction), which should be still, what type of water they are (e.g. blackwater swamp vs green water marsh vs ponds vs estuary vs ocean)
• building built places. It was ok I think at planning places conceptually, and good at designing in theory what they should deliver (from their data), but not at actually implementing the layout and placing the buildings and making it all look good. And very bad at things like boardwalks and bridges. Took a lot of work to get it to create pieces that connect/snap together as well. For every built place, I would like agents to find their closest semantically equivalent place in either the BM&V mod if it's there or KoTM if there isn't or vanilla Skyrim as last resort, and in the fancy new browser studio give me the 2d layout and 3d render of that place and in some way make it easy for me to use it as inspiration for the new place we're making. Like I want to be able to pick specific assets/meshes from the equivalent place, paired exteriors-and-interiors, etc, and place them myself on our new place (and as discussed have the vegetation clearance and land flattening and seating etc be taken care of automatically) and move them around if I want. And I want to be able to draw on paths and streets and so on, and them to automatically be textured and styled and dressed nicely in a Skyrim native way (and vegetation cleared).