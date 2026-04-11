# Vom Wagner zum Walther: Siegfried Entfesselt

*Liberated from Latin, the Germanic Languages Converge*

## Project Summary

A text transformation system that converts Standard Written German into "Waltherian German" (Waltherisches Deutsch) — a form of the language that restores historical and dialectal features suppressed by 18th-19th century prescriptive standardization. Named for both the MHG poet Walther von der Vogelweide (whose era's grammar the output approximates) and for David Walther (project originator).

The system applies two categories of transformation:

**Category A — Compound Entfusion (original scope):**
1. Splitting compounds exceeding a complexity threshold
2. Restoring historically-erased case morphology at compound joints
3. Recovering original case forms preserved inside Fugenlaute, including archaic forms

**Category B — Syntactic Entfesselung (expanded scope):**
4. Verb position relaxation (restoring MHG/southern German verb-second in subordinate clauses)
5. *Von*-restoration (preferring *von* + dative over synthetic genitive)
6. Progressive aspect restoration (*am* + infinitive construction)
7. *Tun*-periphrasis restoration (*tun* as auxiliary for emphasis/questions/negation)
8. Dative-possessive restoration (*dem Vater sein Haus* pattern)
9. Double negation restoration (MHG-style *nicht...nicht/kein...nicht*)
10. Articles with proper names (*der Hans, die Maria*)

**Core principle:** The system is **optional** — a reading aid, pedagogical tool, and linguistic experiment, not a top-down orthographic mandate. Every transformation restores a feature that is attested in historical German (OHG, MHG, ENHG), in living dialects (Bavarian, Alemannic, Swiss, Rhineland, Austrian), or both. Nothing is invented. The output reads as "relaxed southern German with archaic flavor" — fully intelligible to any German speaker.

**Historical thesis:** Standard Written German (Hochdeutsch/Schriftdeutsch) is not a neutral representation of the German language. It is the product of an aggressive 18th-19th century prescriptive project that took the most conservative, Latinate register of one regional dialect (East Central German, the Saxon chancellery language) and declared it "correct," systematically suppressing features shared with the wider Germanic family. Entfesselt reverses this suppression.

---

## Rationale and Origins

### The hidden family resemblance

The Germanic languages — English, German, Dutch, Frisian, the Scandinavian languages, Yiddish, Plautdietsch — are a family. Speakers of any one of them carry an intuitive grasp of the others that is obscured, not aided, by the way these languages are conventionally written.

A Dutch speaker looking at a German insurance contract sees an impenetrable wall of fused compound nouns. An English speaker opening Kafka sees verb-final subordinate clauses that require holding an entire thought in working memory before the verb arrives and reveals what happened. A Dane reading a German newspaper encounters word order patterns that feel alien despite sharing 80% cognate vocabulary. In each case, the structural similarities between the languages are buried under surface conventions that make them look more different than they are.

This project originated from a simple observation: if you decompose German compound nouns by inserting spaces at the fusion joints and restoring the case morphology that was erased during fusion, the resulting text is structurally almost identical to English noun phrases. *Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz* becomes *Rindfleisches Etikettierungs Überwachungs Aufgaben Übertragungs Gesetz* — and an English speaker can suddenly see "Beef Labeling Supervision Duties Transfer Law" staring back at them. The information was always there. The spaces unlock it.

This led to a deeper question: if compound fusion is a surface convention that obscures Germanic family resemblance, what other surface conventions in Standard Written German do the same thing? Investigation revealed that the 18th-19th century prescriptive standardization of German systematically suppressed exactly the features German shares with English, Dutch, Frisian, and Scandinavian — and retained or strengthened exactly the features that make German look most different from its siblings.

### The Latinization hypothesis

Why would German prescriptivists have pushed the written language away from its Germanic siblings and toward patterns that resemble Latin? The answer may lie in the political identity of the German-speaking world during the formative period of standardization.

The Holy Roman Empire — *Heiliges Römisches Reich Deutscher Nation* — defined itself as the continuation of Rome. Its legitimacy rested on the claim of Roman succession. Latin was the language of the Church, of law, of scholarship, of imperial administration. For a millennium, the most educated German speakers were bilingual in Latin, and the prestige register of German was shaped by Latin models.

When Gottsched, Adelung, and their successors set about standardizing German in the 18th century, their explicit models were Latin grammar and French prose style (French being the contemporary prestige language, itself heavily Latinized). They valued:

- **Periodic sentence structure** with the verb withheld until the end of the clause — modeled on Ciceronian Latin, where the verb conventionally appears last. This became the German subordinate-clause verb-final rule.
- **Synthetic case morphology** over analytic prepositional constructions — because Latin expresses grammatical relations through case endings rather than prepositions. This suppressed the natural German drift toward *von*-constructions.
- **Single-negation logic** — because Latin grammarians taught that two negatives make a positive. This killed the native Germanic double negation that MHG used freely.
- **Complex nominal compounds** written as single orthographic units — possibly influenced by Latin's own tendency toward long compound adjectives and the scholarly habit of creating technical terminology through compounding rather than periphrasis.
- **Suppression of do-support** (*tun*-periphrasis) — because Latin has no equivalent construction, and the prescriptivists considered any structure without a Latin parallel to be "vulgar."

The irony is profound. German was Latinized in the name of the Holy *Roman* Empire — but the actual linguistic evidence suggests that the spoken vernacular of German-speaking peoples was, throughout this period, evolving in the same direction as English, Dutch, and Scandinavian: toward analytic constructions, flexible word order, do-support, and prepositional possession. The prescriptive standard froze German in an artificially conservative, artificially Latinate state while the living language continued to evolve underneath.

Every dialect of German — Bavarian, Alemannic, Swiss, Rhineland, Saxon, Austrian — preserves features that the written standard suppresses. These features are not "errors" or "corruptions." They are the natural Germanic inheritance that the standardizers tried to erase. Entfesselt restores them.

### Practical benefits

**For English speakers learning German:** Entfesselt German is dramatically more accessible than Standard Written German. The compound decomposition makes vocabulary transparent. The verb position relaxation eliminates the most disorienting word-order difference. Do-support and the progressive aspect feel immediately familiar. The *von*-construction maps directly to English "of." A learner who can read Entfesselt German can transition to Standard German gradually, understanding *why* the standard differs rather than merely memorizing rules that feel arbitrary.

**For Dutch and Scandinavian speakers:** The compound decomposition and syntactic relaxation bring German structurally close enough to Dutch and Scandinavian that passive reading comprehension becomes feasible without formal study. An educated Dane with no German training can read an Entfesselt Spiegel article and follow the argument — something that is nearly impossible with Standard Written German despite the massive shared vocabulary.

**For German speakers:** Entfesselt text reads as informal, southern-flavored, slightly archaic German. It is fully intelligible. Many German speakers will recognize it as "how my grandmother talks" or "how people actually speak in Bavaria/Austria/Switzerland." The experience of reading it may prompt reflection on how much of the written standard is convention rather than necessity.

**For the Inter-Germanic centroid project:** Entfesselt German is the form of German that participates in the centroid. With compounds unfused and syntax relaxed, German's structural distance from the rest of the family collapses. The centroid language becomes feasible precisely because Entfesselt reveals that German was never as far from its siblings as the written standard makes it appear.

---

## Part I: Compound Entfusion

### Rule 1: Compound Identification

Input text is tokenized. Each token is checked against a compound splitter. Candidates are nouns (capitalized in German) that decompose into two or more independent morphemes.

**Tools:** Existing German compound splitters:
- CharSplit (neural character-based splitter)
- jWordSplitter (dictionary-based)
- GermaNet compound data
- SMOR (Stuttgart Morphological Analyzer)
- BPEmb subword embeddings as a fallback

**Output:** Each compound decomposed into constituent morphemes with boundaries and Fugenlaute marked.

Example: `Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz`
→ `[Rind][fleisch][etikettierung][s][überwachung][s][aufgaben][übertragung][s][gesetz]`

### Rule 2: The Two-Tier Threshold

Count *content morphemes* (excluding Fugenlaute) in the compound.

#### Tier 1: Algorithmic (> 4 content morphemes) — ALWAYS UNFUSE

Compounds exceeding four content morphemes are always unfused. No human judgment needed. These are productive/nonce formations — bureaucratic chains, legal terminology, technical stacks. No German speaker stores these as dictionary entries; they parse them on the fly. The system makes that parsing visible.

This tier ships immediately with zero curation.

#### Tier 2: Curated (≤ 4 content morphemes) — DEFAULT FUSED, OPTIONAL UNFUSING

Compounds of four elements or fewer are kept fused by default — treated as vocabulary items, like irregular verbs. Existing Fugenlaute inside them are preserved as lexical irregularities.

Many 3-4 element compounds are transparent enough that unfusing benefits readability. These are candidates for optional unfusing via human curation.

**Three bins:**

**Bin A — NEVER UNFUSE:** Opaque/lexicalized compounds.
```
Handschuh, Kindergarten, Schmetterling, Flugzeug, Hubschrauber, Staubsauger
```

**Bin B — OPTIONALLY UNFUSE:** Transparent compounds benefiting from unfusing.
```
Bundesgesundheitsminister, Kraftfahrzeugversicherung
```

**Bin C — LEAVE ALONE:** Short lexicalized compounds, no benefit to unfusing.
```
Krankenhaus, Krankenwagen, Kühlschrank, Briefträger, Flughafen, Bahnhof
```

**Curation workflow:**
1. Extract all ≤4-element compounds from target corpus
2. LLM scores each for transparency (1-5), assigns tentative bin
3. Native German speaker reviews, adjusts bins
4. Static lookup table shipped with tool, grows over time

**Curation is a separate sub-project and is NOT required for operation.** The LLM handles all compound splitting decisions from day one. It already knows which 2-word sub-compounds are real lexicalized words, it already understands hierarchical structure, and it already makes sound splitting decisions. The curation project exists to *codify* those decisions into a static lookup table for speed, consistency, and offline operation — but the system produces good output without it.

During processing, all encountered ≤4-element compounds are logged to a file (`compounds-for-curation.tsv`) with their context, frequency, LLM-determined splitting, and tentative bin assignment. This file accumulates across processing runs and feeds the curation workflow whenever it begins. The curation sub-project has its own section (see Part III) but does not block any phase of the main pipeline.

**Key principle:** The LLM is the primary decision-maker. Curation is refinement, not prerequisite.

#### The Two-Word Preservation Default

When splitting 3-4 element compounds, **prefer to preserve lexicalized 2-word sub-compounds as fused units.** This is the natural splitting strategy — it respects the internal hierarchical structure of the compound and produces output that matches how German speakers actually parse.

**Example:** *Krankenhausfinanzierung* (Krankenhaus + Finanzierung)
- **Preferred:** Krankenhaus Finanzierung (preserves the lexicalized 2-word compound *Krankenhaus*)
- **Not preferred:** Kranken Haus Finanzierung (decomposes a unit that functions as a single word)

**Example:** *Bundesgesundheitsminister* (Bundes + Gesundheitsminister or Bundes + Gesundheit + Minister)
- **Preferred:** Bundes Gesundheitsminister (preserves 2-word sub-compound *Gesundheitsminister*)
- **Also acceptable:** Bundes Gesundheits Minister (fully decomposed — curator decision)

**Implementation:** When the compound splitter identifies sub-compounds that exist as independent dictionary entries (Duden headwords), those sub-compounds are kept fused by default. The LLM uses these preserved sub-compounds as the primary splitting points. Full decomposition is offered as a curator option but is not the default.

This principle applies recursively: in a 5+ element compound being algorithmically unfused, any 2-word sub-compound that is a dictionary entry stays fused. The split happens at the joints *between* lexicalized sub-compounds, not inside them.

#### Visual Scan Distance — The Third Criterion

The element count threshold (≤4 stay fused) and the lexicalization test (opaque meaning stays fused) are necessary but not sufficient. A third criterion applies: **visual scan distance**.

English-trained eyes expect a word boundary roughly every 5-8 characters. Germanic languages other than German share this expectation — Dutch, Frisian, Scandinavian words are generally shorter than German fused compounds. The P95 of English dictionary word length is **14 characters** — meaning 95% of all English words are 14 characters or shorter. When a German compound exceeds 14 characters in fused form, it is longer than 95% of all English words, making it visually hostile to readers trained on English or other Germanic languages.

**The three criteria interact:**

| Element count | Lexicalized? | Length | Decision |
|---|---|---|---|
| >4 | — | — | ALWAYS unfuse |
| ≤4 | Opaque | — | NEVER unfuse (Handschuh, Schmetterling) |
| ≤4 | Transparent | ≤14 chars | Default fused (Rathaus, Bahnhof) |
| ≤4 | Transparent | >14 chars | CANDIDATE for unfusing (Versicherungsvertrag) |

The visual scan distance criterion is secondary — it identifies *candidates* for unfusing, not automatic unfusing. Each candidate is evaluated by the LLM or curator and, if approved, entered into the Entfesselt Wörterbuch.

#### Word-Family Consistency

Once a modifier element (*Kasus-*, *Prestige-*, *Fach-*, *Bundes-*) is unfused in one compound, it unfuses in ALL compounds that use it by default. This ensures dictionary consistency — a reader who sees *Kasus Morphologie* will also see *Kasus Endungen*, not the inconsistent *Kasus Morphologie* alongside *Kasusendungen*.

**Exceptions are permitted** (like irregular verbs) when a specific compound in the word family is (a) under 14 characters AND (b) unfusing would damage intelligibility or create ambiguity. These exceptions are individually documented in the Wörterbuch.

#### The Entfesselt Wörterbuch (Dictionary)

All unfusing decisions are recorded in a dictionary file (the *Entfesselt Wörterbuch*). Once a compound is unfused in the Wörterbuch, it stays unfused **everywhere, in every text, without exception**. Consistency is non-negotiable.

The Wörterbuch is a project deliverable — a growing, curated dictionary of Entfesselt forms that ships with the tool and grows with each text processed. It contains:

- The standard fused form
- The Entfesselt unfused form (with preserved Fugenlaute / restored case endings)
- Which criterion triggered the unfusing (element count, curation, visual scan distance)
- English gloss

The Wörterbuch ensures that the same compound is always rendered the same way across all target texts — Grundgesetz, Communist Manifesto, Kafka, Wagner, etc.

#### Effect on Grammar Regularity

Capping productive compounding at 4 elements makes the Fugenlaut system a **closed class**. No new Fugenlaut choices needed — all new multi-element terminology assembled phrasally using regular case marking. Existing irregulars are vocabulary; the productive system is regular.

Analogous to English irregular verbs: ~200 memorized forms, but the productive rule (add -ed) is perfectly regular.

### Rule 3: Relationship Classification

For each joint in an unfused compound, classify the semantic relationship:

| Relationship | Description | Example |
|---|---|---|
| GENITIVE-POSSESSIVE | X belongs to Y | Königs+krone |
| GENITIVE-SUBJECTIVE | X performs action of Y | Sonnen+aufgang |
| GENITIVE-OBJECTIVE | X is acted upon by Y | Brief+träger |
| MATERIAL | Y is made from X | Stein+mauer |
| PURPOSE | Y is for X | Schreib+tisch |
| LOCATION | Y is at X | Haus+tür |
| TEMPORAL | Y occurs during X | Nacht+schicht |
| INSTRUMENT | Y is done by X | Dampf+schiff |

**Implementation:** LLM-assisted, rule-based fallback (genitive default for noun+noun, purpose for verb+noun), or hybrid.

### Rule 4: Case Restoration — The Fossil-First Principle

**CRITICAL PRINCIPLE: Fossil-first.** The Fugenlaut is the primary evidence of the original case relationship. Where present, it is preserved as-is, even if Modern German phrasal syntax would use a different form. The unfused text may contain archaic case forms — this is a feature, not a bug.

**Priority order:**
1. Fugenlaut corresponds to recognizable historical case form (OHG/MHG/ENHG) → PRESERVE
2. Fugenlaut corresponds to Modern German case form → PRESERVE
3. Fugenlaut has no identifiable case origin → use most appropriate historical form, preferring oldest intelligible
4. No historical form traceable → fall back to Modern German phrasal syntax

**Examples:**

| Compound | Fugenlaut | Historical origin | Unfused form |
|---|---|---|---|
| Königskrone | -s- | Genitive -s (modern and historical) | Königs Krone |
| Liebeslied | -s- | MHG feminine genitive -s | Liebes Lied |
| Sonnenschein | -en- | Weak noun genitive -en (OHG sunnen) | Sonnen Schein |
| Freiheitsstatue | -s- | MHG abstracts in -heit took genitive -s | Freiheits Statue |

**Declension resources:** Wiktionary, LanguageTool morphdb, Lexer's MHG Handwörterbuch, Köbler's OHG Wörterbuch, Grimm's Deutsches Wörterbuch, Morphy.

### Rule 5: Fugenlaut Handling — Preserve, Trace, Restore

Fugenlaute are NOT stripped. They are primary evidence. Default: preserve as suffix on preceding word after space insertion.

| Fugenlaut | Action |
|---|---|
| -s-, -es- | PRESERVE. Genuine genitive. |
| -n-, -en- | PRESERVE. Weak declension form. |
| -e- | TRACE to historical origin. |
| -er- | PRESERVE. Often genuine plural. |
| -ens- | PRESERVE. Weak genitive + -s. |
| -(zero)- | RESTORE appropriate historical case form. |

Zero-linker cases are the only ones requiring active restoration.

### Rule 6: Output Formatting

**Capitalization:** All nouns capitalized (standard German orthography).
**Spacing:** Spaces at unfused joints. No hyphens unless ambiguous.
**Article insertion:** Optional. Minimal mode (default) relies on fossilized case forms. Full phrasal mode inserts articles where needed.

### Rule 7: Verb-Noun Compounds

Restore full infinitive form; use "zum/zur" where appropriate. Below threshold → stays fused.

### Rule 8: Adjective-Noun Compounds

Restore full adjectival agreement. Below threshold → stays fused.

---

## Part II: Syntactic Entfesselung

These transformations address features of Standard Written German that were imposed by 18th-19th century prescriptivism over attested historical and dialectal patterns. Each transformation restores a feature with centuries of attestation.

### Rule 9: Verb Position Relaxation

**What it restores:** Verb-second word order in subordinate clauses.

**Standard German:** *Ich weiss, dass er nach Hause gegangen ist.* (verb-final)
**Entfesselt:** *Ich weiss, dass er ist nach Hause gegangen.* (verb-second)

**Attestation:** MHG texts (Walther, Wolfram, Gottfried) show verb-second in subordinate clauses regularly. Universal in Bavarian, Alemannic, and Swiss German dialects today. Common in spoken German across all regions. The verb-final rule in subordinate clauses was *strengthened* by prescriptive standardizers, not inherited from the historical language.

**Implementation:** LLM moves finite verb from clause-final to post-conjunction position. Both orders remain acceptable; Entfesselt prefers verb-second where it produces more natural-sounding German.

### Rule 10: *Von*-Restoration

**What it restores:** Prepositional possession with *von* + dative.

**Standard German:** *Das Haus meines Vaters* (synthetic genitive)
**Entfesselt:** *Das Haus von meinem Vater* (analytic, with *von*)

**Attestation:** Dominant pattern in spoken German across all regions. Standard in Swiss German and Austrian dialects. Productive since ENHG. Structurally identical to English "of my father," Dutch "van mijn vader," Scandinavian constructions.

**Implementation:** Replace synthetic genitive with *von* + dative where colloquially attested. Both forms remain acceptable; Entfesselt prefers *von*-construction as default.

### Rule 11: Progressive Aspect (*am* + Infinitive)

**What it restores:** The German progressive construction.

**Standard German:** *Ich arbeite.* (ambiguous: habitual or right-now)
**Entfesselt:** *Ich bin am Arbeiten.* (progressive: right-now only)

**Attestation:** Documented from 15th century. Standard in Rhineland German, Luxembourgish. Structurally identical to Dutch *aan het werken zijn* and English *is working*. Fills a real aspectual gap — Standard German has no way to distinguish habitual from progressive without adverbs.

**Implementation:** Where source text implies ongoing action (context-dependent), offer progressive alternative. LLM determines when progressive aspect is semantically appropriate.

### Rule 12: *Tun*-Periphrasis

**What it restores:** *Tun* (do) as auxiliary verb for emphasis, question formation, negation.

**Standard German:** *Verstehst du das?* (synthetic question)
**Entfesselt:** *Tust du das verstehen?* (do-support, as in English)

**Standard German:** *Ich arbeite wirklich.* (adverbial emphasis)
**Entfesselt:** *Ich tu wirklich arbeiten.* (do-support emphasis)

**Attestation:** Attested from 14th century. Used by Luther in his Bible translation. Universal in all German dialects. Independently reinvented by every German-speaking child before school teaches them not to. Stigmatized by 18th century prescriptivists because Latin has no do-support.

**Implementation:** LLM inserts *tun*-periphrasis where it serves emphasis, question formation, or negation support. Not mandatory — offered as alternative construction.

### Rule 13: Dative-Possessive

**What it restores:** *Dem X sein Y* pattern for possession.

**Standard German:** *Das Haus des Vaters* (genitive)
**Entfesselt:** *Dem Vater sein Haus* (dative-possessive)

**Attestation:** Documented across all German dialect regions from MHG onward. Standard pattern in Yiddish. Parallels Dutch and colloquial Scandinavian constructions. Used by tens of millions of German speakers daily.

**Implementation:** Offered as alternative alongside genitive and *von*-constructions. LLM selects the most natural-sounding option based on context.

### Rule 14: Double Negation

**What it restores:** MHG-style reinforcing double negation.

**Standard German:** *Ich weiss nichts.* (single negation)
**Entfesselt:** *Ich weiss nichts nicht.* or *Ich weiss kein Ding nicht.*

**Attestation:** Productive in MHG (*ich enweiz niht*). Alive in Bavarian and Austrian dialect (*I hob koa Geld ned*). Parallels Afrikaans (*Ek het nie geld nie*). Shakespeare used double negation freely in English. Suppressed by prescriptivists importing Latin-derived logic that two negatives make a positive.

**Implementation:** Used sparingly for emphasis where dialectally natural. Not applied universally — reserved for contexts where reinforcement adds clarity or force.

### Rule 15: Articles with Proper Names

**What it restores:** Definite articles before personal names.

**Standard German:** *Hans kommt.* (no article)
**Entfesselt:** *Der Hans kommt.*

**Attestation:** Universal in spoken southern and central German, Austrian, and Swiss German. Attested from OHG. Suppressed in written standard as "informal" despite being the dominant pattern in speech for most of the German-speaking world.

**Implementation:** Insert *der/die* before personal names in narrative and dialogue contexts. Not applied in formal/legal contexts where bare names are conventional.

### Rule 16: Resumptive Pronouns After Parentheticals

**What it restores:** Pronoun that re-picks-up the subject after a long interruption (appositive, parenthetical list, relative clause).

**Standard German:** *Die germanischen Sprachen — Englisch, Deutsch, Niederländisch — sind eine Familie.*
**Entfesselt:** *Die germanischen Sprachen — das Englisch, das Deutsch, das Niederländisch — die sind eine Familie.*

**Attestation:** Universal in spoken German across all dialect regions. Standard in Bavarian, Alemannic, Rhineland, and Austrian speech. Also attested in MHG prose where long appositives intervene between subject and verb. Suppressed in written standard as "redundant" — but it serves a real parsing function: after a long interruption, the resumptive pronoun signals to the reader/listener that the main clause is resuming.

**Implementation:** Insert resumptive pronoun (*der/die/das/die* matching the original subject's gender/number) when more than ~5 words intervene between subject and verb. Not used for short parentheticals where the subject is still fresh in working memory.

### Rule 17: Perfekt over Präteritum

**What it restores:** Compound past tense (Perfekt) as the default narrative past tense.

**Standard Written German:** *Er definierte sich als König.* (simple past / Präteritum)
**Entfesselt:** *Er hat sich als König definiert.* (compound past / Perfekt)

**Standard Written German:** *Die Standardisierung unterdrückte diese Merkmale.* (Präteritum)
**Entfesselt:** *Die Standardisierung hat diese Merkmale unterdrückt.* (Perfekt)

**Attestation:** Spoken German overwhelmingly uses Perfekt for past narration across ALL dialect regions. The Präteritum in speech is largely restricted to a handful of high-frequency verbs: *war* (was), *hatte* (had), *wusste* (knew), *konnte* (could), *wollte* (wanted), *sollte* (should), *musste* (must), *durfte* (was allowed). For all other verbs, spoken German uses Perfekt. The Präteritum as a general narrative tense is a feature of written Standard German imposed by the prescriptive tradition — it maps to Latin's synthetic past tenses and to French *passé simple*. Southern German dialects (Bavarian, Alemannic, Swiss) have lost the Präteritum entirely for all verbs except *sein* (to be).

**Why this matters for the centroid:** English uses compound past freely ("he has defined himself"), as do Dutch, Scandinavian, and Yiddish. The Perfekt-preference brings German narration structurally closer to all its siblings.

**Implementation:** Default to Perfekt for past narration. Retain Präteritum only for the high-frequency verbs where it is natural in speech (*war, hatte, wusste, konnte, wollte, sollte, musste, durfte*). The LLM judges which verbs sound natural in Präteritum vs. Perfekt based on spoken German norms.

**Exceptions:** *sein* (to be) → *war* stays as Präteritum (universal even in dialect). Modal verbs (*können, wollen, sollen, müssen, dürfen*) → Präteritum stays. *haben* → *hatte* stays. All others default to Perfekt.

---

## Part III: Compound Curation Sub-Project

This section describes a separate, parallel project that refines compound splitting decisions made by the LLM. **It is not required for the main pipeline to operate.** The LLM makes all splitting decisions from day one using its own linguistic knowledge. The curation project codifies those decisions into a static lookup table for speed, consistency, and cases where the LLM's judgment can be improved by native-speaker review.

### How the LLM handles splitting without curation data

When processing a compound, the LLM:
1. Identifies the internal hierarchical structure
2. Identifies which 2-word sub-groupings are lexicalized (dictionary entries, common collocations)
3. Preserves those 2-word sub-compounds as fused units by default
4. Splits at the boundaries between sub-compounds
5. Applies fossil-first case restoration at each split joint
6. Logs the compound and its splitting decision to `compounds-for-curation.tsv`

This produces good output immediately. The LLM already knows that *Gesundheitsminister* is a real word and *Bundesgesundheits-* is not. It already knows that *Krankenhaus* should stay fused and *Krankenhausfinanzierungsregelungen* should split as *Krankenhaus Finanzierungs Regelungen*. These are not difficult decisions for an LLM with broad German training data.

### When curation adds value

The curation project adds value in three ways:
1. **Speed:** A static lookup table is faster than an LLM call for every compound
2. **Consistency:** The LLM might split the same compound differently in different contexts; the lookup table ensures identical treatment
3. **Edge cases:** Some compounds have genuinely ambiguous structure where native-speaker judgment outperforms the LLM

### Partial unfusing combinatorics

A compound with N elements can be unfused in multiple ways.

**3-element ABC: 3 options** (A B C, AB C, A BC)
**4-element ABCD: 7 options** (A B C D, AB C D, A BC D, A B CD, AB CD, ABC D, A BCD)

Not all semantically valid. Internal hierarchical structure constrains valid splits.

**Default: preserve lexicalized 2-word sub-compounds.** The LLM identifies which 2-word sub-groupings are dictionary entries and keeps those fused. The split happens at the boundary between sub-compounds, not inside them. This is the default behavior whether or not curation data exists.

Example: *Bundesgesundheitsminister* defaults to *Bundes Gesundheitsminister* (not *Bundes Gesundheits Minister*) because *Gesundheitsminister* is a dictionary entry.

### Curator voting workflow (when curation project is active)

1. Curators receive logged compounds from `compounds-for-curation.tsv`
2. LLM's default splitting is presented as the primary candidate
3. Alternative splittings (including full decomposition) are presented alongside
4. Curators vote independently; majority determines canonical entry in lookup table
5. Minority alternatives preserved as configurable variants (`--variant=minority`)

### Data value

Voting results are publishable psycholinguistic data on perceived phrase boundaries, lexicalization gradients, and compound processing. The voting database should be published openly as a research resource.

---

## Part IV: Target Texts

### Poetry Policy

Poetic texts are presented in **three-column format** (Standard | Entfesselt | English). The original is preserved in the Standard column and is never altered. The Entfesselt version serves as a comprehension aid alongside the original. Meter, rhyme, and alliteration are acknowledged as untouchable — they are too deeply embedded in the poetic structure to survive transformation without loss.

### Showcase Texts (approved)

**1. Grundgesetz Articles 1-19** (Fundamental Rights)
- Format: Three-column (Standard | Entfesselt | English)
- Purpose: Compound unfusing showcase on legal German
- Maximum compound density, bureaucratic stacking, verb-final clauses
- Public domain

**2. Communist Manifesto** (Marx & Engels, 1848)
- Format: Three-column (Standard | Entfesselt | English)
- Purpose: Full Entfesselt treatment on political prose — compounds + syntax
- ~12,000 words, manageable for proof of concept
- Peak prescriptive-era German, dense with exactly the features Entfesselt targets
- Public domain

**3. Kafka's *Die Verwandlung*** (The Metamorphosis, 1915)
- Format: Three-column (Standard | Entfesselt | English)
- Purpose: Literary showcase — demonstrates how prescriptive syntax creates "Kafkaesque" effect
- Shows what happens when you remove the oppressive syntactic features Kafka exploited as literary devices
- Public domain

**4. Grimm's Märchen** (selected tales)
- Format: Three-column (Standard | Entfesselt | English)
- Purpose: Pedagogical tool for German learners and children
- Short, famous, already used in every German classroom
- Public domain

**5. Thomas Mann's *Der Tod in Venedig*** (Death in Venice, 1912)
- Format: Three-column (Standard | Entfesselt | English)
- Purpose: Literary showcase for intermediate learners
- Mannered, elegant, long sentences — Entfesselt version reads like modern English-style novella
- Public domain

**6. Wagner's *Siegfried*** (libretto)
- Format: Three-column (Standard | Entfesselt | English)
- Purpose: Aesthetic showcase, "Vom Wagnerischem zu Waltherischem Deutsch"
- Poetic — original preserved intact in Standard column, Entfesselt as comprehension aid only
- Public domain

**7. Hitler's *Mein Kampf*** (selected chapters)
- **STATUS: DEFERRED.** Politically sensitive. Requires proper scholarly framing, institutional partnership, and the right cultural moment. Legally viable (public domain since 2016), educationally valuable (demonstrates that syntactic opacity has real-world consequences), but must be handled with appropriate scholarly apparatus. Will be revisited when the project has established credibility through other texts.

### Proposed Publication

Volume title: ***Entfesselt: Deutsche Texte, Befreit*** ("Unchained: German Texts, Liberated")

Initial volume contains Grundgesetz Articles 1-19, Communist Manifesto Chapter 1, and Kafka's *Die Verwandlung*. Introduction explains the project, linguistic principles, and historical argument about prescriptive standardization. Afterword invites German speakers to evaluate readability.

---

## Part V: The Inter-Germanic Centroid Project

Entfesselt is one component of a larger project to construct an Inter-Germanic centroid language — a synthetic language representing the structural center of the Germanic family, analogous to Interslavic for Slavic languages.

### Centroid Members

**Core Ingvaeonic (North Sea Germanic):**
- Anglo-Saxon / Old English
- Modern English
- Frisian (West Frisian)
- Scots (as data source, Northumbrian OE descendant)
- Plautdietsch / Mennonite Low German (Low German/Ingvaeonic, no HG consonant shift)

**North Germanic:**
- Old Norse
- Icelandic
- Danish
- Swedish
- Norwegian

**West Germanic (unfused):**
- German (Entfesselt form — unfused compounds, relaxed syntax)
- Dutch (unfused)
- Afrikaans (unfused)

**MHG-derived:**
- Yiddish (preserves MHG pre-stacking compound behavior, analytic extreme, lost genitive)

### Phonological Ranking: Closeness to English

Ranked by vowel and consonant shift distance only (ignoring grammar and vocabulary):

1. **Frisian** — Anglo-Frisian shared innovations (palatalization, nasal loss before fricatives). Closest living relative.
2. **Plautdietsch / Low German** — No HG consonant shift. Consonant inventory near-identical to English.
3. **Scots** — Sister language from same Northumbrian OE base. Vowel divergence, consonant near-identity.
4. **Dutch** — No HG consonant shift. Vowel system has Dutch-specific developments.
5. **Afrikaans** — Simplified Dutch phonology, some convergences toward English.
6. **Danish / Norwegian** — Reasonably close consonants, but stød/tonal accent absent in English.
7. **Swedish** — Similar to Danish/Norwegian, pitch accent adds distance.
8. **Icelandic** — Conservative consonants map to OE, but vowel and aspiration differences.
9. **Yiddish** — HG consonant shift (p→pf, t→ts). Slavic contact softened some sounds.
10. **Standard German** — HG consonant shift is maximum phonological divergence from English in the family.

This ranking informs vocabulary weighting: phonologically closer languages contribute proportionally more to the centroid's lexical inventory.

### The Unfusing Constraint

All languages with recursive compound stacking (German, Dutch, Afrikaans, Swedish to a degree) participate in the centroid only in unfused form. This collapses what appeared to be a major typological split into a surface representation difference. With everyone unfused, the entire family operates on the same principle: two-element modification with relational markers, sequenced left-to-right, head-final within each pair.

Note: Scandinavian compound stacking is itself a medieval import. Old Norse was strictly two-element. Longer compounds entered Swedish, Danish, and Norwegian through Low German influence during the Hanseatic period (13th-15th centuries), when Low German-speaking merchants and administrators brought continental compounding patterns into Scandinavian administrative and commercial language. The linking morphemes (-s-, -e-, -er-) in Danish and Swedish parallel the German Fugenlaute and likely derive from the same contact. Unfusing Scandinavian compounds is therefore not just removing a surface convention — it is reversing a medieval German import and restoring the original Old Norse pattern.

### How Entfesselt Brings German Closer to Each Centroid Member

This is the core argument of the project as a position paper. Every Entfesselt transformation restores a feature that brings Standard German closer to one or more of its sister languages — and in most cases, closer to the reconstructed Proto-Germanic or attested common ancestor (Old Norse, Anglo-Saxon). The prescriptive standardization of German artificially increased the distance between German and the rest of the family. Entfesselt reverses that increase.

**Old Norse (the deep anchor):**
Old Norse is the best-attested early Germanic language and the closest proxy for Proto-North/West Germanic structural patterns. Entfesselt brings German closer to Old Norse in every dimension:
- **Compounds:** Old Norse used strictly two-element compounds with live case morphology at joints (*konungs-garðr* with real genitive -s). Entfesselt restores exactly this pattern — two-element sub-compounds with fossil or restored case morphology.
- **Verb position:** Old Norse had flexible verb position, including verb-second in subordinate clauses. The rigid verb-final subordinate clause is a later German innovation. Entfesselt's verb position relaxation restores ON-era flexibility.
- **Case morphology at compound joints:** In Old Norse, compounds and phrases used the same case system — no separate compound-internal grammar. Entfesselt eliminates the German split between compound morphology and phrasal morphology, restoring the ON unity.
- **Do-support:** Old Norse used *gera* (do/make) as a periphrastic auxiliary in some constructions. The *tun*-periphrasis Entfesselt restores has cognate roots.
- **Double negation:** Old Norse used reinforcing negation freely (*eigi...ekki*). Entfesselt's double negation restoration parallels ON usage.

**Anglo-Saxon / Old English (the sister anchor):**
Anglo-Saxon and Old Norse share the deepest structural parallels in the family. Entfesselt brings German closer to OE in ways that reveal their common West Germanic inheritance:
- **Compounds:** OE compounds were two-element with transparent case relationships, exactly as Entfesselt restores for German. OE *cynestōl* (king-seat = throne) parallels Entfesselt *Königs Stuhl*.
- **Kennings vs. stacking:** OE used poetic kennings (metaphorical two-element substitutions), never recursive noun stacking. Entfesselt's compound policy matches the OE pattern.
- **Progressive aspect:** OE had a progressive construction (*ic wæs gangende* = I was going). The *am* + infinitive Entfesselt restores is the German cognate of a construction both OE and Modern English share.
- **Do-support:** OE used *dōn* as a periphrastic auxiliary. English preserved and expanded this into full do-support. German's *tun*-periphrasis is the exact cognate, suppressed by prescriptivists. Entfesselt restores it.

**Modern English:**
English is the centroid member that diverged most from Standard German — but much of that divergence is artificial, created by the prescriptive standardization of German rather than by natural drift. Entfesselt closes the gap dramatically:
- **Compound decomposition:** Entfesselt noun phrases are structurally identical to English noun phrases. "Beef labeling supervision duties transfer law" = *Rindfleisches Etikettierungs Überwachungs Aufgaben Übertragungs Gesetz*.
- **Verb position:** Entfesselt verb-second in subordinate clauses matches English word order (*I know that he HAS gone home* vs. Standard German *dass er nach Hause gegangen IST*).
- **Do-support:** English *do you understand?* = Entfesselt *tust du das verstehen?*
- **Progressive:** English *I am working* = Entfesselt *Ich bin am Arbeiten*.
- **Prepositional possession:** English *the house of my father* = Entfesselt *das Haus von meinem Vater*.
- **Double negation:** Colloquial English still uses reinforcing double negation (*I don't know nothing*); Entfesselt restores the same pattern in German.

**Frisian:**
As the closest living relative to English, Frisian shares the Ingvaeonic innovations. Entfesselt brings German closer to Frisian by:
- **Removing the compound barrier:** Frisian compounds are short, transparent, and use live case/prepositional syntax. Entfesselt matches this.
- **Case simplification:** Modern West Frisian collapsed to two genders (common/neuter) and lost most case morphology except genitive -s. Entfesselt's *von*-restoration moves German possession marking toward the Frisian/English analytic pattern.

**Plautdietsch / Low German:**
Low German never underwent the High German consonant shift and preserves Ingvaeonic features. Entfesselt brings Standard German structurally closer to Low German by:
- **Removing the compound stacking** that Low German uses less aggressively than High German.
- **Restoring *tun*-periphrasis,** which Low German uses freely (*Ik do dat verstahn*).
- **Permitting double negation,** which Low German preserves.
- **Relaxing verb position,** which is more flexible in Low German subordinate clauses than in Standard German.

**Dutch:**
Dutch underwent compound fusion similar to German but less extreme. Entfesselt brings German closer to Dutch by:
- **Compound decomposition** reduces German compound length toward Dutch norms.
- **Progressive aspect:** Dutch has *aan het werken zijn* — structurally identical to Entfesselt *am Arbeiten sein*. Both languages now share the construction that Standard German suppresses.
- ***Von*-restoration:** Dutch uses *van* for possession exactly as Entfesselt uses *von*.
- **Articles with names:** Dutch uses *de Jan, de Maria* in colloquial speech, paralleling Entfesselt *der Hans, die Maria*.

**Afrikaans:**
Afrikaans is the most analytically simplified Germanic language. Entfesselt brings German closer to Afrikaans by:
- **Double negation:** Afrikaans *Ek het nie geld nie* (I have not money not) directly parallels Entfesselt's restored double negation.
- **Analytic possession:** Afrikaans uses *se* and *van* rather than synthetic genitive. Entfesselt's *von*-restoration moves in the same direction.
- **Compound decomposition:** Afrikaans compounds, though fused, tend to be shorter than German. Entfesselt normalizes German compound length downward.

**Danish / Norwegian / Swedish:**
The Scandinavian languages descended from Old Norse and share its structural conservatism in some areas while having developed compound stacking through German contact. Entfesselt brings German closer to Scandinavian by:
- **Compound length normalization:** Scandinavian compounds rarely exceed 3-4 elements. Entfesselt caps German at the same level.
- **Progressive aspect:** Scandinavian languages have progressive constructions (*holder på å arbeide* in Norwegian). Entfesselt's progressive restoration brings German into alignment.
- **Flexible verb position:** Scandinavian subordinate clause verb position is more flexible than Standard German's rigid verb-final rule.

**Icelandic:**
Icelandic preserves Old Norse structure most faithfully. Entfesselt brings German closer to Icelandic by:
- **Compound-phrasal unity:** Icelandic, like Old Norse, uses the same case system inside and outside compounds. Entfesselt restores this unity for German.
- **Two-element compound limit:** Icelandic compounds are overwhelmingly two-element (modern neologisms sometimes reach three). Entfesselt matches this.
- **Archaic case preservation:** Entfesselt's fossil-first principle preserves archaic case forms that are *closer to Icelandic's living case system* than Modern German's phrasal syntax is.

**Yiddish:**
Yiddish descended from MHG and preserves pre-stacking compound behavior. Entfesselt brings German closer to Yiddish by:
- **Two-element compound limit:** Yiddish never developed recursive stacking. Entfesselt matches this.
- **Dative-possessive:** Yiddish uses *dem tatn zayn hoyz* (the father his house) — structurally identical to Entfesselt *dem Vater sein Haus*.
- **Analytic case expression:** Yiddish lost the genitive case and uses prepositional constructions. Entfesselt's *von*-restoration moves German in the same direction Yiddish went naturally.
- **Flexible verb position:** Yiddish does not enforce verb-final in subordinate clauses. Entfesselt's verb position relaxation brings German closer to the Yiddish pattern.

**Scots:**
Scots descends from Northumbrian OE and shares the Ingvaeonic innovations with English and Frisian. Entfesselt brings German closer to Scots by:
- **All the same convergences as with English,** plus:
- **Preserved ON/OE vocabulary:** Where Scots retains ON/OE words that Standard English lost (*bairn, kirk, ken*), Entfesselt German's archaic case forms often map more cleanly to these than to Standard English equivalents.

### The common pattern

Every transformation in Entfesselt moves German closer to multiple centroid members simultaneously. This is not coincidence — it reflects the underlying thesis: the prescriptive standardization of German *systematically* increased its distance from the rest of the Germanic family. Each suppressed feature was one that German shared with its siblings. Removing the suppression reveals the family resemblance that was always there.

The convergence is strongest at the deep level — Old Norse and Anglo-Saxon — because the Entfesselt transformations restore features from the period before the Germanic languages diverged as far as they have today. By reverting German toward its MHG/OHG state in targeted ways, Entfesselt finds the structural common ground that the entire family shares.

### Future application: Entfesselung of other Germanic languages

The methodology developed for German Entfesselung can be applied to any Germanic language that underwent similar prescriptive standardization or contact-driven structural borrowing:

- **Dutch Entfesselung:** Unfuse compounds, restore dialectal features suppressed by ABN (Algemeen Beschaafd Nederlands) standardization.
- **Swedish/Danish/Norwegian Entfesselung:** Unfuse compounds (reversing medieval German influence), restore ON-era patterns where attested in dialect or historical text.
- **Nynorsk as precedent:** Norwegian Nynorsk already represents a partial Entfesselung — Ivar Aasen constructed it in the 19th century by surveying rural dialects to recover pre-Danish features. The Entfesselt methodology formalizes and extends this approach.

---

## Implementation Architecture

```
Input German Text
       │
       ▼
┌─────────────────────┐
│  TOKENIZER / PARSER   │  spaCy de_core
│                       │  POS tagging, dependency parse
│                       │  Clause structure identification
└────────┬──────────────┘
         │
         ▼
┌─────────────────────┐
│ COMPOUND SPLITTER     │  CharSplit / SMOR / dictionary
│                       │  Decompose nouns into morphemes
│                       │  Identify Fugenlaute
└────────┬──────────────┘
         │
         ▼
┌─────────────────────┐
│ LLM COMPOUND         │  LLM determines splitting points
│ SPLITTING             │  Preserves 2-word sub-compounds
│ (Claude API)          │  Applies fossil-first case restoration
│                       │  Logs ≤4 compounds to curation file
└────────┬──────────────┘
         │
         ▼
┌─────────────────────┐
│ CURATION TABLE        │  IF curation data available:
│ OVERRIDE (optional)   │  Override LLM decisions with curated entries
│                       │  Otherwise: LLM decisions pass through
└────────┬──────────────┘
         │
         ▼
┌─────────────────────┐
│ SYNTACTIC             │  LLM-powered (Claude API)
│ ENTFESSELUNG          │  Verb position relaxation
│                       │  Von-restoration
│                       │  Progressive aspect
│                       │  Tun-periphrasis
│                       │  Dative-possessive
│                       │  Double negation
│                       │  Articles with proper names
│                       │  Resumptive pronouns
│                       │  Perfekt over Präteritum
└────────┬──────────────┘
         │
         ▼
┌─────────────────────┐
│ OUTPUT FORMATTER      │  Reassemble sentence
│                       │  Capitalization, spacing
│                       │  Punctuation preservation
└─────────────────────┘
         │
         ▼
  Entfesselt German Text
```

**Note on architecture:** The LLM (Claude API) is the primary engine for all decisions — compound splitting, sub-compound preservation, case restoration, and syntactic transformations. The compound splitter tools (CharSplit, SMOR) serve as preprocessors that identify compound candidates and morpheme boundaries, but the LLM makes the final splitting decisions. The curation table, when available, overrides the LLM's compound decisions for consistency and speed, but the system produces good output without it.

### Processing Modes

**Mode A: Compound-only** (ships immediately, LLM handles all decisions)
- Compound unfusing: LLM splits >4 element compounds, preserving 2-word sub-compounds
- LLM also handles ≤4 element compounds it judges would benefit from splitting
- Fossil-first case restoration at all split joints
- No syntactic transformations
- Logs all compound decisions to `compounds-for-curation.tsv`

**Mode B: Compound + Curation overrides** (ships when curation data available)
- Same as Mode A, but curation table overrides LLM's compound decisions where entries exist
- Ensures consistency across documents for curated compounds
- LLM still handles all uncurated compounds

**Mode C: Full Entfesselt** (all transformations enabled)
- All compound handling from Mode A/B
- All syntactic transformations (Rules 9-17)
- Full Waltherian output
- This is the mode used for the target text publications

### Configuration flags:

```
--mode A|B|C
--articles          Insert articles at unfused joints (default: off for A, on for B/C)
--classifier        genitive-only | full (default: genitive-only for A, full for B/C)
--curation-table    Path to Bin A/B/C lookup (required for B/C)
--verb-position     Allow verb-second in subordinate clauses (Mode C)
--von-restoration   Prefer von + dative (Mode C)
--progressive       Allow am + infinitive (Mode C)
--tun-support       Allow tun-periphrasis (Mode C)
--dative-possessive Allow dem X sein Y (Mode C)
--double-negation   Allow reinforcing double negation (Mode C)
--name-articles     Insert articles before proper names (Mode C)
--resumptive        Insert resumptive pronouns after long parentheticals (Mode C)
--perfekt           Prefer Perfekt over Präteritum for past narration (Mode C)
--variant           majority | minority (for curator voting alternatives)
```

---

## Dependencies and Resources

### Required for Mode A:
- German noun gender dictionary (Wiktionary dump or LanguageTool morphdb)
- German noun declension tables (full paradigms)
- Compound splitter (CharSplit recommended)

### Required for Mode B:
- Everything from Mode A, plus curation table and LLM API for relationship classification

### Required for Mode C:
- Everything from Mode B, plus full syntactic parsing (spaCy de_core) and LLM API for syntactic transformations

### Historical linguistic resources:
- Lexer's Mittelhochdeutsches Handwörterbuch
- Köbler's Althochdeutsches Wörterbuch
- Grimm's Deutsches Wörterbuch
- Georg Wenker's Sprachatlas / Digitaler Wenker-Atlas (dialect attestations)

---

## Evaluation Criteria

### For native German speakers:
1. Is the output intelligible without explanation?
2. Does it read as valid (if informal/archaic) German?
3. How natural does it feel? (1-5 scale)
4. Which transformations improve readability? Which feel forced?

### For English speakers learning German:
1. Can you identify individual words and their relationships?
2. Is this easier to read than standard German?
3. Does word order feel more natural?
4. Does the progressive / do-support feel familiar?

### For the centroid project:
1. Does Entfesselt German structurally align with English noun phrases?
2. Does it align with unfused Dutch / Scandinavian?
3. Can a single Inter-Germanic grammar cover both forms?

---

## Future Extensions

1. **≤4-element curation expansion.** Community-driven. Target: 15,000+ compounds curated within first year.

2. **Dutch Entfesselung.** Same compound pipeline. Dutch case system is simpler; restoration uses prepositional phrases.

3. **Scandinavian Entfesselung.** Lighter-touch. Bureaucratic/technical compounds only.

4. **Cross-Germanic alignment.** Parallel Entfesselt texts across German, Dutch, Scandinavian. Measure structural convergence. Feed into centroid project.

5. **Bidirectional tool.** Entfesselt → Standard German. Learners practice compound formation.

6. **Browser extension.** Real-time Entfesselung of German websites. Mode A/B/C configurable. Hover tooltips showing original form.

7. **LLM curation assistant.** Dedicated tool for compound curation. Transparency scoring, bin assignment, curator voting interface.

8. **Deferred: *Mein Kampf* critical edition.** When project has established credibility. Scholarly framing, institutional partnership required.
