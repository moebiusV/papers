# Revision pass — What the Viking Poets Knew

Editorial and fact-check pass over `chapters/`. Prose only; no argument, structure,
or citation content was altered. `book.typ`, `Makefile`, `build.sh`, `README.md`,
and `DESCRIPTION.md` are untouched. Full line-level diff in `REVISIONS.diff`.

## Fact-check (all verified against sources; nothing needed correcting)

Every post-cutoff claim in the manuscript holds up:

- **Gurnee et al., "Verbalizable Representations Form a Global Workspace in Language
  Models"** (Transformer Circuits, Anthropic, 2026-07-06). Title, date, J-lens/J-space
  characterization, the five functional properties, and the access-vs-phenomenal
  restriction are all stated correctly. URL `transformer-circuits.pub/2026/workspace`
  is live.
- **Karpathy LLM-wiki** (April 2, 2026 tweet, 16M+ views). Three-layer markdown/Obsidian
  architecture — immutable `raw/`, LLM-compiled `wiki/`, schema file — plus lint passes,
  described accurately.
- **MemPalace / Milla Jovovich + Ben Sigman.** The surprising attribution is real: the
  actress co-built it. 96.6% R@5 raw on LongMemEval, 100% with Haiku reranking, method
  of loci, verbatim storage — all correct.
- **OpenClaw.** Append-only log, curated long-term memory file, "memory flush" before
  compaction, and the three-phase "Dreaming" consolidation pass — all real and accurately
  described.
- **Karen Thomson, *The Decipherable Rigveda: The Earliest Indo-European Poetry***
  (Motilal Banarsidass). Title, publisher, the *grávan* = "a man who is singing" word
  study, and her Bristol/Warwick/Edinburgh training all match.

Classical/scientific claims spot-checked and sound as written: O'Keefe's 2014 Nobel for
place cells; the digamma recovered from Homeric meter (*woînos*, *wépos*, *androtēta*);
the boar's-tusk helmet in Mycenaean graves and Linear B; Ugaritic (1929) and Linear B
(1950s) as decipherment keys; Hygelac/Chlochilaicus in Gregory of Tours; Damasio's
somatic markers; Byzantine fault tolerance (Lamport 1982); Bitcoin (Nakamoto 2008). The
manuscript's own hedges on contested points (Haïk-Vantoura's decipherment, Delitzsch's
*edin*/Eden, the dating of the Song of Deborah, the boar's-tusk helmet as memory vs.
excavated object) are correctly placed.

## Style pass

**Em-dashes.** Removed all six prose em-dashes (all in Chapter 3), recast per house style
as commas, colons, or parentheses. Epigraph attribution dashes (`> — Author`) left in
place as a deliberate, consistent typographic convention.

**Staccato antithesis pairs.** Dissolved 24 clipped "X isn't Y. It's Z." / "Not X.
Structured Y." constructions across the introduction and Chapters 1, 2, 4, 5, 6, 7, and
the conclusion. Recasts vary — "not X but Y", semicolon merges, and full rewrites — to
avoid trading one machine cadence for another while keeping the direct register. The
argument's emphasis is preserved (e.g. "the disagreement isn't a failure of the system;
it *is* the system").

**Filler vocabulary.** "crucial" / "pivotal" in running prose and footnotes replaced with
"decisive" / "essential" / "central" / "the layer that matters most". A doubled "robust"
in Chapter 1 and two more in the conclusion varied to "durable". Left untouched:
technical uses ("error-correction robustness", "the encoding is so robust that
comprehension is not required"), the genuine metaphor "compressing a symphony into a
sentence", and the "Cannabis Synergy" paper title in a citation.

**Trailing whitespace** trimmed from chapter files.

Left deliberately intact: the attributed under-15-word quote in Chapter 7; the rhetorical
list cadence ("Standard intelligence tests: normal. Logical analysis: intact.") which is
voice, not antithesis; and all footnote scholarship.

## Rebuilding

The committed `viking-poets.pdf` / `viking-poets.docx` were removed because they no longer
match the corrected source. Regenerate them from `chapters/`:

    make            # PDF + DOCX via Typst / pandoc
    ./build.sh      # PDF only (typst compile book.typ book.pdf)
