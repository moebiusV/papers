# Editorial pass — round 2

## Citations verified (with links)
- Ch.1 fn5 "Scaling Laws for Neural Language Models" = Kaplan et al. (2020).
  Verified real: https://arxiv.org/abs/2001.08361
- Ch.1 fn1 rewritten. Chung & Siegelmann (2021) is real
  (https://proceedings.neurips.cc/paper/2021/hash/ef452c63f81d0105dd4486f775adec81-Abstract.html)
  but is about RNNs, not transformers. The footnote now leads with the correct
  on-topic transformer result — Bhattamishra, Patel & Goyal, "On the
  Computational Power of Transformers..." CoNLL 2020
  (https://aclanthology.org/2020.conll-1.37/ , arXiv:2006.09286) — which is
  almost certainly what the fabricated "Bhatt et al." was mangling. Chung &
  Siegelmann kept as the parallel bounded-precision RNN result. The note now
  also ties both back to the book's external-memory argument.

## Conclusion
- Added the "tonic" paragraph: recapitulates the opening AI-failure theme
  (the 2026 LLM as brain-in-a-jar / the unlucky bard) beside the six doors,
  in the home key, closing the sonata form.

## New file: chapters/09_appendix_2_building_the_stack_in_silicon.md (+ .desc)
- Translates the six human layers into LLM analogs, per your outline:
  pervasive memory with attribution; real-time update (not frozen weights) with
  snapshotting; log-everything-then-prune; the write policy as a salience
  problem (apposition/surprise = what to store — the Crabtree/kenning point);
  debug the reasoning chain not just the answer (halakhic verification);
  "science is the discipline of what to preserve / LLMs must learn to do
  science"; and the seventh layer, motivation, with reality kept as referee so
  the drives stay honest. Cites OpenClaw (early 2026) alongside Karpathy's wiki
  and MemPalace as existing partial reinventions. ~2,400 words, prose, no
  em-dashes.

## New file: blurb_jacket_copy.md
- ~150-word jacket copy aimed at the three-layer audience; invokes GEB.

## Note
GEB / Hofstadter is NOT mentioned anywhere in the book. Hamming, Reed-Solomon,
and Shannon ARE (Chapter 3, text + footnote 2). The blurb's GEB comparison is
therefore an external framing device, not something the book claims internally.
