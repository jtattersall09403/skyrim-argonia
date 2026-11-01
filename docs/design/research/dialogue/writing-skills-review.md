<!-- imported unchanged from elder-souls-argonia docs/research/dialogue/writing-skills-review.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Review of two public writing-skill repos, for one-person NPC dialogue

Lane 2.7d13-skills, 2026-10-19. Asked for by the owner after the round 1 Chasepoint samples
([feedback](../../../lanes/2.7d/owner-words/feedback-round1-samples.md), last bullet): "Review these
thoroughly and see if we can lift and adapt any of what they do into our context."

Both repos were cloned read-only into `/tmp/skill-review/` and read as text; nothing from them was run.
They are untrusted third-party material and fan-written prompts: priors for method, never a source of
lore or facts ([0002](../../old-decisions/0002-era-and-source-confidence.md)). Licences: EveryDay-Writer is
MIT, creative-writing-skills is Apache 2.0, so adapting rules with a credit line is allowed.

## Reconciliation block

| Live doc | Covers | This review |
| --- | --- | --- |
| [text-and-voice/ai-writing-tells.md](../text-and-voice/ai-writing-tells.md) | Lexical, syntactic and structural AI tells with fixes, five reviewer tests | CONFIRMS almost all of EveryDay-Writer's anti-AI list (negative parallelism, tricolon, tacked-on -ing, throat-clearing, aphorism, self Q&A). SUPERSEDES nothing. ADDS: the "not reliable" caveat on word lists, the cluster rule, and the protect-human-signs list (Lift 6, 7). |
| [.claude/skills/dialogue-write/SKILL.md](../../../.claude/skills/dialogue-write/SKILL.md) §2, §4 and `references/tells.md`, `references/style.md` | Two passes (voice, then facts), the stranger test, endings, overuse, usefulness | CONFIRMS: enter late and leave early (our "endings"), two jobs per line (our "one plain usable thing, then the speaker's own"), fabrication ban (our grounding gate). NEW to us: Lifts 1 to 5, 8 to 13, 15 to 17. |
| [text-and-voice/dialogue-rulings-index.md](../text-and-voice/dialogue-rulings-index.md) | One row per dialogue ruling | The owner's round 1 words (too pithy, "does not" for "doesn't", "claim", "the count", "the tally", no context for the player) are not yet rows; this review's Lifts 3, 9 and 15 answer them. |
| [standards/text/style-guide.md](../../standards/text/style-guide.md), [style-core.md](../../standards/text/style-core.md) | House grammar, hard bans, shape faults | CONTRADICTED on three surface rules only (see "Where their rules clash with ours"); otherwise silent. |

Single doc to edit: for the evidence, [text-and-voice/ai-writing-tells.md](../text-and-voice/ai-writing-tells.md)
(add Lifts 6 and 7 and the two repos to its Sources); for the writer-facing rules,
`.claude/skills/dialogue-write/references/tells.md` (the Lift list is the input). This file sits at
`docs/research/dialogue/` because the brief names that path; the existing home for the theme is
`docs/research/text-and-voice/`, so the README row there should point here, or this file should move
there when the lifts land.

## How to read this review

Coverage is complete by file name (Part 1 and Part 2 name every skill, reference, agent, prompt and
doc file in both repos). Depth differs: files that bear on dialogue, voice, critique or revision were
read in full; platform, packaging and knowledge-base files were read by heading and opening paragraphs
and are marked "skimmed". "Applies" means a rule an NPC-dialogue writer can use; "Does not" says why.

What kind of text each repo is built for decides most of the verdicts:

- EveryDay-Writer targets a human writer publishing newsletters, LinkedIn posts, copy and some fiction,
  in their own voice. Its centre is an anti-AI rule file and a voice-fingerprint onboarding. It is
  nonfiction-first: its fabrication rule (§0.2) says "in fiction, invented detail is the entire job".
- creative-writing-skills targets a novelist with an agent team (muse, writer, critic, editor,
  reader-sim, character-sim). Its centre is a reader-reward model, a list of LLM failure modes, a
  critique method and a knowledge base. It is prose-fiction-first.
- Our task is neither: short spoken topic answers, one speaker at a time, to a player who is a stranger,
  where every fact comes from a record and the lines must read like Morrowind. Most of their rules
  therefore apply to the voice and anti-AI side and almost none to length, structure or platform.

---

# Part 1: EveryDay-Writer (Deupaxx/EveryDay-Writer, v0.3.0, MIT)

## 1.1 Entry and core files

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `SKILL.md` | Master dispatcher `ew`. Four steps: resolve voice, onboard if missing, load per-voice references, dispatch to a sub-skill. Every invocation reads runtime contract, workspace, anti-AI rules, slop commandments, voice resolver, references, then the sub-skill. Defines interactive, file and embedded output modes and the "never present a first draft" loop. | Applies: the read order (rules first, voice second, task last) and "wrong-voice output is fluent and plausible, which makes it far harder to catch than an error" (our wrong-person risk). Does not: routing to platform skills, voice tags, vault persistence. |
| `CLAUDE.md` | Contributor guide: plugin discovery requirements, the 4-step flow, "core constraints", cowork port rule (copies must be edited in both places). | Does not. One idea worth noting: copies drift, so state a single source (we already do). |
| `README.md` | Marketing and install: what the system is, the A-Player framing, command list, install paths. Skimmed. | Does not. |
| `core/runtime-contract.md` | Short restatement of read order, precedence, fabrication rule, two-pass loop and final checklist, so a skill can load a small file first. | Applies: a short contract in front of the long rules is the pattern our packet already uses. |
| `core/anti-ai-rules.md` | The main rule file (read in full). §0 operating standard; §0.1 precedence (voice profile outranks style rules, a pasted sample outranks the profile); §0.2 fabrication rule; §1 banned words; §2 sentence tells; §3 tone tells; §4 structure tells; §5 formatting tells; §6 craft rules (King, Lamott, Brande: second draft minus 10 percent, show don't announce, R.U.E., specificity is proof); §7 two-pass loop with three interrogation questions and a checklist; §8 voice profile; §9 what not to flag; §10 signs of human writing to preserve. | Applies, most of it: §0.1, §0.2 (as a bracket mechanic), §2 (negative parallelism, countdown, self Q&A, aphorism formulas, conversational openers, tailing negation fragments), §6 R.U.E., §7.1, §9, §10. Does not: §1 word list (ours is wider and tuned to Argonia register), §4 and §5 (headings, bullets, bold, title case, emoji), the A-Player tone of §0. |
| `core/ai_slop_commandments.md` | A fine-tuning style reference: lexical (slop vocabulary by era, copula avoidance, vague authority, promotional register), structural (negative parallelism, tacked-on -ing, significance inflation, "despite its challenges", tricolon saturation, outline wrappers, inline-header bullets, collaborative bleed, cutoff disclaimers), content (Wikipedia-style failures), formatting, style (elegant variation, conclusion signposting, fractal recapping), a checklist and era-indexed vocabulary. | Applies: 1.2 copula avoidance ("serves as" for "is"), 2.2 tacked-on -ing, 2.3 significance inflation, 2.5 tricolon threshold (one per paragraph), 5.1 elegant variation over-correction (calling the same thing different names), 2.8 collaborative bleed. Does not: Wikipedia-specific sections 3.2 to 3.4, heading and bold rules, era vocabulary (it dates fast and its own appendix says "statistical fingerprints, not absolute prohibitions"). |
| `core/voice-profile.md` | The voice resolver: finds the active voice under the data root, fails loudly on ambiguity, enforces a clean-room rule so a client's material never reaches another voice, tags output with the voice name. | Applies in spirit: nothing from another speaker's sheet may leak into this speaker (our "neighbours must differ", culture, person layers). Does not: file resolution, ghostwriting clients. |
| `core/voice-profile-template.md` | Blank fingerprint: identity, sentence length, paragraph length, rhythm, punctuation, vocabulary level, first-person use, specificity, emotional temperature, structural habits, tone axes, five confirmed voice adjectives each with evidence, "what NOT to write for this voice", stored samples that do not override the profile. | Applies: five adjectives each with one evidence sentence, and a per-voice "not this voice" list (Lift 12). Does not: platform and goals fields. |
| `core/obsidian-workspace.md` | Storage resolution, path safety, topic notes, filenames, frontmatter, safe update rules. Skimmed. | Does not (our records live in `world/sources/`). |
| `agents/openai.yaml` | Codex display name, brand colour, default prompt, implicit invocation allowed. | Does not. |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `package.json`, `.github/workflows/publish.yml`, `.gitignore`, `LICENSE` | Packaging, version drift checks, npm publish, MIT licence. | Does not. |
| `bin/check.js`, `bin/install.js`, `bin/package-claude-skill.js`, `test/install.test.js` | Package validator (frontmatter, manifest location, version drift, stale storage patterns), installer with vault setup, Claude skill zip builder, installer tests. No prose linting: all anti-AI rules are prompt text only. | Does not. Note for us: they have no mechanical gate at all; our `lint_prose` and `check` reds are stronger. |

## 1.2 Onboarding

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `onboarding/ONBOARDING.md` | Router: detects environment, asks whose voice, defines what a complete profile contains, sets onboarding tone. | Does not. |
| `onboarding/claude-code-mode.md` | Active onboarding. Analyse samples (sentence length and variance, openers, closers, register, first-person use, specificity, rhythm, temperature, what it is good and bad at) without sharing the analysis; ask goals; ask for a 200-word freewrite because it is the most unguarded signal; propose five voice adjectives and press once on "yes, all right" before accepting; fill tone axes. | Applies: the list of measurable voice markers is a good checklist for what a person sheet should pin down (Lift 12); "press once before accepting" is a cheap critic habit. Does not: asking a human for samples. |
| `onboarding/claude-ai-cowork-mode.md` | Passive onboarding that infers a voice from memory and asks gap-fill questions. | Does not. |
| `onboarding/subject-mode.md` | Ghostwriting: builds a profile for someone else, marks assumed fields `[assumed]`, records who confirmed. | Applies: mark inferred fields as inferred; our person sheets already separate recorded from invented, and the SKILL says age, family and secrets are "not recorded". |

## 1.3 Sub-skills (`skills/`)

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `skills/scene-structure/SKILL.md` | Fiction scene mechanics (read in full): scene contract (Yorke: event, change, conflict), enter late and leave early, beats as action/reaction pairs, show-don't-tell mechanics with R.U.E., one telling detail, dialogue subtext rule with examples, the "said" rule, POV discipline, pacing, forward momentum, post-generation review and checklist. | Applies: enter late and leave early (an answer starts at the fact and stops at the fact), subtext for emotional topics, R.U.E. (do not explain a feeling the line has shown), one telling detail, precision about small things when avoiding the big thing. Does not: scene entry and exit across a chapter, forward-momentum question at the end (our endings rule forbids a tidy or hook-like closer; Morrowind answers stop on the fact), POV across narration. |
| `skills/script-writing/SKILL.md` | Screenplay and video scripts (read in full): screen test, slug lines, action lines, parentheticals, visual verbs, subtext and the iceberg rule, silence as dialogue, "read every exchange aloud", scene economy and the two-scene test, three-act structure, character on screen, TV and short-form variations. | Applies: read aloud; behaviour carries the unspoken; do not write a parenthetical for a line that cannot carry its own tone ("if the sarcasm isn't on the page without the direction, rewrite the line"). Does not: formatting, page counts, act structure, camera. |
| `skills/script-writing/craft-reference.md` | Mode selector, universal script standard (reason to stay, visible change, necessary next beat, changed ending), screenplay core, character drama (values, inner contradiction, mannerisms, traits; complexity from incompatible values), dialogue section (stylised pressure; add pressure when too direct: what does the character want, what are they afraid would happen if they said it plainly, what object or silence carries it), YouTube retention material. | Applies: the three pressure questions for a speaker and the value-conflict model of complexity (Lift 14). Does not: YouTube, retention hooks, formatting. |
| `skills/audit/SKILL.md` | Rewrite-and-compare workflow: read whole, identify failures privately, mark what must survive (§10) and what is a false positive (§9), rewrite under the fabrication limit, interrogate, present BEFORE / AFTER / WHAT CHANGED / VOICE MATCH. | Applies: step 2b, decide what must survive before editing; the false-positive pass before cutting; "Every claim in the original survives into the rewrite. The shape does not have to." Does not: the presentation format. |
| `skills/failure-library/SKILL.md` | Six categories of real AI failures with quotes from real Wikipedia-style text, each with pattern, mechanism, tell, why it is broken, fix; rule "real examples only". | Applies: format (pattern, mechanism, tell, real quote, fix) matches our `tells.md` wrong-line/right-line shape; the "real examples only, no invented ones" rule is worth adopting (our trial sections already quote real draft lines). The categories themselves are encyclopaedic and do not apply. |
| `skills/outline/SKILL.md` | One-question-at-a-time interrogation by format (newsletter, sales, LinkedIn, tweets, short story, screenplay) that finds "the point" before drafting, then builds an outline. | Applies lightly: for a scene the four questions (what does the POV want, what opposes it, what changes, what is the last beat) map to a speaker's want, obstacle, what the player learns, last fact. Does not: the other formats. |
| `skills/voice/SKILL.md` | Voice management commands: list, switch, create, import, recalibrate, delete, repair, plus fabrication discipline. Skimmed. | Does not. |
| `skills/workspace/SKILL.md` | Vault connect, disconnect, migrate, topic management with hard stops. Skimmed. | Does not. |
| `skills/world-builder/SKILL.md` | World-building process: questioning, bible skeleton, file output, fast capture, draft cartography. Principles: the world must serve the story (conflict, character, stakes, specificity), rule-to-consequence test, the minimum viable bible, record decisions when made. | Applies: "world-building that exists only to be admired is a procrastination strategy" backs our rule that a placed thing answers "why here?" and that colour comes from what the speaker sees and does. Does not: the process (our lore dossiers and records are the bible). |
| `skills/world-builder/questioner.md` | Five-level question sequence (concept, protagonist, conflict, rules, society); one question at a time; flag contradictions at once; "I don't know yet" becomes an open question, not a forced decision. | Does not as a process. One rule applies: "I don't know yet" is recorded as open, not invented (matches our no-invention rule). |
| `skills/world-builder/skeleton-template.md` | World bible template: premise, protagonist, antagonist, stakes, structure, rules, society, history. | Does not. |
| `skills/world-builder/manuscript-ingest.md` | Reverse-maps a draft into entities, relationships, continuity facts, conflicts and gaps, citing where each fact came from and separating confirmed facts from inference. | Applies as a method for the corpus read: extract what each answer asserts (place, price, road, person) and check it against records. Our grounding gate (`corpus.grounded`) already does this mechanically. |
| `skills/world-builder/obsidian-output.md` | Obsidian graph notes with a recoverable multi-note transaction protocol. | Does not. |
| `skills/newsletter-creative/SKILL.md`, `skills/newsletter-creative/scripted-essay-reference.md` | Story-led newsletter: hero's journey backbone, hook architecture, narrative mechanics, payoff contract; scripted essay reference (spoken cadence, rehooks). | Does not. Spoken cadence is the only thing near dialogue and is covered better by the script skill. |
| `skills/newsletter-technical/SKILL.md` | Technical newsletter: structural contract, clarity rules, scannability, insight standard. | Does not. |
| `skills/linkedin/SKILL.md`, `skills/tweets/SKILL.md`, `skills/substack-notes/SKILL.md` | Platform formats: hooks, post structure, thread architecture, compression, discovery. | Does not. |
| `skills/web-copy/SKILL.md`, `skills/sales-copy/SKILL.md` | Page hierarchy, headlines, CTAs, objections, proof, email sequences. | Does not. |

## 1.4 Cowork port (`cowork/`) and resources

`cowork/` repeats the skills as self-contained files for Claude.ai Projects, with the same rules
copied by hand (CLAUDE.md says so). Each is judged by the skill it copies.

| File | Copy of | Verdict |
| --- | --- | --- |
| `cowork/README.md` | Upload guide | Does not. |
| `cowork/ew-master.md` | `SKILL.md` + `core/*` in one 1,537-line file | Same as the files it merges. |
| `cowork/ew-scene-structure.md`, `cowork/ew-script-writing.md`, `cowork/ew-audit.md`, `cowork/ew-failure-library.md`, `cowork/ew-world-builder.md`, `cowork/ew-outline.md`, `cowork/ew-voice.md` | the matching `skills/*` | Same verdicts as their originals. |
| `cowork/ew-newsletter-creative.md`, `cowork/ew-newsletter-technical.md`, `cowork/ew-linkedin.md`, `cowork/ew-tweets.md`, `cowork/ew-substack-notes.md`, `cowork/ew-web-copy.md`, `cowork/ew-sales-copy.md` | the matching platform skills | Does not. |
| `resources/Everyday Writer — Anti-AI Rules Rundown.md` | Human-readable bad/good pairs for the §1 to §5 rules | Applies: same content as `core/anti-ai-rules.md`; nothing new. |
| `resources/General Writing Commandments_ The Foundation of Clarity.md` | King/Lamott/Brande directives: active voice, adverb elimination, first word that fits, shitty first draft, R.U.E., show don't tell, revision minus 10 percent | Applies: R.U.E. with the dialogue pair "'I hate you,' he said angrily" vs "He slammed his fist onto the table. 'I hate you.'". Does not: schedule and drawer-time directives. |
| `resources/General Writing Directives_ The Laws of Construction.md` | Yorke/Truby/Bernhardt structure: R.U.E., cradle-to-grave history, causality (therefore/but), fractal structure, seven steps, four-corner opposition, inciting incident timing, sales-as-journey | Does not for dialogue. The "cradle to grave history" is the opposite of our rule that unrecorded backstory is never invented. |
| `resources/README.md`, `references/DROP-MD-FILES-HERE.md`, `docs/distribution.md`, `docs/superpowers/specs/2026-08-06-multi-voice-design.md`, `docs/superpowers/specs/2026-09-20-obsidian-second-brain-design.md` | Housekeeping and design history (multi-voice, vault storage) | Does not. The multi-voice spec's contamination argument (a client's brand file reaching the writer's own work) is the same reason each speaker's packet must carry only that speaker's world. |

---

# Part 2: creative-writing-skills (haowjy/creative-writing-skills, 0.5.14, Apache 2.0)

`skills/` is the Mars source; `cw/skills/` is a genericised copy with Meridian references removed
(AGENTS.md says CI fails on drift). Each `cw/` file below is judged as the same file as its `skills/`
twin unless listed under 2.6 as cw-only.

## 2.1 Writing-principles (the diagnostic layer) and llm-writing

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `skills/writing-principles/SKILL.md` (and `cw/`) | Read in full. Trust the reader (readers reconstruct emotion, infer motive, hold tension; the model's helpfulness instinct pulls the other way). Economy: every element does more than one thing. Five reader reward channels: transportation, aesthetic, social simulation, flow, curiosity/prediction. Punctuation tells (em dashes read as AI). | Applies strongly: reward channels give a vocabulary for panel lenses; "dialogue that only informs" is flat; transportation needs the speaker to know only what they have lived. Caution: trusting the reader has a limit in our game, because the owner's round 1 complaint is that the player had no context, so "leave space" never applies to what a thing is. |
| `skills/writing-principles/resources/failure-modes.md` (and `cw/`) | Read in full. Nine patterns, each with what happens, the fix and why the instinct fires: over-elaborating scope, flattening voice, info-dumping, labelling emotions (and the stock-tells trap), resolving tension prematurely, homogenising character simulations, emotional commentary, collapsing ambiguity, over-intensifying language, mismatching project style. Rule: the antidote is calibration, never "do the opposite". | Applies: homogenising (Lift 3), over-elaborating (Lift 9), stock tells (Lift 10), over-intensifying (Lift 11), mismatching project style (Lift 8), collapsing ambiguity (Lift 13). Info-dumping applies only partly (see Lift 5). |
| `skills/writing-principles/resources/citations.md` (and `cw/`) | Research behind the model: transportation, reading flow, curiosity, social cognition (including a failed replication, stated), syntactic templates, diversity collapse, attractor states, role-decomposition for screenwriting, persona-prompting interference; craft canon (Hemingway, Forster, Gardner, Baxter, Wood, Le Guin, Saunders). | Applies as evidence: Shaib et al. 2024 (sentence structures copied from pretraining survive alignment) and "Price of Format" (prompt-side "be creative" does not close the gap) explain why a stronger instruction does not fix the owner's "pithy" fault and why a structural check does. Caution: the PRISM result is about discriminative tasks, not generation, so it is no ground to drop persona framing. |
| `cw/skills/llm-writing/SKILL.md` | Scope, ground, draft, revise (whole artifact then inward, then zoom out again); a delete list: filler sections, labels without mechanism, hidden uncertainty, qualifier softening, conditions on instructions, restatement, transition words, "It's not X, it's Y", conversational bleed. | Applies: revise from large to small and back; "conversational bleed" (terms coined in the conversation, "the old version") is exactly how a writer leaks packet jargon into a speaker's mouth. Does not: the instruction-writing parts. |

## 2.2 Creative-writing craft, modes and genre

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `skills/creative-writing-craft/SKILL.md` (and `cw/`) | Index of craft resources, loaded one at a time. | Applies: load only the resource needed. |
| `skills/creative-writing-craft/resources/prose-writing.md` (and `cw/`) | Psychic distance, free indirect discourse, sentence rhythm, sensory grounding, interiority, show through action, POV. | Applies a little: what a character notices reveals who they are (a chef notices smells, a soldier exits) is the same as our "favourite subject is where a talker wanders". Free indirect discourse and POV do not apply to topic answers. |
| `skills/creative-writing-craft/resources/scene-construction.md` (and `cw/`) | Scene entry in the middle of action, dialogue (two jobs at once, subtext, voice differentiation by vocabulary, structure and what they talk about, action beats over tags), pacing, transitions. | Applies: voice differentiation test "identify the speaker without tags", two jobs per line. Does not: tags and beats (our answers are bare topic text), pacing across a chapter. |
| `skills/creative-writing-craft/resources/style-analysis.md` (and `cw/`) | Analyse prose into style files by dimension; split files where a caller would want one part without the other; principle plus one or two examples plus pointers, never a catalogue; patterns (reproduce) versus problems (tics to log); voice test and brevity test. | Applies: Lift 16 and 17. Our `style.md` (22 KB) and `tells.md` (25 KB) fail its brevity test by a wide margin. |
| `skills/creative-writing-craft/resources/genre/fantasy.md` (and `cw/`) | Protect world detail that changes choice, cost or danger; common failures: lore front-loaded, magic as a clean system, invented terms without orientation, everywhere "generically ancient". | Applies: "terminology introduced through use before explanation" is wrong for us (the player is a stranger and must be told what a thing is), but "make every place sound generically ancient" is a fault our register-vocabulary bans already catch. |
| `skills/creative-writing-craft/resources/genre/horror.md`, `litfic.md`, `mystery.md`, `romance.md`, `thriller.md` (and `cw/`) | One-page genre addenda: protect, common LLM failure modes, what to check in revision. | Mostly does not. Mystery's "clues that glow with importance" and "over-explaining deductions" is a tell for quest-hint NPCs; romance's "polishing voices until both characters sound emotionally fluent and identical" repeats failure-modes. |
| `skills/creative-writing-modes/SKILL.md`, `resources/prose-modes.md` (and `cw/`) | Five production modes (fresh draft, revision, bridge, alternate take, line polish), each with what to read first. Revision is from synthesised critique, smallest surface that fixes the failed reader simulation, note declined findings. Alternate take must change a real variable and say what it proves. Line polish only after structure settles and not "polish away the point". | Applies: Lifts 18 and 19. |

## 2.3 Agents (`agents/`, `cw/agents/`)

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `agents/writer.md` | Production prose from brief, critique notes, adjacent scenes, style, character state, canon. "Use llm-writing to catch unchosen defaults, not to flatten the prose into tidy explanation. Ambiguity, silence, repetition, compression, or fragmentation are valid when they create the intended reader effect." Notes mode, judgement calls and contradictions with character state; never updates character state. | Applies: Lift 18; the report contract (mode used, judgement calls, contradictions with the record) is useful in a writer's result. |
| `agents/critic.md` | One focus area at a time; each finding: what is wrong, why it matters to the reader, what to do instead, severity, tied to a quoted passage so the synthesiser need not re-read. | Applies: Lift 20. |
| `agents/editor.md` | Third-party editor: first read for felt experience, second to diagnose; large to small; protect the author's voice; query rather than dictate; anchor every note; lead with the overall diagnosis; order by reader cost. | Applies partly: the "query, don't dictate" and "distinguish voice from error" habit suits a reviewer who must not flatten a rambling speaker. |
| `agents/reader-sim.md`, `cw/skills/reader-sim/SKILL.md`, `skills/reader-sim/SKILL.md` | Read as a stated persona with a knowledge boundary, report the felt experience moment by moment through the five reward channels, no craft diagnosis, anchor to the text. If no persona is given, state the one assumed. | Applies: this is our voice-reader panel. Lift 21. |
| `agents/character-sim.md`, `agents/character-sim.author-variant`, `skills/character-sim/SKILL.md` (and `cw/`) | Speak as the character from their knowledge, voice and state; when no files exist work from a sketch and say the assumptions; under pressure people stall, redirect, defend, shut down, over-explain, joke, attack and rarely name their inner state; let conversations be messy. The author variant adds: "voice without state produces generic performance; state without voice produces the right thoughts in the wrong mouth." | Applies: Lifts 1, 2 and 4. |
| `agents/continuity-checker.md` | Cross-reference against canon: timeline, character state, geography, facts, decisions, vocabulary; report contradictions with evidence and no fixes; consistency errors cluster in the middle of long content. | Applies: our grounding gate covers this mechanically; "don't speculate about intent or suggest fixes" is the right shape for a checker. The "middle clusters" finding suggests reading the middle answers of a long speaker first. |
| `agents/muse.md` | Author-facing orchestrator: preserve intent, delegate by stance, read drafts yourself, synthesise conflicts, do not forward raw reports, do not let provisional brainstorms harden into canon. | Applies: "keeping stances in separate spawns prevents critique from contaminating drafting"; matches our planner and writer split. |
| `agents/brainstormer.md`, `agents/outliner.md`, `agents/style-creator.md`, `agents/web-researcher.md` | Option generation, outlines, style-file creation, web research for fiction. | Does not (we do not brainstorm or outline dialogue; research goes through lore dossiers). |
| `cw/agents/*.md` (11 files, same names as above) | Shortened genericised copies of the same agents. | Same verdicts as their originals. |

## 2.4 Story review (`skills/story-review/`, `cw/skills/story-review/`)

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `SKILL.md` | Edit levels (editorial review, developmental, line, copy, proofreading), big before small. | Applies: order of passes. |
| `resources/prose-critique.md` | Adversarial reading: find what does not work; good findings are specific, reasoned, directable, non-obvious; time-wasters (vague "could be stronger", restating, praise, attacking settled premise); severity; calibrate to stage; report shape. | Applies: Lift 20. |
| `resources/prose-critique/voice.md` | Dialogue (two jobs, subtext, on-the-nose, "As you know, Bob", voice distinction by vocabulary, structure, verbal habits, register), tags and beats, POV, voice drift (read first and last page against each other). | Applies: Lifts 3, 5, 22. |
| `resources/prose-critique/character.md` | Motivation, arc, agency, relationships, voice distinction ("some deflect, some lecture, some barely speak; the variation is the characterization"). | Applies (voice distinction only). |
| `resources/prose-critique/prose.md` | Rhythm, clarity, word choice (repetition, filter words), show vs tell, AI prose patterns (emotional choreography, placeholder prose, metaphor clusters, summary endings, emotional inflation), and three documented failure modes to hunt (syntactic templating, stock physical tells, attractor-state fluency). | Applies: Lifts 7, 10, 23. |
| `resources/prose-critique/antipatterns.md` | AI antipatterns graded by evidence: research-backed (lower lexical variability, fewer personal pronouns, more positive emotion, shallow interiority, low dialogue subtext), community-identified structural patterns, and "Not reliable: word-level slop lists". | Applies: Lift 7. |
| `resources/prose-critique/baseline.md` and `analyze.py` | Measure sentence length, openers, dialogue ratio, repetition and pronouns against the project's own approved chapters; metrics are triggers, not verdicts. | Applies: Lift 24. |
| `resources/prose-critique/structure.md`, `continuity.md` | Plot logic, pacing, scene necessity, stakes, setup/payoff; timeline, geography, character state, report format. | Does not for structure (no plot in a topic answer). Continuity maps to the grounding gate. |
| `resources/editorial-review.md`, `developmental-edit.md`, `line-edit.md`, `copyedit.md`, `proofreading.md` | Level-specific methods. Line edit: name patterns not every instance; redundancy ("the text does the work, then a sentence explains what the work accomplished") is the most common AI line-level failure. Copyedit: style sheet, fix silently only if unambiguous, query otherwise. Proofreading: AI-specific errors (duplicated phrases after insertion, orphaned references, tense shifts at revision boundaries). | Applies: line-edit redundancy test (Lift 25) and the proofreading list (orphaned references after a fact is moved is a real risk in our fact-fitting pass). Developmental and editorial levels do not. |
| `resources/reader-sim-signal.md` | Use reader-sim as experience evidence, not a fix list; preserve the persona; trust the felt experience over the reader's explanation; convergence between reader and critic is high confidence; map signal to reward channels; watch the middle. | Applies: Lift 21. |

## 2.5 Planning, memory, staffing and research

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `skills/story-planning/SKILL.md`, `resources/creative-direction.md`, `resources/brainstorming.md`, `resources/story-architecture.md` (and `cw/`) | Direction, minimal capture, source tags, arc and scene structure. | Does not. The capture rule ("record what was stated; do not fill gaps the author left open") agrees with our no-invention rule. |
| `skills/story-planning/resources/brainstorming/chapter-planning.md`, `character-development.md`, `continuity-timeline.md`, `worldbuilding.md` | Capture guides: do not upgrade vague input into structure or a psychological profile ("the psychology trap"); show contradictions side by side and never auto-resolve. | Applies: the psychology trap is the same fault as inventing a speaker's grievance or history. Rest does not. |
| `skills/story-planning/resources/story-architecture/arc-design.md`, `chapter-and-scene.md`, `structural-problems.md` | Arc, chapter, scene design; common structural faults. | Does not. |
| `skills/story-memory/SKILL.md`, `resources/story-context.md`, `fact-extraction.md`, `story-reference-writing.md`, `story-reference-writing/reference-modes.md`, `writing-artifacts.md`, `writing-issues.md` (and `cw/`) | Context handoffs (what a writer needs: brief, style, character state, 2 to 4 continuity files, vocab), fact extraction, reference writing, artifact layout, issue log. `writing-issues.md`: one finding is a critique note; a pattern across chapters is a logged issue with evidence, scope, severity; check duplicates before logging. | Applies: `story-context.md` matches our packet design (tight scope, "tell the writer where to find more"); `writing-issues.md` is Lift 17. The rest is knowledge-base plumbing we already have in `docs/` and `world/sources/`. |
| `skills/creative-research/SKILL.md` (and `cw/`) | Source types and reliability grading for fiction research. | Does not (lore comes from dossiers and UESP under the era policy). |
| `skills/creative-writing-muse/SKILL.md` (and `cw/`) | Single-agent muse: self-prompt before each stance (intent, reader effect, constraints, what stays ambiguous, output, "what would be the wrong kind of success?"), keep stances separate. | Applies: the "wrong kind of success" question (Lift 26). |
| `skills/writing-staffing/SKILL.md` (and `cw/`) | Which skills and files each agent gets; one writer per scene; 1 to 2 critics for low stakes, 3 for standard, 4 to 5 for pivotal with duplicated coverage of the critical dimension; fan-out the same question to different model families only for disputed high-stakes calls; reader-sim after the write/critique loop converges. | Applies: scale critics to stakes; one writer per person (voice degrades when several handle adjacent content). Model names (`sol`, `terra`) do not. |

## 2.6 cw-only skills (`cw/skills/`)

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `grill-with-docs/SKILL.md` | Interviews the author against documented decisions; one branch at a time with a recommended answer; challenges terminology against vocab. | Does not (our owner interaction is plain-English check-ins, 0083). |
| `shared-dao/SKILL.md` | One name per concept, one concept per name; resolve terms early; vocab at the lowest shared scope. | Applies: the owner's "claim", "count", "tally" fault is word overuse, and one-term-per-concept is the opposite pressure from elegant variation; our `style.wordCap` handles the first. |
| `intent-modeling/SKILL.md` | Separate what was said from what was meant; "a correction names one instance; the mistake is usually a class; find the other instances". | Applies: the round 1 feedback is a class correction, not eight line edits. |
| `information-hierarchy/SKILL.md`, `structured-artifact/SKILL.md`, `structured-artifact/resources/delivery.md`, `diagrams.md`, `images-and-mockups.md`, `react-flow.md`, `md-validation/SKILL.md`, `md-validation/resources/mermaid-authoring.md` | Answer-first reports, HTML artifacts, diagrams, mermaid, link checks. Skimmed. | Does not. |
| `kb-management/SKILL.md`, `knowledge-layers/SKILL.md`, `knowledge-layers/resources/bootstrap.md`, `code.md`, `corrections/code.md`, `corrections/register.md`, `qi-layer/SKILL.md`, `qi-layer/resources/references.md`, `project-setup/SKILL.md`, `reflect/SKILL.md`, `zoom-out/SKILL.md` | Knowledge layers, AGENTS.md craft, corrections register (record each human correction by class, with an "enforced by" column, strongest first), project setup, orientation. Skimmed. | Mostly does not. The corrections register is the same idea as our rulings index plus "fix in the tool first" (CLAUDE.md "Current recipe"), which we already hold. |

## 2.7 Repo-level files

| File | What it does | Dialogue verdict |
| --- | --- | --- |
| `README.md`, `AGENTS.md`, `docs/architecture.md` | Overview, install, agent table; repo conventions (`skills/` vs `cw/skills/`, sync rule); the thesis "a strong muse, a few clean cognitive roles, durable story context, intentional prose methodology". README "Current Experiments": rhetorical questions in prompts, unproven. | Applies: few roles, clean stances. The rhetorical-question experiment is untested by their own admission. |
| `docs/research/README.md`, `book-editor-research.md`, `craft-how-to-write-structure.md`, `reader-interest-second-pass.md` | Durable research notes: editing levels, craft sources, reader interest. `craft-how-to-write-structure.md` item: "Write for reader participation, not reader rescue". | Applies as evidence for Lifts 4 and 13; "Explanation fixes all confusion" is listed as a misconception. |
| `docs/writing-workflow.html` | Rendered workflow diagram page. Not read in detail. | Does not. |
| `drafts/engineering-creative-writing.md` | The maintainer's blog-post draft: the thesis is "keeping the model's mind clear". | Does not. |
| `bootstrap/project-setup/BOOTSTRAP.md`, `.claude/commands/README.md`, `bs.md`, `critique.md`, `kb.md`, `write.md` | Setup interview and four slash commands (brainstorm, critique, kb, write). | Does not. |
| `CHANGELOG.md`, `mars.toml`, `meridian.toml`, `.claude-plugin/marketplace.json`, `cw/.claude-plugin/plugin.json`, `.claude/settings.json`, `.claude/hooks/*`, `.codex/hooks.json`, `.codex/hooks/deny-interactive-prompts/*`, `.githooks/pre-commit`, `scripts/create_skill_zips.py`, `scripts/sync_cw_skills.py`, `scripts/release.sh`, `LICENSE`, `.gitignore` | Packaging, sync, hooks and release. | Does not. |

---

## What does not apply, in one place

- Platform copy, headlines, calls to action, sales structure, newsletters, threads (all EveryDay-Writer
  platform skills): the player is not a reader being persuaded.
- Voice onboarding from a human's samples and ghostwriting clients: our voices are authored from
  records and Morrowind exemplars.
- Plot, arcs, acts, scene necessity, chapter endings, forward-momentum questions: a topic answer has no
  plot, and our endings rule wants the answer to stop on the fact.
- "Cradle to grave" histories and psychology: forbidden here; unrecorded backstory is never invented.
- "Trust the reader / leave space": limited. The owner's rule is that a helpful speaker says what the
  thing is, in plain words, to a stranger. Subtext suits grief, grudges and refusals, never what a
  place, price or road is.
- Their word lists: only taste (their own antipatterns file says so). Ours are tuned to Argonia and
  gated by `lint_prose`.
- Their operating-standard rhetoric ("A-Players"), curly-quote and hyphenation tells, Wikipedia
  boilerplate, heading and bullet rules: no headings or bullets in dialogue.

## Where their rules clash with ours (do not import)

| Their rule | Ours | Ruling |
| --- | --- | --- |
| EveryDay-Writer: 2 to 3 em dashes per piece is fine | No em dashes ([style-core](../../standards/text/style-core.md) §1) | Ours. |
| EveryDay-Writer: straight double quotes | Single quotes inside a line | Ours. |
| EveryDay-Writer §5: drop the hyphen in predicative compounds ("cross functional") | Not addressed; British house grammar | Do not import; no speaker needs it. |
| creative-writing-skills: "said" is invisible, use action beats | Topic answers carry no tags | Does not apply. |
| creative-writing-skills fantasy: introduce terms through use before explaining | Owner: tell the stranger what the thing is, plainly | Ours. |
| EveryDay-Writer: voice profile and sample outrank style rules | Our hard gates outrank a person's habit | Take only the principle below (Lift 8): a person sheet may choose formality; it may not break a hard ban. |

---

# Lift list

Each rule is an imperative for the NPC-dialogue writer. "Check" says where it would live or what
would enforce it, for the planner to decide; nothing here changes a gate by itself.

1. **Write from what the speaker has lived, not from what the packet holds.** The packet knows the
   whole world; the speaker knows their day, their trade and their neighbours. Before each answer ask
   what this person would never have seen, and leave that out. Use what they avoid, as well as what
   they say, to show where they stand.
   Credit: from creative-writing-skills/agents/character-sim.author-variant ("Speak from the character's knowledge, not the story's"); creative-writing-skills/skills/writing-principles/SKILL.md (Transportation).

2. **Load voice and state together, never one without the other.** A voice sheet without the person's
   current situation gives a generic performance; the situation without the voice gives right thoughts
   in the wrong mouth. Read the person's sheet and their day before any fact.
   Credit: from creative-writing-skills/agents/character-sim.author-variant.

3. **Do not make everyone fluent.** Let some people fragment, deflect, over-explain, stay blunt or
   stay short. Voice variety is the characterisation: if two speakers could swap lines, rewrite one by
   changing how it is said (length, what they open with, what they leave unsaid), not just the topic.
   Keep the helpfulness rule: variety lives in manner and extra detail, not in withholding what a
   thing is.
   Credit: from creative-writing-skills/skills/writing-principles/resources/failure-modes.md ("Homogenizing character simulations"); creative-writing-skills/skills/story-review/resources/prose-critique/voice.md.

4. **Under emotional pressure, let the speaker dodge; under no pressure, let them say it.** A grudge,
   grief or refusal is shown by stalling, changing the subject, answering a smaller question, or a
   flat "Fine." Never have a speaker name their own emotional state cleanly. But a plain question
   about the world gets a plain answer.
   Credit: from creative-writing-skills/skills/character-sim/SKILL.md; creative-writing-skills/skills/story-review/resources/prose-critique/voice.md ("on the nose"); EveryDay-Writer/skills/scene-structure/SKILL.md (Dialogue, subtext rule).

5. **Test every line with a cold stranger.** Read the answer as someone who knows nothing the line
   assumes: is every noun something the player has met, or been told in this answer? A line that
   refers to the speaker's own job, goods or standing as if known fails. Delete the clause or say what
   it is. (Their "As you know, Bob" rule is the reverse fault: two insiders explaining to each other.
   Ours is an insider explaining nothing to an outsider.)
   Credit: from creative-writing-skills/skills/story-review/resources/prose-critique/voice.md ("As You Know, Bob", inverted); creative-writing-skills/skills/reader-sim/SKILL.md (knowledge boundary).

6. **Judge tells by cluster, not instance, and protect what a person would really say.** One
   contraction, one short sentence, one "however" is English. Flag a line only when several tells
   stack, and never flatten a specific odd detail, an uneven rhythm, a self-correction or a speaker's
   own habit to satisfy a rule. If a draft has no specific, odd, hard-to-invent detail, add one from
   the record; do not delete another phrase.
   Credit: from EveryDay-Writer/core/anti-ai-rules.md (§9 What not to flag, §10 Signs of human writing).

7. **Treat banned-word lists as house taste, and hunt the structural tells that are evidence.** Do not
   claim a word proves machine writing. Hunt instead: dialogue with no subtext, emotion resolved
   inside the same answer, a tidy summary ending, the same sentence skeleton across answers, an
   upbeat skew, thoughts that are always complete and ordered.
   Credit: from creative-writing-skills/skills/story-review/resources/prose-critique/antipatterns.md ("Not Reliable: Word-Level Slop Lists", research-backed signals); creative-writing-skills/skills/story-review/resources/prose-critique/prose.md (Documented AI Failure Modes).

8. **Let the person's sheet decide formality, within the hard bans.** "Does not" against "doesn't",
   "I am" against "I'm" is a property of the speaker (role, age, mood, culture), not a house default.
   Default an ordinary chatty speaker to the contracted form; give a formal one the long form because
   the sheet says so. Match the settled corpus and sheet before your own taste; consistency across
   the place beats any one line's polish.
   Credit: from EveryDay-Writer/core/anti-ai-rules.md (§0.1 Precedence: "Matching the writer beats scrubbing the tell"); creative-writing-skills/skills/writing-principles/resources/failure-modes.md ("Mismatching project style").

9. **Write the brief and stop.** If the topic asks what the Hist is, answer that, with one thing of
   the speaker's own. Do not add the aftermath, the reflection, the neighbour's view or the
   closing line because more felt safer. When an answer packs several facts into one pithy sentence,
   split it into the plain sentences a person would say.
   Credit: from creative-writing-skills/skills/writing-principles/resources/failure-modes.md ("Over-elaborating scope"); EveryDay-Writer/skills/scene-structure/SKILL.md (Enter late. Leave early).

10. **Do not announce feeling, and do not swap in a stock gesture.** A speaker does not say they are
    angry or proud; they also do not "sigh", "shrug" or "clench" on cue. Show it by what they pick
    to talk about, what they refuse, or one specific habit only this person would have. Never
    follow a showing line with a line that explains it (R.U.E.).
    Credit: from EveryDay-Writer/skills/scene-structure/SKILL.md (R.U.E.); creative-writing-skills/skills/writing-principles/resources/failure-modes.md ("Labeling emotions", "The stock-tells trap").

11. **Understate. Plain words land harder at the point that matters.** "I miss him" beats a line
    about the weight of absence. Keep intensity low in ordinary talk so the one heavy answer can be
    heard; a conversation about prices carries the weight of a conversation about prices.
    Credit: from creative-writing-skills/skills/writing-principles/resources/failure-modes.md ("Over-intensifying language"); creative-writing-skills/skills/story-review/resources/prose-critique/prose.md ("Emotional inflation").

12. **Give each person a five-word voice with proof, and a "not this voice" list.** Name five
    adjectives for how they sound, each backed by one sentence of evidence from their own lines, and
    list two or three patterns that would sound like someone else (for example the neighbour's opener).
    Check the list against the finished answers.
    Credit: from EveryDay-Writer/core/voice-profile-template.md (Voice adjectives, What NOT to write for this voice); EveryDay-Writer/onboarding/claude-code-mode.md (Step 5).

13. **Leave open what the record leaves open.** Do not settle a rumour, motive or dispute the pool
    leaves undecided; do not give a verdict on the people in it. Write lines consistent with each
    reading. Where the lore is missing, write nothing about it and report the gap (or, in a draft for
    the planner, mark it `[need: what the pool lacks]`) rather than invent.
    Credit: from creative-writing-skills/skills/writing-principles/resources/failure-modes.md ("Collapsing ambiguity"); EveryDay-Writer/core/anti-ai-rules.md (§0.2 Fabrication rule, bracket marking).

14. **Before drafting an answer, state the speaker's want and fear for this exchange in one line each.**
    What do they want from the stranger (to be rid of them, a sale, company)? What would they not say
    plainly, and what do they say instead? One line each, kept in the working notes, not the output.
    Credit: from EveryDay-Writer/skills/script-writing/craft-reference.md (Dialogue: "What does the character want from this exchange?").

15. **Cap and log the recurring word.** When a word or construction recurs across one place's answers
    (`claim`, `count`, `tally`, `keep`), log it as a tic with counts and the places it appears, check
    the next place against the log, and do not replace it with a near synonym that becomes the next
    tic. A repeated name for one thing is allowed: use the same word for the same thing, not elegant
    variants.
    Credit: from creative-writing-skills/skills/story-memory/resources/writing-issues.md (recurring tics are issues with evidence, scope, severity); EveryDay-Writer/core/ai_slop_commandments.md (§5.1 Elegant variation over-correction).

16. **Read each answer aloud before freezing it.** If it cannot be said at speed without stumbling, or
    the stress falls on the wrong word, it is not right. Rhythm, interruption and an unfinished thought
    are allowed; a sentence that needs two readings to parse is not.
    Credit: from EveryDay-Writer/skills/script-writing/SKILL.md (Rhythm in dialogue, pre-draft checklist); EveryDay-Writer/skills/script-writing/craft-reference.md (Dialogue).

17. **Keep the instructions a writer carries short enough to hold in one read.** A style file teaches
    by one principle plus one or two examples plus a pointer, not a catalogue; if the writer has to
    keep it open while drafting, it is over-prescribed. Split by what a caller would want separately
    (a culture, a register, the person) and test with a fresh writer: could they, from this file and a
    brief, produce prose the owner recognises?
    Credit: from creative-writing-skills/skills/creative-writing-craft/resources/style-analysis.md (File Splitting, Quality Tests).

18. **Use the tell checks to catch unchosen defaults, not to flatten the speaker.** A repeated phrase,
    a fragment or a rambling turn is valid if the person sheet calls for it; cut it only when it is
    the writer's default showing. At polish, do not remove the rough edge that is the voice. Write
    the whole answer before judging lines.
    Credit: from creative-writing-skills/agents/writer.md; creative-writing-skills/skills/creative-writing-modes/resources/prose-modes.md (Fresh draft, Line polish).

19. **Revise from a synthesised critique, change the smallest thing that cures it, and say which
    findings you declined.** Name which reader failed (the stranger could not follow; the person sounds
    like a neighbour) and touch only that. If the fault is manner, change manner; do not rewrite facts.
    For a pivotal person, write a second take that changes one named variable (opening move, length,
    stance) and say what each take proves.
    Credit: from creative-writing-skills/skills/creative-writing-modes/resources/prose-modes.md (Revision, Alternate Take).

20. **Make every critic finding specific, reasoned and directable, and drop praise.** Each finding:
    the quoted line, what it costs the stranger, what to do, severity. One focus per critic. Critique
    the execution, never the settled premise (the stance, the record, the pool). The planner reads the
    findings without re-reading the answers.
    Credit: from creative-writing-skills/agents/critic.md; creative-writing-skills/skills/story-review/resources/prose-critique.md (What Makes a Good Finding).

21. **Trust the reader's felt report for where and what, and the critic for why.** A panel reader who
    says "I lost track here" is right about the place even if the diagnosis is wrong. Treat a place
    flagged by both a reader and a critic as high confidence, and one that only a reader flags as a
    real finding. State each reader's persona and knowledge boundary (a stranger to the province).
    Credit: from creative-writing-skills/skills/story-review/resources/reader-sim-signal.md; creative-writing-skills/skills/reader-sim/SKILL.md.

22. **Check voice drift by reading a speaker's first and last answers against each other.** Any
    single answer can look fine; the shift in register, vocabulary, length or manner shows only across
    the set. Do the same across a place: if every neighbour's first answer opens the same way, they
    are one voice.
    Credit: from creative-writing-skills/skills/story-review/resources/prose-critique/voice.md (Voice Drift).

23. **Name a repeated sentence skeleton as its own finding.** When answers share a shape (clause order,
    modifier placement, length) while the content changes, report the shape and give the pattern, not
    a list of phrases. If emotional peaks and mundane answers have the same measured finish, the
    finish is the fault.
    Credit: from creative-writing-skills/skills/story-review/resources/prose-critique/prose.md ("Syntactic templating", "Attractor-state fluency").

24. **Measure against the settled baseline, and treat each number as a prompt to look.** Compare an
    answer set's sentence-length spread, opener variety, pronoun use and repetition with the approved
    corpus for that culture, within one register class, never across. A number outside the range asks
    for a look; it does not decide quality.
    Credit: from creative-writing-skills/skills/story-review/resources/prose-critique/baseline.md; creative-writing-skills/skills/story-review/resources/prose-critique/analyze.py.

25. **After a line shows something, delete the line that explains it.** The commonest line-level fault
    is the text doing the work and then a sentence saying what the work achieved. Find it by asking of
    every second sentence: did the first already say this?
    Credit: from creative-writing-skills/skills/story-review/resources/line-edit.md (Redundancy); EveryDay-Writer/core/anti-ai-rules.md (§6 R.U.E.).

26. **Name the wrong kind of success before drafting.** In one line, say what a technically clean but
    useless answer would look like for this topic and this person (tidy, pithy, a small essay with a
    closing line), then check the draft is not that.
    Credit: from creative-writing-skills/skills/creative-writing-muse/SKILL.md (Self-Prompt Before Each Stance).

27. **After the draft, privately answer three questions, then revise.** (a) Which exact line would a
    player point at as machine or odd? (b) Does any line state a place, price, road, name or number
    not in the packet? (c) Which is the weakest line, and is it the one the answer rests on? Revise
    from the answers; do not paste them into the result.
    Credit: from EveryDay-Writer/core/anti-ai-rules.md (§7.1 Never present a first draft, the three interrogation questions).

28. **Proof the seams after a revision.** Fact-fitting moves facts; check for a duplicated sentence
    left where a line was inserted, a pronoun or "the" pointing at a fact that was cut, and a tense or
    register shift at the join.
    Credit: from creative-writing-skills/skills/story-review/resources/proofreading.md (Common AI-Specific Proofing Errors).

---

## Recommendations

1. Add Lifts 5, 8, 9 and 15 to `.claude/skills/dialogue-write/references/tells.md` first: they answer
   the owner's round 1 bullets directly (no context for the player, "does not", pithy, "claim/count/tally").
   Evidence: feedback-round1-samples.md; none of the four appear in `tells.md` or `style.md`
   (grep for "cold stranger", contraction-by-sheet, "write the brief" found nothing).
2. Apply Lift 17 to the skill itself: `style.md` is 22.5 KB and `tells.md` 25.3 KB, against a source
   that holds "if they need to keep it open as reference while drafting, it's over-prescribed". Measure
   with a fresh writer who has only the packet before adding anything.
3. Add Lifts 6 and 7 and both repos to `docs/research/text-and-voice/ai-writing-tells.md` (Sources
   and a "caveat" paragraph). Its existing line "no single tell proves anything" agrees; the cluster
   rule is the actionable addition.
4. Lift 24 is the only mechanical item: the repo's `analyze.py` computes sentence-length spread,
   opener variety, dialogue ratio, repetition and pronoun counts against a project baseline. We
   already hold the Morrowind corpus profile (`morrowind-dialogue-corpus.md`), so a per-culture
   baseline is cheap to add to `dialogue_gates`; do not copy their script (read-only, untrusted).
5. Log the round 1 owner words as rows in `dialogue-rulings-index.md` (contraction by speaker,
   "claim", "the count", "the tally", cold-stranger context, pithiness).
6. Nothing here is lore, so no dossier or UESP lookup was needed; the era policy is untouched.

Covered: every file in both clones (git metadata excluded): all skill, reference, agent, prompt, command,
spec, research and packaging files, by name in Parts 1 and 2; files marked "skimmed" were read by heading
and opening only. Skipped: image assets (`assets/` GIF, docs images), `docs/writing-workflow.html` body,
`CHANGELOG.md` body, `scripts/sync_cw_skills.py` body, `bin/install.js` body, `test/install.test.js`
body (packaging, no writing guidance); nothing was run.
