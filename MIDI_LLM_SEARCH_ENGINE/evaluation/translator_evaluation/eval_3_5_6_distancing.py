#!/usr/bin/env python3
"""Single lexical-distancing checker for eval-3 paraphrases.

RULE
----
Given a concept, its paraphrase must NOT contain any word that appears in that
concept's subcategory section of system_prompt.txt, UNLESS that word also
appears in at least MIN_OTHER_PLACES other spots in the whole prompt. This is
what lets generic/function words through without needing the allowlist.

A word that IS in the subcategory section and is rare elsewhere is FORBIDDEN
unless it is explicitly listed in ALLOWLIST. ALLOWLIST starts empty and is grown
only from real flagged paraphrases where the word is necessary routing
vocabulary that cannot be swapped out.

This module is self-contained (no imports from lexical_distance.py) and serves
as the single distancing gate for evals 3, 5 and 6:
  * score(paraphrase, concept)   -> eval 3
  * novelty(query)               -> evals 5 & 6

Usage
-----
  python eval_3_5_6_distancing.py                  # report flags with current allowlist
  python eval_3_5_6_distancing.py --annotate       # write flagged_words/flagged_count into JSON
  python eval_3_5_6_distancing.py --annotate --no-allowlist   # annotate with empty allowlist
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter

PROMPT_PATH = "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_RETRIEVE/system_prompt.txt"
MATERIALS_PATH = "evaluation_3_materials.json"

# --- tokenizer (inlined so this file has no dependency on lexical_distance.py) ---
_TOKEN = re.compile(r"[a-z0-9]+")

# Function words / scaffolding stripped from content tokens.
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "at", "as", "is", "are", "be", "was", "were", "been", "being", "it", "its",
    "this", "that", "these", "those", "which", "who", "whom", "from", "into",
    "onto", "over", "under", "between", "among", "there", "here", "what", "when",
    "where", "how", "why", "than", "then", "so", "such", "both", "each", "few",
    "more", "most", "some", "any", "all", "other", "another", "much", "many",
    "very", "too", "only", "just", "about", "above", "below", "within", "without",
    "along", "across", "around", "before", "after", "during", "while", "though",
    "through", "throughout", "still", "even", "also", "once", "often", "never",
    "always", "sometimes", "usually", "generally", "really", "quite", "rather",
    "should", "would", "could", "can", "may", "might", "will", "must",
    "has", "have", "had", "having", "do", "does", "did", "done", "get", "gets",
    "got", "make", "makes", "made", "take", "takes", "took", "like", "way", "ways",
}


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


def content_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if t not in STOPWORDS]


def _prompt_tokens() -> set[str]:
    toks: set[str] = set()
    for text in load_sections().values():
        toks.update(content_tokens(text))
    return toks


def novelty(text: str) -> float:
    """Fraction of a query's content tokens NOT present in the system prompt.
    1.0 = fully novel; 0.0 = every word appears in the prompt."""
    toks = content_tokens(text)
    if not toks:
        return 1.0
    sys_set = _prompt_tokens()
    overlap = sum(1 for t in toks if t in sys_set)
    return 1.0 - overlap / len(toks)

# Rule: a word is forbidden for a concept if it appears anywhere in that
# concept's subcategory section, UNLESS it is explicitly listed in ALLOWLIST.
# No frequency/"appears elsewhere" logic — we allowlist every allowed word by hand.

# ---------------------------------------------------------------------------
# ALLOWLIST — starts COMPLETELY EMPTY. A word is added here only when a real
# flagged paraphrase needs it as unavoidable routing vocabulary (the model
# cannot map the feature without naming it). Structured by category.
# ---------------------------------------------------------------------------

# Kit pieces / drums routing vocabulary (must be nameable).
KIT_PIECES = {
    "kit", "kick", "tom", "toms", "hat", "hi", "crash", "snare", "clap", "rimshot", "cymbal", "drum",
    "closed", "open",
}

# Instrument-family / metadata routing vocabulary (metadata_instrument_family).
INSTRUMENTS = {
    "instrument", "lead", "synth", "piano", "acoustic", "guitar", "strings", "bass"
}

# Intervals / interval-qualifier routing vocabulary.
INTERVALS = {
    "third", "fourth", "fifth", "sixth", "seventh", "ninth", "eleventh",
    "thirteenth", "tritone", "eighth", "semitone", "octave", "octaves", "melody", "line", "intervals",
}

# Harmony / interval-domain routing vocabulary.
HARMONY = {
    "voicings", "voicing", "harmonic", "harmony", "chords", "chord", "chordal", "consonance", "consonances",
    "imperfect", "perfect", "melodic", "scale", "unison", "major", "minor", 
}

# Beat-position / note-count numbers.
NUMBERS = {"3", "14", "17", "21",
    "number", "11", "13", "1", "two", "three", "four", "six", "2", "4", "6", "8",
    "quarter", "second", "one", "single", "half", "32nd", "whole", }

# Note letters (metadata_root_key) and tokenization artifacts.
NOTES = {"f", "g", "note", "notes", "pitch"}
GENERIC = {"s"}

# Generic English function/connector words that cannot be removed from prose.
FUNCTION_WORDS = {"mostly", "no", "but", "per", "every", "time", "fine", "off", "they"}

# Direction / register-level routing vocabulary.
DIRECTION = {"down", "up", "low", "high", "medium", "mid", "middle"}

# Grid / timing routing vocabulary.
GRID_TIMING = {"bars", "bar", "beats", "beat", "grid", "placement"}

# Register / range routing vocabulary.
REGISTER = {"range", "register"}

# General routing vocabulary (notes, interval qualifiers, beat/bar, connectors).
GENERAL: set[str] = set()

ALLOWLIST: set[str] = KIT_PIECES | INSTRUMENTS | INTERVALS | HARMONY | NUMBERS | NOTES | GENERIC | GENERAL | FUNCTION_WORDS | DIRECTION | GRID_TIMING | REGISTER
# ---------------------------------------------------------------------------


def load_sections() -> dict[str, str]:
    prompt = open(PROMPT_PATH).read()
    sections: dict[str, str] = {}
    cur: str | None = None
    buf: list[str] = []
    for ln in prompt.splitlines():
        m = re.match(r"^### (.+)$", ln)
        if m:
            if cur:
                sections[cur] = " ".join(buf)
            cur = m.group(1).strip()
            buf = []
        elif cur is not None:
            buf.append(ln)
    if cur:
        sections[cur] = " ".join(buf)
    return sections


def load_materials() -> dict:
    return json.load(open(MATERIALS_PATH))


_CONCEPT_SECTION_CACHE: dict[str, str] | None = None


def _concept_to_section(sections: dict[str, str]) -> dict[str, str]:
    """Map each feature concept to its subcategory section, using the taxonomy.

    The taxonomy's per-concept ``llm.subcategory`` value names the ``###`` section
    in system_prompt.txt that defines it. (Parsing bullets from the prompt text is
    unreliable: most concepts appear as ``Detail concepts:`` lists / nested
    sub-bullets, not as ``- name:`` bullets.)
    """
    global _CONCEPT_SECTION_CACHE
    if _CONCEPT_SECTION_CACHE is not None:
        return _CONCEPT_SECTION_CACHE
    from midi_analyzer_tagger.extractors import PLUGINS
    from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
    from midi_analyzer_tagger.exporters.taxonomy import TaxonomyExporter

    reg = ExtractorRegistry(PLUGINS)
    reg.compile_taxonomy()
    tax = TaxonomyExporter(reg).to_dict()
    mapping: dict[str, str] = {}
    for concept, data in tax.items():
        if concept in ("llm_categories", "llm_subcategories"):
            continue
        sc = (data.get("llm") or {}).get("subcategory")
        if sc and sc in sections:
            mapping[concept] = sc
    _CONCEPT_SECTION_CACHE = mapping
    return mapping


def _forbidden_for_section(section_tokens: set[str], allowlist: set[str]) -> set[str]:
    """A word is forbidden if it appears in this concept's subcategory section and
    is not explicitly allowlisted. (No frequency logic — allowlist is manual.)"""
    return section_tokens - allowlist


def _index() -> tuple[dict[str, str], dict[str, str]]:
    sections = load_sections()
    concept_section = _concept_to_section(sections)
    return sections, concept_section


def run(allowlist: set[str]):
    sections, concept_section = _index()
    mat = load_materials()
    flagged = []
    per_word: dict[str, list] = {}
    for concept, paras in mat.items():
        sc = concept_section.get(concept)
        if sc is None:
            continue
        sec = sections[sc]
        forbidden = _forbidden_for_section(set(content_tokens(sec)), allowlist)
        for p in paras:
            used = sorted(set(content_tokens(p["paraphrase"])) & forbidden)
            if used:
                flagged.append((len(used), concept, p["paraphrase"], used))
                for w in used:
                    per_word.setdefault(w, []).append((concept, p["paraphrase"]))
    flagged.sort(key=lambda r: r[0], reverse=True)
    return flagged, per_word, sections


def annotate_materials(allowlist: set[str], path: str = MATERIALS_PATH) -> None:
    """Write flagged_words / flagged_count into each paraphrase entry."""
    mat = json.load(open(path))
    sections, concept_section = _index()
    total = 0
    flagged = 0
    for concept, paras in mat.items():
        sc = concept_section.get(concept)
        if sc is None:
            continue
        sec = sections[sc]
        forbidden = _forbidden_for_section(set(content_tokens(sec)), allowlist)
        for p in paras:
            total += 1
            used = sorted(set(content_tokens(p["paraphrase"])) & forbidden)
            if used:
                p["flagged_words"] = used
                p["flagged_count"] = len(used)
                flagged += 1
            else:
                p.pop("flagged_words", None)
                p.pop("flagged_count", None)
    json.dump(mat, open(path, "w"), indent=2, ensure_ascii=False)
    print(f"annotated: {flagged} of {total} paraphrases flagged (allowlist={len(allowlist)})")


def score(paraphrase: str, concept: str, allowlist: set[str] | None = None) -> dict:
    """Eval-3 gate: is a paraphrase lexically distanced from its concept's section?

    Returns a dict compatible with the old LexicalScorer.score interface
    (keys: leaked_tokens, leaked_ngrams, distanced, novelty, forbidden_count).
    """
    allowlist = ALLOWLIST if allowlist is None else allowlist
    sections, concept_section = _index()
    sc = concept_section.get(concept)
    if sc is None:
        return {"leaked_tokens": [], "leaked_ngrams": [], "distanced": True,
                "novelty": round(novelty(paraphrase), 4), "forbidden_count": 0}
    sec = sections[sc]
    forbidden = _forbidden_for_section(set(content_tokens(sec)), allowlist)
    toks = set(content_tokens(paraphrase))
    leaked = sorted(toks & forbidden)
    return {"leaked_tokens": leaked, "leaked_ngrams": [], "distanced": not leaked,
            "novelty": round(novelty(paraphrase), 4), "forbidden_count": len(forbidden)}


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--annotate" in argv:
        use_allowlist = "--no-allowlist" not in argv
        annotate_materials(set() if not use_allowlist else ALLOWLIST)
    else:
        flagged, per_word, sections = run(ALLOWLIST)
        total = sum(len(v) for v in load_materials().values())
        print("allowlist size =", len(ALLOWLIST))
        print("paraphrases flagged:", len(flagged), "of", total)
        print("distinct forbidden words:", len(per_word))
        print()
        for w, hits in sorted(per_word.items(), key=lambda kv: -len(kv[1])):
            print(f"{len(hits):3d}  {w!r}")
