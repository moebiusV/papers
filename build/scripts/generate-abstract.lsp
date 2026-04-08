#!/usr/bin/env newlisp
; generate-abstract.lsp — Generate executive-summary abstracts for papers
; using Claude Opus, then insert them into paper.md YAML frontmatter.
;
; Usage:
;   ./scripts/generate-abstract.lsp                   ; all papers/
;   ./scripts/generate-abstract.lsp --private         ; include private/
;   ./scripts/generate-abstract.lsp --force           ; overwrite existing
;   ./scripts/generate-abstract.lsp --test            ; one paper then exit
;   ./scripts/generate-abstract.lsp papers/foo/paper.md  ; specific file
;
; Logs work to .abstract-log.db (sqlite3).
; Prints token counts and cost after each call and as a running total.

(load (string (env "HOME") "/.local/share/newlisp/curl4.lsp"))
(load "/usr/share/newlisp/modules/sqlite3.lsp")

; ── Constants ────────────────────────────────────────────────────────────────

(constant 'API-URL    "https://api.anthropic.com/v1/messages")
(constant 'MODEL      "claude-opus-4-6")
; Opus pricing (per million tokens, as of 2026)
(constant 'COST-IN    0.015)   ; $15 / 1M input tokens
(constant 'COST-OUT   0.075)   ; $75 / 1M output tokens

; ── Globals ───────────────────────────────────────────────────────────────────

(setq api-key      (trim (read-file (string (env "HOME") "/.anthropic_api_key"))))
(setq total-in     0)
(setq total-out    0)
(setq db           nil)

; ── CLI flags ─────────────────────────────────────────────────────────────────

(setq flag-private (find "--private" (main-args)))
(setq flag-force   (find "--force"   (main-args)))
(setq flag-test    (find "--test"    (main-args)))

; Positional args: paper.md paths (anything not starting with --)
(setq explicit-papers
  (filter (fn (a) (and (not (starts-with a "--"))
                       (> (length a) 0)
                       (!= a (main-args 0))
                       (!= a (main-args 1))))
          (rest (rest (main-args)))))

; ── SQLite logging ────────────────────────────────────────────────────────────

(define (db-open)
  (setq db (sqlite3:open ".abstract-log.db"))
  (sqlite3:exec db [text]
    CREATE TABLE IF NOT EXISTS abstracts (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      paper      TEXT NOT NULL,
      model      TEXT NOT NULL,
      tokens_in  INTEGER,
      tokens_out INTEGER,
      cost_usd   REAL,
      abstract   TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  [/text])
  (sqlite3:exec db [text]
    CREATE TABLE IF NOT EXISTS log (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      message    TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  [/text]))

(define (db-log msg)
  (when db
    (sqlite3:exec db (string "INSERT INTO log(message) VALUES(" (sqlite3:escape msg) ")"))))

(define (db-save-abstract paper tok-in tok-out cost-val abstract-text)
  (when db
    (sqlite3:exec db
      (string "INSERT INTO abstracts(paper,model,tokens_in,tokens_out,cost_usd,abstract)"
              " VALUES(" (sqlite3:escape paper) ","
              (sqlite3:escape MODEL) ","
              tok-in "," tok-out "," cost-val ","
              (sqlite3:escape abstract-text) ")"))))

; ── Cost display ─────────────────────────────────────────────────────────────

(define (format-cost usd)
  (format "US$%.4f" usd))

(define (print-cost label tok-in tok-out)
  (letn (cost (add (mul tok-in  (div COST-IN  1000000))
                   (mul tok-out (div COST-OUT 1000000))))
    (inc total-in  tok-in)
    (inc total-out tok-out)
    (println (string "  " label
                     " | in:" tok-in " out:" tok-out
                     " | call:" (format-cost cost)
                     " | total:" (format-cost
                                    (add (mul total-in  (div COST-IN  1000000))
                                         (mul total-out (div COST-OUT 1000000))))))
    cost))

(define (print-totals)
  (letn (total (add (mul total-in  (div COST-IN  1000000))
                    (mul total-out (div COST-OUT 1000000))))
    (println (string "\nTotal tokens: in=" total-in " out=" total-out))
    (println (string "Total cost:   " (format-cost total)))))

; ── Text extraction ───────────────────────────────────────────────────────────

(define (strip-frontmatter text)
  ; Remove YAML --- ... --- block at start
  (if (starts-with text "---")
    (letn (end-pos (find "\n---" text))
      (if end-pos
        (trim (slice text (+ end-pos 4)))
        text))
    text))

(define (extract-md path)
  (strip-frontmatter (read-file path)))

(define (extract-docx path)
  ; Use pandoc to convert DOCX to plain text
  (letn (cmd (string "pandoc " (escape-shell path) " --to=plain --wrap=none 2>/dev/null"))
    (trim (join (exec cmd) "\n"))))

(define (escape-shell s)
  (string "'" (replace "'" s "'\\''") "'"))

(define (extract-text path)
  (cond
    ((ends-with path ".md")   (extract-md path))
    ((ends-with path ".docx") (extract-docx path))
    (true (throw-error (string "Unsupported format: " path)))))

; Word count
(define (word-count text)
  (length (parse text {[\s]+} 4)))  ; 4 = PCRE_UNGREEDY (not needed, just split)

; ── Check for existing non-placeholder abstract ───────────────────────────────

(define (has-abstract? path)
  (if (not (file? path)) nil
    (letn (content (read-file path)
           found   (find "^abstract:" content 2))  ; 2 = PCRE_MULTILINE
      (if (not found) nil
        ; Check it's not a placeholder
        (not (find {(?i)\[Replace} content 0))))))

; ── YAML frontmatter update ───────────────────────────────────────────────────

(define (yaml-indent text)
  ; Indent every line with two spaces for YAML block scalar
  (join (map (fn (line) (string "  " line))
             (parse text "\n"))
        "\n"))

(define (insert-abstract paper-md abstract-text)
  (letn (content    (read-file paper-md)
         indented   (yaml-indent abstract-text)
         new-block  (string "abstract: |\n" indented)
         has-field  (find "^abstract:" content 2))
    (if has-field
      ; Replace existing abstract block (up to next top-level key or closing ---)
      (setq content (replace {(?m)^abstract:.*?(?=^\w|\Z)} content new-block 6))
      ; Insert before closing ---
      (setq content (replace "\n---\n" content (string "\n" new-block "\n---\n"))))
    (write-file paper-md content)
    (println (string "  Wrote abstract to: " paper-md))))

; ── Claude API call ───────────────────────────────────────────────────────────

(define (call-claude text)
  (letn (system-prompt
          [text]You are a senior policy analyst and editor. You write concise, authoritative executive summaries for whitepapers addressed to heads of state, government ministers, and senior advisors.

Rules:
- One paragraph, 80-120 words.
- Plain declarative prose. No bullet points, no headings.
- Open with the central claim or recommendation.
- Name the problem, the proposed solution, and the key benefit.
- Tone: formal, direct, confident. No hedging, no jargon.
- Do NOT begin with "This paper", "This document", or "This whitepaper".
- Write as if the proposal is addressed to one decision-maker. Do not imply or state that the same proposal is being shared with other governments, parties, or actors. No phrases like "various stakeholders", "multiple governments", "international partners", or anything suggesting parallel outreach.[/text]

         ; Truncate to ~8000 words
         words      (parse text {[\s]+} 0)
         short-text (if (> (length words) 8000)
                      (string (join (slice words 0 8000) " ") "\n\n[truncated]")
                      text)

         user-msg   (string "Generate an executive-summary abstract for the following paper.\n"
                            "Return only the abstract text — no preamble, no labels.\n\n"
                            "---\n" short-text)

         payload    (string "{\"model\":\"" MODEL "\","
                            "\"max_tokens\":300,"
                            "\"system\":" (json-encode system-prompt) ","
                            "\"messages\":[{\"role\":\"user\",\"content\":"
                            (json-encode user-msg) "}]}")

         slist      0)

    (curl:start)
    (setq slist (curl_slist_append slist "Content-Type: application/json"))
    (setq slist (curl_slist_append slist (string "x-api-key: " api-key)))
    (setq slist (curl_slist_append slist "anthropic-version: 2023-06-01"))
    (curl:setopt CURLOPT_HTTPHEADER slist)
    (curl:post API-URL payload)
    (curl_slist_free_all slist)

    (letn (http-code (curl:http_code)
           body      curl:body)
      (curl:stop)
      (when (!= http-code 200)
        (throw-error (string "API error " http-code ": " body)))
      body)))

(define (json-encode s)
  ; Minimal JSON string encoding
  (setq s (replace {\\} s {\\\\}))
  (setq s (replace {"} s {\"}))
  (setq s (replace "\n" s {\n}))
  (setq s (replace "\r" s {\r}))
  (setq s (replace "\t" s {\t}))
  (string "\"" s "\""))

(define (parse-api-response body)
  ; Extract content text and usage from API JSON response
  (letn (parsed (json-parse body))
    (if (not parsed)
      (throw-error (string "Failed to parse API response: " body))
      (letn (content   (lookup "content" parsed)
             usage     (lookup "usage" parsed)
             tok-in    (int (lookup "input_tokens" usage) 0 10)
             tok-out   (int (lookup "output_tokens" usage) 0 10)
             text-val  (lookup "text" (nth 0 content)))
        (list text-val tok-in tok-out)))))

; ── Process one paper ─────────────────────────────────────────────────────────

(define (process-paper source-path paper-md)
  (println (string "\nPaper: " paper-md))

  (when (and (not flag-force) (has-abstract? paper-md))
    (println "  Skipping (abstract exists). Use --force to regenerate.")
    (db-log (string "SKIP " paper-md))
    (throw 'skip nil))

  (letn (text (extract-text source-path)
         wc   (word-count text))
    (when (< wc 50)
      (println (string "  WARNING: only " wc " words extracted, skipping."))
      (db-log (string "SKIP-SHORT " paper-md " words=" wc))
      (throw 'skip nil))

    (println (string "  Calling Opus (" wc " words)..."))
    (letn (body    (call-claude text)
           result  (parse-api-response body)
           abst    (nth 0 result)
           tok-in  (nth 1 result)
           tok-out (nth 2 result)
           cost    (print-cost paper-md tok-in tok-out))
      (insert-abstract paper-md abst)
      (db-save-abstract paper-md tok-in tok-out cost abst)
      (db-log (string "OK " paper-md)))))

; ── Find papers ───────────────────────────────────────────────────────────────

(define (find-papers base-dir)
  ; Returns list of (source-path paper-md) pairs
  (let (result '())
    (dolist (subdir (directory base-dir {^[^.]} 0))
      (letn (dir     (string base-dir "/" subdir)
             md-path (string dir "/paper.md"))
        (if (file? md-path)
          (push (list md-path md-path) result -1)
          ; No paper.md — look for DOCX
          (dolist (f (directory dir {\.docx$} 0))
            (push (list (string dir "/" f) md-path) result -1)))))
    result))

; ── Main ─────────────────────────────────────────────────────────────────────

(define (main)
  (db-open)
  (db-log (string "START flags: private=" (string flag-private)
                  " force=" (string flag-force)
                  " test=" (string flag-test)))

  (letn (papers
          (if (> (length explicit-papers) 0)
            (map (fn (p) (list p p)) explicit-papers)
            (let (pp (find-papers "papers"))
              (when flag-private
                (extend pp (find-papers "private")))
              pp)))

    (when (= (length papers) 0)
      (println "No papers found.")
      (db-log "EXIT no papers")
      (exit))

    (println (string "Found " (length papers) " paper(s).\n"))

    (dolist (pair papers)
      (letn (src (nth 0 pair)
             md  (nth 1 pair))
        (catch
          (process-paper src md)
          'skip))
      (when flag-test
        (println "\n--test: stopping after first paper.")
        (break))))

  (print-totals)
  (db-log "END")
  (sqlite3:close db))

(catch (main) 'top-err)
(when top-err
  (println (string "FATAL: " top-err))
  (when db (sqlite3:close db))
  (exit 1))

(exit)
