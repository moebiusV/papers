// Print cover — What the Viking Poets Knew
// 6x9 in trade paperback, single integrated spread, Lulu-compatible
// Compile: typst compile cover.typ viking-poets-cover.pdf

#let tw = 6.00in   // trim width (one panel)
#let th = 9.00in   // trim height
#let sw = 0.73in   // spine width (290 pp, 50# cream)
                   // speedrun book's 523 pp → 1.31 in; confirm against printer spec
#let bd = 0.125in  // bleed

#set page(width: tw*2 + sw + bd*2, height: th + bd*2, margin: 0pt)
#set text(font: "EB Garamond", lang: "en")

// Panel edges (left-to-right on the OUTSIDE spread):
//   Back cover: [bd, bd+tw]              (LEFT panel)
//   Spine:      [bd+tw, bd+tw+sw]
//   Front cover:[bd+tw+sw, bd+tw*2+sw]   (RIGHT panel)

#let bc-l = bd
#let fc-l = bd + tw + sw
#let fc-c = fc-l + tw/2
#let bc-c = bc-l + tw/2
#let sc   = bd + tw + sw/2
#let sm   = 0.50in                     // safety margin from trim edges

// ── background ──────────────────────────────────────────────────────────
#let cover-bg = rgb(28, 30, 34)        // deep slate — adjust to match the artwork
#rect(width: 100%, height: 100%, fill: cover-bg)

// ═══════════════════════════════════════════════════════════════════════════
//  BACK COVER  (left panel)
// ═══════════════════════════════════════════════════════════════════════════

#place(top + left, dx: bc-l + sm, dy: 1.00in,
  block(width: tw - sm*2)[
    #set text(fill: luma(205), size: 11pt)
    #set par(first-line-indent: 0em, leading: 0.65em)

    *A skald composing in tenth-century Iceland and an engineer at Bell Labs in 1950 were working on the same problem, and they reached the same answer: structure is redundancy, and redundancy is how a signal survives a channel that wants to corrupt it. One worked in kennings, alliteration, and meter. The other worked in parity bits.*

    #v(0.7em)
    The skald's channel was human memory, a poem carried intact across centuries of imperfect recall; the engineer's was a noisy wire. Same fight against loss, different substrate. The skalds were only one workshop among many: the scribes who counted every letter of the Hebrew Bible, the reciters who kept the Vedas word-perfect for three thousand years — whole information technologies built to hold knowledge against forgetting, corruption, and forgery.

    #v(0.7em)
    Now a machine writes with perfect fluency and no idea when its own memory has invented something, while the field rediscovers these old defenses one patch at a time. If *Gödel, Escher, Bach* and *Hackers & Painters* are on your shelf, you have felt this convergence coming. The question the book leaves you turning over: what can the information technologies of the ancient world teach modern AI?
  ]
)

// ISBN
#let isbn-x = bc-l + tw - sm - 1.8in
#let isbn-y = th - sm - 1.0in
#place(top + left, dx: isbn-x, dy: isbn-y,
  rect(width: 1.8in, height: 0.9in, stroke: 0.5pt + luma(160)))
#place(top + left, dx: isbn-x, dy: isbn-y + 0.20in,
  block(width: 1.8in,
    align(center + horizon,
      text(fill: luma(160), size: 8pt, font: "Liberation Sans")[
        ISBN 978-0-000000-00-0 \
        9 0 0 0 0
      ]
    )
  )
)

// ═══════════════════════════════════════════════════════════════════════════
//  SPINE
// ═══════════════════════════════════════════════════════════════════════════

#let spine-text(body, size: 14pt, fill: luma(225), dy: 4.5in, tracking: 0.04em) = {
  let box-w = th - 1.2in
  place(top + left, dx: sc - box-w/2, dy: dy,
    rotate(-90deg,
      block(width: box-w,
        align(center + horizon,
          text(fill: fill, size: size, weight: "regular",
               tracking: tracking, hyphenate: false)[#body]
        )
      )
    )
  )
}

#spine-text("What the Viking Poets Knew", size: 16pt, dy: 3.6in)
#spine-text("David Walther", size: 13pt, fill: luma(160), dy: 7.30in)

// ═══════════════════════════════════════════════════════════════════════════
//  FRONT COVER  (right panel)
// ═══════════════════════════════════════════════════════════════════════════

// Title
#place(top + left, dx: fc-l, dy: 0.55in,
  block(width: tw,
    align(center + horizon,
      text(fill: luma(245), size: 30pt, weight: "regular", tracking: 0.02em)[What the Viking Poets Knew]
    )
  )
)

// Subtitle
#place(top + left, dx: fc-l, dy: 1.35in,
  block(width: tw,
    align(center + horizon,
      text(fill: luma(215), size: 15pt, style: "italic")[That AI Researchers Need To]
    )
  )
)

// Tagline
#place(top + left, dx: fc-l, dy: 1.85in,
  block(width: tw,
    align(center + horizon,
      text(fill: luma(205), size: 12pt, weight: "regular", tracking: 0.02em)[
        The beauty of the baud, \
        the poetry of the process
      ]
    )
  )
)

// Cover art
#let img-w = tw - sm*2
#place(top + left, dx: fc-l, dy: 2.60in,
  block(width: tw,
    align(center + horizon,
      image("cover.png", width: img-w, fit: "contain")
    )
  )
)

// Author
#place(top + left, dx: fc-l, dy: th - sm - 0.20in,
  block(width: tw,
    align(center + horizon,
      text(fill: luma(185), size: 15pt)[David Walther]
    )
  )
)

// ═══════════════════════════════════════════════════════════════════════════
//  CROP MARKS
// ═══════════════════════════════════════════════════════════════════════════

#let mk-len = 0.16in
#let mk-lw  = 0.4pt

#let crop(x, y, hd, vd) = {
  let hx = if hd == -1 { x - mk-len } else { x }
  place(top + left, dx: hx, dy: y, line(length: mk-len, stroke: mk-lw, angle: 0deg))
  let vy = if vd == -1 { y - mk-len } else { y }
  place(top + left, dx: x, dy: vy, line(length: mk-len, stroke: mk-lw, angle: 90deg))
}

#crop(bc-l,        bd,      -1, -1)
#crop(bc-l + tw,   bd,       1, -1)
#crop(bc-l,        bd + th, -1,  1)
#crop(bc-l + tw,   bd + th,  1,  1)
#crop(fc-l,        bd,      -1, -1)
#crop(fc-l + tw,   bd,       1, -1)
#crop(fc-l,        bd + th, -1,  1)
#crop(fc-l + tw,   bd + th,  1,  1)

// fold guides (dashed lines at spine edges)
#let fold(x) = {
  place(top + left, dx: x, dy: bd,
    line(length: th,
         stroke: (paint: luma(160), dash: "dashed", thickness: 0.3pt),
         angle: 90deg))
}
#fold(bc-l + tw)
#fold(fc-l)
