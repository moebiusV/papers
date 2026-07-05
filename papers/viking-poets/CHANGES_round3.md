# Editorial pass — round 3

## Blurb (blurb_jacket_copy.md) — rewritten
Two problems fixed: it repeated the false "everyone just wants bigger models"
straw-man, and the close was garbled ("...across domains that were never meant
to touch ... shown, not asserted" dangling). New version:
- Opens on the real problem (confident, fluent, and wrong; can't tell when its
  own memory invented something).
- States plainly that the field IS pursuing reliability, not just scale
  (retrieval, tool use, verification), and the book's point is that the
  traditions had the whole architecture these tools reinvent piecemeal.
- Keeps the GEB + Hackers & Painters follow-on nod. No em-dashes. ~150 words.

## Introduction — straw-man corrected (same error as the blurb)
The opening "Everyone in AI is asking... how do we make transformers smarter?
Bigger models, more parameters..." implied the field equates smarter with
bigger. Rewritten to acknowledge that reliability is already being bolted on
from outside (retrieval, tool use, verification, each briefly glossed in line),
and to make the sharper, true point: these arrive piecemeal, patch by patch, on
top of an unstated assumption that intelligence is fundamentally a scaling
problem. The "wrong question / right question" pivot is preserved.

## "Solutions being tried" now explained at first occurrence
Audit of the field's techniques the book invokes:
- RAG (retrieval-augmented generation): already fully explained at first
  occurrence in Chapter 2 (vector database, context window, the "duct tape"
  critique). No change needed.
- VM / tool offload / code interpreter: explained in Chapter 1 (footnote 6) and
  self-glossed in Appendix 2. OK.
- Calibration / uncertainty monitoring: explained in Chapter 6 (the
  token-probability-distribution passage). OK.
- Multi-agent verification: added a one-line gloss at first occurrence in
  Appendix 2 ("several model instances or specialized agents that cross-check
  one another's work rather than a single model grading itself").
- The Introduction's new mentions of retrieval/tool use/verification each carry
  a one-clause functional gloss, with the fuller treatment following in the
  chapters.

## Paul Graham — confirmed present, bio strengthened
Already in Chapter 6 (twice + fn 11) via "Taste for Makers." Added a one-clause
bio ("the Lisp programmer and essayist who co-founded the startup accelerator Y
Combinator") and noted in fn 11 that the essay is collected in *Hackers &
Painters*, grounding the blurb's reference in the book.

## Person-bio audit — gaps fixed
- Taliesin (Ch 3): quoted in the epigraph but never identified. Now "the
  legendary Welsh bard whose satirical contest against the court poets of King
  Maelgwn is preserved in the medieval Hanes Taliesin."
- Poincaré (Ch 6): "The French mathematician Henri Poincaré (1854–1912)…"
- Ramanujan / Hardy (Ch 6): "The self-taught Indian mathematician Srinivasa
  Ramanujan (1887–1920)…"; "the Cambridge number theorist G. H. Hardy, who
  brought him to England…"
- Eric Raymond (Ch 6): "the open-source programmer and essayist best known for
  The Cathedral and the Bazaar."
- Rest of the cast already follows the convention. Optional remaining: Jonathan
  Edwards, Joseph Campbell (works given, no one-clause bio).

## New passage — theory of mind, the world in motion, the time problem (Ch 1)
Inserted after the world-model cluster: theory of mind as real-time simulation
of a changing system (tracking game, reading a mood); why a shared dynamic
model makes communication compact (ties to kennings); and the LLM's
frozen-snapshot / no-clock weakness named as "the time problem," a missing
temporal channel to match the missing spatial one (the body). Two verified
footnotes (Premack & Woodruff 1978; Baron-Cohen, Leslie & Frith 1985) plus a
hedged footnote on the contemplative claim that time troubles "spirit"
intelligences (kept to a footnote; the book takes no position). Callback added
in Appendix 2 (real-time memory = the answer to the Ch 1 time problem).

## Citations verified this round
- Premack & Woodruff, BBS 1(4):515–526 (1978): confirmed.
- Baron-Cohen, Leslie & Frith, Cognition 21(1):37–46 (1985): confirmed.

## Round 3b — blurb reworked as a tease; more bios
- Blurb rewritten as a tease, not a summary: opens on one surprising
  equivalence (a tenth-century skald and a 1950 Bell Labs engineer solving the
  same error-correction problem), promises the through-line without
  enumerating it, and closes on an insider note (GEB + Hackers & Painters
  readers, "you were right"). Primary (~150 words) plus a shorter (~85 word)
  alternate. No footnote-style over-explanation.
- Bios added for the remaining bare introductions: Coleridge, Jonathan Edwards,
  Joseph Campbell, Kurt Vonnegut (with "Harrison Bergeron" now named in text),
  and light identifiers for Hesiod, Democritus, and Pindar.

## Round 3c — packaging, tagline, blurb relocated
- blurb_jacket_copy.md moved from the package root into chapters/.
- Full buildable scaffolding restored to the package: book.typ, build.sh,
  README.md, and every chapter's .desc (00–09). book.typ now lists Appendix 2
  (chapters/09_...) so it compiles into the book.
- Tagline added: "How ancient poetry can make AI reliable" — defined as
  #let book-tagline in book.typ and rendered on the full title page beneath the
  subtitle (with a short centered rule), and echoed at the top of the blurb.
  It is one line to change if you prefer another wording.

## Round 3d — tagline revised; README synced
- Tagline changed to "From ancient epic poems to modern AI: the technology of
  mind" (semicolon in the suggested form changed to a colon; "science of mind"
  is the alternate). Updated in book.typ (title page), the blurb, and the
  README header.
- README brought into sync with the corrected manuscript: removed all
  em-dashes; replaced the old "everyone just wants bigger models" straw-man
  paragraph with the corrected framing (field pursues reliability too, piece by
  piece); added Appendix 2 to the Contents; doc count 9 -> 10.

## Round 3e — DESCRIPTION.md (the README source) corrected
The README is generated from DESCRIPTION.md, so fixes were applied there:
- Removed all em-dashes; replaced the "everyone just wants bigger models"
  straw-man paragraph with the corrected framing (matches the book).
- Placed the marketing tagline "From ancient epic poems to modern AI: the
  technology of mind." as the first (italic) body line, so it renders right
  under the header when the README is regenerated.
- Note on schema: the metadata field labeled "Tagline:" actually holds the
  SUBTITLE ("That AI Researchers Need To"), which was left untouched. The
  marketing tagline lives in the body rather than a metadata field, since the
  generator's known fields are Title / Tagline / Creation-Date.
Both DESCRIPTION.md (source) and README.md (already-corrected output) ship in
the package.
