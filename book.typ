// ═══════════════════════════════════════════════════════════════════
//  What the Viking Poets Knew — Typst typesetting source
//  Compile with:  typst compile book.typ book.pdf
// ═══════════════════════════════════════════════════════════════════

#import "@preview/cmarker:0.1.1": render

// ─────────────────────────────────────────────────────────────────
//  METADATA  (edit these before going to print)
// ─────────────────────────────────────────────────────────────────

#let book-title     = "What the Viking Poets Knew"
#let book-subtitle  = "That AI Researchers Need To"
#let book-author    = "Author Name"
#let book-year      = "2026"
#let book-publisher = "Publisher Name"
#let book-city      = "City"
#let book-isbn      = "000-0-000000-00-0"

// ─────────────────────────────────────────────────────────────────
//  HELPERS
// ─────────────────────────────────────────────────────────────────

// Full title from a Markdown file's first H1 line
#let md-title(src) = {
  let line = src.split("\n").find(l => l.starts-with("# "))
  if line != none { line.slice(2).trim() } else { "" }
}

// Everything after the first H1 (the body text)
#let md-body(src) = {
  let lines = src.split("\n")
  let idx   = lines.position(l => l.starts-with("# "))
  if idx != none { lines.slice(idx + 1).join("\n") } else { src }
}

// Running-header title: strip "Chapter N: " or "Introduction: " prefix
#let md-short-title(src) = {
  let full  = md-title(src)
  let parts = full.split(": ")
  if parts.len() > 1 { parts.slice(1).join(": ") } else { full }
}

// Convert Markdown footnotes ([^id] / [^id]: text) to inline Typst footnotes.
// cmarker does not support Markdown footnote syntax, so we preprocess.
// Each [^id]: definition is collected, the definition lines are stripped,
// and each inline [^id] reference is replaced with a <!--raw-typst #footnote(...)-->
// block that cmarker will evaluate as live Typst.
#let process-footnotes(src) = {
  // Collect definitions: [^id]: text-to-end-of-line
  let footnotes = (:)
  for m in src.matches(regex("\[\^([^\]]+)\]: ([^\n]+)")) {
    footnotes.insert(m.captures.at(0), m.captures.at(1).trim())
  }

  // Strip definition lines
  let result = src.replace(regex("\n\[\^[^\]]+\]: [^\n]+"), "")

  // Replace inline [^id] references with raw-typst footnote calls.
  // The footnote body passes through render() so Markdown italics, em-dashes
  // etc. are handled correctly.
  for (id, text) in footnotes {
    let escaped = text.replace("\\", "\\\\").replace("\"", "\\\"")
    result = result.replace(
      "[^" + id + "]",
      "<!--raw-typst #footnote(render(\"" + escaped + "\", h1-level: 0))-->"
    )
  }
  result
}

// Chapter argument: centered italic index of the chapter's topics,
// typeset between the chapter title and the body text.
// Called from <!--raw-typst #chapter-argument[...]--> in Markdown.
#let chapter-argument(content) = {
  v(-0.9in)   // pull back against the 1in heading gap
  align(center,
    text(size: 10.5pt, style: "italic",
      par(first-line-indent: 0em, leading: 1.5em, content)
    )
  )
  v(0.6in)    // restore space before body text
}

// ─────────────────────────────────────────────────────────────────
//  STATE
// ─────────────────────────────────────────────────────────────────

// Current chapter's short title, used in recto running headers
#let running-title = state("running-title", "")

// ─────────────────────────────────────────────────────────────────
//  PAGE GEOMETRY  (6 × 9 in trade paperback)
// ─────────────────────────────────────────────────────────────────

#set page(
  width:  6in,
  height: 9in,
  margin: (top: 0.875in, bottom: 0.875in, inside: 1in, outside: 0.75in),
)

// ─────────────────────────────────────────────────────────────────
//  TYPOGRAPHY
// ─────────────────────────────────────────────────────────────────

#set text(font: "EB Garamond", size: 12pt, lang: "en")
#set par(justify: true, leading: 0.65em, first-line-indent: 1.5em)
#set strong(delta: 300)

// ─────────────────────────────────────────────────────────────────
//  ELEMENT STYLES
// ─────────────────────────────────────────────────────────────────

// Footnotes ── small, separated, flush-left
#set footnote.entry(
  separator: pad(bottom: 4pt, line(length: 33%, stroke: 0.4pt)),
  gap: 0.65em,
  indent: 0em,
)
#show footnote.entry: set text(size: 10pt)
#show footnote.entry: set par(first-line-indent: 0em, leading: 0.55em)

// Section breaks ── cmarker renders --- as line(length: 100%)
// Replace with a centred floral ornament
#show line: _ => [
  #v(0.9em)
  #align(center)[#text(size: 14pt)[❧]]
  #v(0.9em)
]

// Block quotes (intro epigraph, pull quotes)
#show quote.where(block: true): it => pad(
  top: 0.8em, bottom: 0.8em,
  left: 2em, right: 2em,
  par(
    first-line-indent: 0em,
    text(style: "italic", it.body)
  )
)

// H1 ── chapter / introduction title
// "Chapter N: Title" already in the string; just centre it large.
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(1.5in)
  align(center,
    text(size: 22pt, weight: "regular", tracking: 0.02em, it.body)
  )
  v(1in)
}

// H2 ── section headings (rare; kept for completeness)
#show heading.where(level: 2): it => block(
  above: 1.4em, below: 0.6em,
  text(size: 13pt, style: "italic", weight: "regular", it.body)
)

// ─────────────────────────────────────────────────────────────────
//  BODY-PAGE TEMPLATE  (running headers + Arabic page numbers)
// ─────────────────────────────────────────────────────────────────

#let body-pages(doc) = {
  set page(
    header: context {
      // Suppress header on chapter-opening pages
      // (those pages begin with a heading, so the header runs blank
      //  if we simply check whether the first element on the page
      //  is a heading — Typst handles this via weak pagebreaks.)
      let n = counter(page).at(here()).first()
      set text(size: 9pt, tracking: 0.06em)
      if calc.odd(n) {
        align(right, smallcaps(running-title.at(here())))
      } else {
        align(left, smallcaps(book-title))
      }
    },
    footer: context {
      let n = counter(page).at(here()).first()
      align(center, text(size: 10pt, str(n)))
    },
    numbering: "1",
  )
  doc
}

// ─────────────────────────────────────────────────────────────────
//  CHAPTER INCLUDE
// ─────────────────────────────────────────────────────────────────

#let chapter(path) = {
  let src        = read(path)
  let full-title = md-title(src)
  let short      = md-short-title(src)
  let body       = md-body(src)

  // Update running header before the heading so it's live on the
  // opening page and every page that follows.
  running-title.update(short)

  // Proper Typst heading → feeds #outline() automatically
  heading(level: 1, outlined: true, numbering: none)[#full-title]

  // Render Markdown body; pass render into scope so the footnote
  // <!--raw-typst --> blocks can call render() for their own content.
  render(process-footnotes(body), scope: (render: render, chapter-argument: chapter-argument))
}

// ═════════════════════════════════════════════════════════════════
//  FRONT MATTER
// ═════════════════════════════════════════════════════════════════

// ── Half-title ────────────────────────────────────────────────────

#page(header: none, footer: none, numbering: none)[
  #v(2.5in)
  #align(center,
    text(size: 18pt, weight: "regular", tracking: 0.03em, book-title)
  )
]

// ── Blank verso ───────────────────────────────────────────────────

#page(header: none, footer: none, numbering: none)[]

// ── Full title page ───────────────────────────────────────────────

#page(header: none, footer: none, numbering: none)[
  #v(1.5in)
  #align(center)[
    #text(size: 30pt, weight: "regular", tracking: 0.02em, book-title)
    #v(0.6em)
    #text(size: 16pt, style: "italic", weight: "regular", book-subtitle)
    #v(2.8em)
    #text(size: 13pt, book-author)
    #v(1fr)
    #text(size: 11pt)[#book-publisher #sym.dot.c #book-city]
    #v(0.6in)
  ]
]

// ── Copyright ─────────────────────────────────────────────────────

#page(header: none, footer: none, numbering: none)[
  #v(1fr)
  #set text(size: 10pt)
  #set par(first-line-indent: 0em, leading: 0.8em)

  Copyright #sym.copyright #book-year #book-author

  #v(0.8em)

  All rights reserved. No part of this publication may be reproduced,
  distributed, or transmitted in any form or by any means, including
  photocopying, recording, or other electronic or mechanical methods,
  without the prior written permission of the author, except in the
  case of brief quotations in critical reviews and certain other
  noncommercial uses permitted by copyright law.

  #v(0.8em)

  First edition, #book-year

  #v(0.8em)

  ISBN #book-isbn

  #v(0.8em)

  Typeset in EB Garamond using Typst. \
  Printed in the United States of America.
]

// ── Epigraph ──────────────────────────────────────────────────────

#page(header: none, footer: none, numbering: none)[
  #v(3in)
  #align(center)[
    #set text(size: 11pt, style: "italic")
    #set par(first-line-indent: 0em, leading: 1.1em)
    To make a machine think like ourselves, \
    first we must truly see ourselves.
  ]
]

// ── Table of contents ─────────────────────────────────────────────

#set page(
  header: none,
  footer: context {
    align(center,
      text(size: 10pt, counter(page).display("i"))
    )
  },
  numbering: "i",
)

#counter(page).update(1)

#v(0.5in)
#align(center,
  text(size: 14pt, tracking: 0.18em, upper[Contents])
)
#v(0.7in)

#show outline.entry: set text(size: 11pt)
#show outline.entry: set par(first-line-indent: 0em, leading: 1.6em)

#outline(
  title: none,
  depth: 1,
  indent: 0em,
)

// ═════════════════════════════════════════════════════════════════
//  BODY
// ═════════════════════════════════════════════════════════════════

#show: body-pages
#counter(page).update(1)

#chapter("book/00_introduction_the_wrong_question.md")
#chapter("book/01_chapter_1_intelligence_needs_bodies.md")
#chapter("book/02_chapter_2_the_scroll_that_doesnt_change.md")
#chapter("book/03_chapter_3_what_the_viking_poets_knew.md")
#chapter("book/04_chapter_4_the_adversarial_problem.md")
#chapter("book/05_chapter_5_what_the_meditators_knew.md")
#chapter("book/06_conclusion_the_incorruptible_manuscript.md")
