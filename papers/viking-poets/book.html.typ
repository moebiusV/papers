// What the Viking Poets Knew - HTML template
//
// The web counterpart of book.header.typ.  buildabook html fills in the chapter calls
// below the marker at the end and compiles with
//     typst compile --features html --format html
// The paged template uses page geometry, align, pad and v(), which an HTML export
// drops together with their contents, so this one is written in real HTML elements.
// Keep the helpers and the metadata in step with book.header.typ.

#import "@preview/cmarker:0.1.1": render

// -----------------------------------------------------------------
//  METADATA  (same as book.header.typ)
// -----------------------------------------------------------------

#let book-title     = "What the Viking Poets Knew"
#let book-subtitle  = "That AI Researchers Need To"
#let book-tagline   = "The beauty of the baud, the poetry of the process"
#let book-author    = "David Walther"
#let book-year      = "2026"
#let book-isbn      = "000-0-000000-00-0"

#set document(title: book-title, author: book-author)
#set text(lang: "en")

// -----------------------------------------------------------------
//  STYLE
// -----------------------------------------------------------------

#html.elem("style")[
  :root { color-scheme: light dark; }
  body { max-width: 40rem; margin: 2rem auto; padding: 0 1rem; font: 1.1rem/1.6 Georgia, "EB Garamond", serif; }
  h1, h2, h3 { font-weight: normal; line-height: 1.25; }
  h2 { text-align: center; font-size: 1.7rem; margin: 4rem 0 1.5rem; }
  h3 { font-style: italic; font-size: 1.2rem; margin: 2rem 0 .5rem; }
  p { margin: 0 0 1rem; }
  header.title-page { text-align: center; margin: 3rem 0 4rem; }
  header.title-page h1 { font-size: 2.4rem; margin-bottom: .3rem; }
  header.title-page .subtitle { font-size: 1.3rem; font-style: italic; margin: 0 0 1rem; }
  header.title-page .tagline { letter-spacing: .04em; margin: 0 0 1.5rem; }
  section.copyright { font-size: .85rem; margin: 3rem 0; }
  nav[role="doc-toc"] ol { list-style: none; padding: 0; }
  nav[role="doc-toc"] li { margin: .35rem 0; }
  blockquote { margin: 1.2rem 0 1.2rem 1.5rem; font-style: italic; }
  blockquote.epigraph { text-align: center; margin: 3rem 1rem; }
  blockquote.verse { padding-left: 1rem; border-left: 2px solid currentColor; }
  p.chapter-argument { text-align: center; font-style: italic; font-size: .95rem; margin: -.5rem 0 2.5rem; }
  p.ornament { text-align: center; font-size: 1.4rem; margin: 1.5rem 0; }
  sup { line-height: 0; }
  a { color: inherit; }
  section.footnotes, ol[role="doc-endnotes"] { font-size: .9rem; }
]

// -----------------------------------------------------------------
//  HELPERS  (same as book.header.typ, minus the page-only ones)
// -----------------------------------------------------------------

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

// Native math, as in the paged template (cmarker needs a callback for $...$)
#let render-math(body, block: false) = math.equation(
  block: block,
  eval(body, mode: "math"),
)

// Markdown footnotes ([^id] / [^id]: text) become Typst footnotes, as in book.header.typ
#let process-footnotes(src) = {
  let footnotes = (:)
  for m in src.matches(regex("\[\^([^\]]+)\]: ([^\n]+)")) {
    footnotes.insert(m.captures.at(0), m.captures.at(1).trim())
  }
  let result = src.replace(regex("\n\[\^[^\]]+\]: [^\n]+"), "")
  for (id, text) in footnotes {
    let escaped = text.replace("\\", "\\\\").replace("\"", "\\\"")
    result = result.replace(
      "[^" + id + "]",
      "<!--raw-typst #footnote(render(\"" + escaped + "\", h1-level: 0, math: render-math))-->"
    )
  }
  result
}

// A page has no number on the web.  pgan plants an anchor; pageof links to it.
#let pgan(id) = html.elem("span", attrs: (id: "pg-" + id))[]
#let pageof(id) = html.elem("a", attrs: (href: "#pg-" + id))[here]

// Centred italic index of a chapter's topics, between the title and the text
#let chapter-argument(content) = html.elem("p", attrs: (class: "chapter-argument"), content)

// Verse quotation
#let verse-quote(body) = html.elem("blockquote", attrs: (class: "verse"), body)

// cmarker renders a Markdown rule (---) as a line; the web shows the ornament instead
#show line: _ => html.elem("p", attrs: (class: "ornament"))[\u{2767}]

// -----------------------------------------------------------------
//  CHAPTER INCLUDE
// -----------------------------------------------------------------

// buildabook passes the structural kind from outline.txt, as for the paged template.
// The heading gets the id "ch-" plus its file name without ".md" (Typst writes a label as an
// id only when it is a plain identifier, so no leading digit), so a page can link to one
// chapter of the single HTML file; buildabook readme does.
#let chapter(path, token: none, part: false, toc: true) = {
  let src        = read(path)
  let full-title = md-title(src)
  let body       = md-body(src)

  let stem = if path.ends-with(".md") { path.slice(0, path.len() - 3) } else { path }
  let id   = "ch-" + stem.replace(regex("[^A-Za-z0-9_-]"), "-")
  [#heading(level: 1, outlined: toc, numbering: none)[#full-title]#label(id)]
  if token != none {
    pgan(token.split(":").last())
  }

  render(
    process-footnotes(body),
    math: render-math,
    blockquote: it => html.elem("blockquote", it),
    scope: (
      render: render,
      chapter-argument: chapter-argument,
      render-math: render-math,
      verse-quote: verse-quote,
    ),
  )
}

// =================================================================
//  FRONT MATTER
// =================================================================

#html.elem("header", attrs: (class: "title-page"))[
  #html.elem("h1")[#book-title]
  #html.elem("p", attrs: (class: "subtitle"))[#book-subtitle]
  #html.elem("p", attrs: (class: "tagline"))[#book-tagline]
  #html.elem("p")[#book-author]
]

#html.elem("section", attrs: (class: "copyright"))[
  Copyright #sym.copyright #book-year #book-author

  All rights reserved. No part of this publication may be reproduced,
  distributed, or transmitted in any form or by any means, including
  photocopying, recording, or other electronic or mechanical methods,
  without the prior written permission of the author, except in the
  case of brief quotations in critical reviews and certain other
  noncommercial uses permitted by copyright law.

  First edition, #book-year

  ISBN #book-isbn
]

#html.elem("blockquote", attrs: (class: "epigraph"))[
  To make a machine think like ourselves, \
  first we must truly see ourselves.
]

#html.elem("h2")[Contents]
#outline(title: none, depth: 1)

// Chapter list appended below by buildabook - DO NOT EDIT BELOW THIS LINE
