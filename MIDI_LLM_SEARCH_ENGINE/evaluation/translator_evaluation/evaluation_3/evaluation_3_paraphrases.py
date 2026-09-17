#!/usr/bin/env python3
"""Test 3 — Fused single + combo paraphrase validation.

Fuses single-paraphrase and paraphrase-combo validation into one script driven
by ``evaluation_3_materials.json``.

Material format: ``{concept: [{paraphrase, direction}, ...]}`` where ``direction``
is coarse (high/mid/low/unknown).

- Single trials: each active concept uses one paraphrase; the model must route to
  that concept. Grid attempt/success are excluded here.
- Grid-pair trials: grid-attempt entries in the material that carry a
  ``pair_direction`` express a combined query stating BOTH the grid attempt and
  success levels (e.g. 'hit consistently and land tight'); the model must return
  both concepts at those levels. All 4 level combos are represented in the material.
- Combo trials: N concepts each contribute one paraphrase, joined by ", "; the
  model must return ALL expected concepts (presence check, extras OK).

Two signals are recorded per trial:
- ``success`` — presence of every expected concept (primary).
- ``direction`` — for each expected concept with a non-``unknown`` direction,
  the returned level is bucketed to high/mid/low by its position in the
  taxonomy's intensity-ordered levels and compared to the expected direction.
  Reported separately (a direction miss does not fail the presence check).

EVERYTHING the LLM emits is logged per trial: the raw model output, the
validated translation (family classification, semantic
analysis, all targets with concept/level/importance/fallback, excluded
concepts), and call metadata (provider, model, token counts, response time).

Per family (drums / pitched). ``metadata_instrument_family`` paraphrases are
filtered by the selected family so the query never contradicts the family hint.
Fully parallel, checkpoint-resumable, deterministic trial construction.
"""
from __future__ import annotations

import json
import math
import random
import re
import shutil
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

_ANALYSER_SRC = Path(__file__).resolve().parents[4] / "MIDI_ANALYZER_TAGGER" / "src"
if str(_ANALYSER_SRC) not in sys.path:
    sys.path.insert(0, str(_ANALYSER_SRC))
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from _logging import log_call
from midi_llm_search_engine.config import get_api_key
from midi_llm_search_engine.index_loader import SearchIndex
from midi_llm_search_engine.llm_client import LLMTranslator
from midi_analyzer_tagger.storage.sqlite import AnalysisDatabase
from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.exporters.taxonomy import TaxonomyExporter
from midi_analyzer_tagger.extractors import PLUGINS

import eval_3_5_6_distancing as distancing

SEED = 42
CONCURRENCY = 20
CHECKPOINT = Path(__file__).resolve().parent / ".evaluation_3_checkpoint.json"

MATERIAL = Path(__file__).resolve().parent / "evaluation_3_materials.json"

# Combos per size 1-10, tapered to establish a paraphrase-routing degradation
# curve (literal scaling is covered by test1/test2). Kept modest at large sizes
# since paraphrases are harder to route than literal tags.
COMBO_BATCHES = [
    (2, 20), (3, 16), (4, 14), (5, 12),
    (6, 10), (7, 8),  (8, 6),  (9, 5),  (10, 4),
]

# Only one kit-piece prevalence per drum family + the family-level prevalence is
# tested (4 pieces + 1 family). The rest are redundant and skipped to save cost.
KEEP_PREVALENCE = {
    "drum_prevalence_kick_kick_1",          # kick family piece
    "drum_prevalence_snare_clap_snare_1",   # snare/clap family piece
    "drum_prevalence_hats_cymbals_crash_1", # hats/cymbals family piece
    "drum_prevalence_toms_others_high_tom", # toms/others family piece
    "drum_prevalence_toms_others",          # family-level prevalence
}

# Combo sizes used for the distributed coverage guarantee (spread across sizes).
COVER_SIZES = [3, 4, 5, 6, 7, 8]

# metadata_instrument_family applies to both families; its paraphrases must be
# family-specific to avoid contradicting the family hint. Direction is
# non-directional (unknown) for metadata_* concepts.
FAMILY_SPECIFIC_PARAPHRASES = {
    "metadata_instrument_family": {
        "drums": [{"paraphrase": "a drum kit", "direction": "unknown"}],
        "pitched": [
            {"paraphrase": "instrument reads as a keyboard", "direction": "unknown"},
            {"paraphrase": "a synth solo voice", "direction": "unknown"},
            {"paraphrase": "a bass instrument", "direction": "unknown"},
            {"paraphrase": "piano", "direction": "unknown"},
            {"paraphrase": "acoustic guitar", "direction": "unknown"},
            {"paraphrase": "strings", "direction": "unknown"},
        ],
    },
}


# Appended to drum-family queries so the model knows a "piece: " prefix scopes
# that segment to a specific kit piece family (only in this test, not the system
# prompt).
DRUM_PREFIX_NOTE = (
    "\n\nNote: In the query above, any segment prefixed by 'kick: ', 'snare/clap: ', "
    "'hats/cymbals: ', or 'toms: ' refers to that specific kit piece family. Route "
    "each such segment to the drum concept for that kit piece."
)

# Appended to pitched-family queries so the model knows a "pitched: " prefix scopes
# that segment to the pitched (non-drum) family.
PITCHED_PREFIX_NOTE = (
    "\n\nNote: In the query above, any segment prefixed by 'pitched: ' refers to the "
    "pitched (non-drum) family. Route it to the general pitched concept, not a drum "
    "kit-piece variant."
)


def _with_prefix_note(prompt: str, family: str) -> str:
    if family == "drums":
        return prompt + DRUM_PREFIX_NOTE
    if "pitched: " in prompt:
        return prompt + PITCHED_PREFIX_NOTE
    return prompt


def _active_concepts(tax: dict, material: dict, family: str) -> list[str]:
    """Concepts in the material that apply to ``family``."""
    result = []
    for cname in material:
        if cname.startswith("__") or cname in ("llm_categories", "llm_subcategories"):
            continue
        data = tax.get(cname, {})
        w = data.get("base_weight", data.get("default_weight", 1.0))
        if not w:
            continue
        fams = data.get("llm", {}).get("instrument_family", [])
        if isinstance(fams, str):
            fams = [fams]
        if family not in fams:
            continue
        result.append(cname)
    # Keep only the chosen prevalence concepts (drop redundant kit-piece prevalences).
    result = [c for c in result if "prevalence" not in c or c in KEEP_PREVALENCE]
    return sorted(result)


def _paraphrases_for(material: dict, concept: str, family: str) -> list[dict]:
    spec = FAMILY_SPECIFIC_PARAPHRASES.get(concept)
    if spec:
        return spec[family]
    return material.get(concept, [])


def _level_bucket(taxonomy: dict, concept: str, level_name: str) -> str | None:
    """Bucket a returned level into coarse high/mid/low by its position in the
    taxonomy's intensity-ordered ``levels`` (index 0 = most intense).

    Bucket boundaries by thirds so 3+ level concepts get a mid band:
      n=2: high={0}, low={1}
      n=3: high={0}, mid={1}, low={2}
      n=4: high={0}, mid={1,2}, low={3}
      n=5: high={0}, mid={1,2,3}, low={4}
      n=6: high={0,1}, mid={2,3}, low={4,5}
    """
    levels = (taxonomy.get(concept, {}).get("llm") or {}).get("levels") or []
    idx = None
    for i, lv in enumerate(levels):
        if len(lv) > 1 and lv[1] == level_name:
            idx = i
            break
    if idx is None:
        return None
    n = len(levels)
    if n <= 1:
        return None
    if n == 2:
        return "high" if idx == 0 else "low"
    k = n // 3
    if idx < k:
        return "high"
    if idx >= n - k:
        return "low"
    return "mid"


# Semantic opposites that must never share a combo (a single melody can't assert
# a dominant direction that is both ascending and descending).
CONFLICT_PAIRS = frozenset({
    frozenset({"melodic_intervals_pct_ascending", "melodic_intervals_pct_descending"}),
})


def _has_conflict(combo, conflicts=CONFLICT_PAIRS) -> bool:
    cset = set(combo)
    return (any(pair <= cset for pair in conflicts)
            or _has_share_conflict(combo)
            or _has_melodic_direction_conflict(combo)
            or _has_duration_profile_conflict(combo)
            or _has_texture_voicing_conflict(combo)
            or _has_melodic_agg_specific_conflict(combo))


_DURATION_PROFILES = {"duration_short_profile", "duration_medium_profile", "duration_long_profile"}


def _has_duration_profile_conflict(combo) -> bool:
    """A part has one dominant duration character; two profiles (short/medium/long)
    in the same combo are contradictory."""
    return sum(1 for c in combo if c in _DURATION_PROFILES) >= 2


def _has_texture_voicing_conflict(combo) -> bool:
    """Multiple vertical note-count bins assert different dominant voicing
    densities (e.g. 'single-note is the norm' + 'six or more ring together'),
    which is a subjective mixture — avoid it."""
    return sum(1 for c in combo if re.match(r"texture_pct_.*_notes$", c)) >= 2


def _has_melodic_agg_specific_conflict(combo) -> bool:
    """Combining the aggregate direction with a specific directional interval is
    redundant and prone to contradiction (e.g. 'rarely moves upward' + 'jumps up
    by major seventh')."""
    agg = {"melodic_intervals_pct_ascending", "melodic_intervals_pct_descending"}
    has_agg = bool(agg & set(combo))
    has_specific = any(re.match(r"profile_melodic_intervals_pct_(?:asc|desc)_\d+", c) for c in combo)
    return has_agg and has_specific


def _share_scope(c: str) -> str | None:
    """Scope key for a dominant-claim share bin (spacing or duration): 'pitched',
    or 'drum:<kit piece>'. Two share bins in the same scope are mutually exclusive
    dominant claims (e.g. 'steady 16th spacing' vs 'attacks on every 8th';
    'multimeasure stretches' vs 'quarter-length dominates'), so they must never
    share a combo.
    """
    if not c.endswith("_share"):
        return None
    if "_spacing_" in c or c.startswith("spacing_"):
        dim = "spacing"
    elif "_duration_" in c or c.startswith("duration_"):
        dim = "duration"
    else:
        return None
    piece = ("drum:" + c.split("_")[1]) if c.startswith("drum_") else "pitched"
    return f"{dim}:{piece}"


def _has_share_conflict(combo) -> bool:
    scopes: dict[str, set] = {}
    for c in combo:
        s = _share_scope(c)
        if s is None:
            continue
        scopes.setdefault(s, set()).add(c)
    return any(len(v) >= 2 for v in scopes.values())


def _melodic_dir_family(c: str) -> str | None:
    """Classify a melodic-motion concept: 'asc', 'desc', or None."""
    if c == "melodic_intervals_pct_ascending" or re.match(r"profile_melodic_intervals_pct_asc_\d+", c):
        return "asc"
    if c == "melodic_intervals_pct_descending" or re.match(r"profile_melodic_intervals_pct_desc_\d+", c):
        return "desc"
    return None


def _has_melodic_direction_conflict(combo) -> bool:
    """A melody can't assert a dominant motion that is both ascending and
    descending (aggregate or specific), so an asc-family + desc-family combo
    is contradictory."""
    fams = {f for f in (_melodic_dir_family(c) for c in combo) if f}
    return "asc" in fams and "desc" in fams


def _sample(concepts: list[str], k: int, n: int, rng: random.Random,
            conflicts: frozenset[frozenset[str]] = CONFLICT_PAIRS) -> list[list[str]]:
    if k > len(concepts):
        return []
    total = math.comb(len(concepts), k)
    needed = min(n, total)
    if total <= needed * 10:
        valid = [list(c) for c in combinations(concepts, k) if not _has_conflict(c, conflicts)]
        return rng.sample(valid, min(needed, len(valid)))
    selected: set[tuple[str, ...]] = set()
    result: list[list[str]] = []
    max_attempts = needed * 100
    attempts = 0
    while len(result) < needed and attempts < max_attempts:
        s = tuple(sorted(rng.sample(concepts, k)))
        if s not in selected and not _has_conflict(s, conflicts):
            selected.add(s)
            result.append(list(s))
        attempts += 1
    return result


def _ensure_covered(combos: list[list[str]], active: list[str], k: int, rng: random.Random) -> list[list[str]]:
    """Guarantee every active concept appears in at least one combo.

    Returns extra combos (of size up to k) covering any concepts missing from the
    union of ``combos``. Greedy: each added combo covers one new concept plus up
    to k-1 already-covered fillers, so only a handful of extra combos are needed.
    """
    covered = set()
    for c in combos:
        covered.update(c)
    uncovered = [c for c in active if c not in covered]
    extra: list[list[str]] = []
    remaining = set(uncovered)
    while remaining:
        c = sorted(remaining)[0]
        fillers = [x for x in active if x != c and x not in remaining]
        take = min(k - 1, len(fillers))
        picked = rng.sample(fillers, take) if take else []
        combo = sorted(set([c] + picked))
        extra.append(combo)
        remaining -= set(combo)
    return extra


def _distributed_cover(combos: list[list[str]], active: list[str],
                       sizes: list[int], rng: random.Random) -> list[list[str]]:
    """Return extra combos covering any active concepts missing from ``combos``,
    distributed across the given combo ``sizes`` (so coverage is not concentrated
    in one size). Shuffles the uncovered concepts and chunks them into combos whose
    sizes cycle through ``sizes``.
    """
    covered = set()
    for c in combos:
        covered.update(c)
    uncovered = [c for c in active if c not in covered]
    if not uncovered:
        return []
    rng.shuffle(uncovered)
    extra: list[list[str]] = []
    i = 0
    si = 0
    while i < len(uncovered):
        k = min(sizes[si % len(sizes)], len(uncovered) - i)
        si += 1
        extra.append(sorted(uncovered[i:i + k]))
        i += k
    return extra


def _run_one(taxonomy, translator, family, key, prompt, expected):
    """expected = list of (concept_name, expected_direction)."""
    translation = None
    record = None
    last_err = ""
    for _ in range(1):
        try:
            translation, record = translator.translate(prompt, family)
            break
        except Exception as e:
            last_err = str(e)
            record = getattr(e, "record", None)
            time.sleep(0.5)

    # --- presence + direction scoring ---
    ok = False
    returned: list = []
    level_by_concept: dict[str, str] = {}
    direction: dict[str, dict] = {}
    if translation:
        targets = translation.targets
        returned = [(t.concept_name, t.level_name) for t in targets]
        returned_set = {t.concept_name for t in targets}
        ok = all(c in returned_set for c, _ in expected)
        level_by_concept = {t.concept_name: t.level_name for t in targets}
        for cname, edir in expected:
            if edir in ("unknown", "n/a"):
                direction[cname] = {"expected": edir, "ok": None}
                continue
            got_level = level_by_concept.get(cname)
            got_dir = _level_bucket(taxonomy, cname, got_level) if got_level else None
            # Direction is a coarse POLARITY check: a 'high' expectation is satisfied
            # by high OR mid (only landing on low fails); a 'low' expectation by low OR
            # mid. 'mid' expectations stay strict. This avoids punishing the model for
            # returning a reasonable moderate level on a 5-6 level concept.
            if got_dir is None:
                ok_dir = None
            elif edir == "high":
                ok_dir = got_dir in ("high", "mid")
            elif edir == "low":
                ok_dir = got_dir in ("low", "mid")
            else:  # mid
                ok_dir = got_dir == "mid"
            direction[cname] = {
                "expected": edir, "got_level": got_level,
                "got_direction": got_dir, "ok": ok_dir,
            }

    # --- exhaustive logging of everything the LLM emitted ---
    llog = log_call(translation, record)

    return {
        "key": list(key),
        "family": family,
        "prompt": prompt,
        "expected": [{"concept": c, "direction": d} for c, d in expected],
        "success": ok,
        "returned": returned,
        "direction": direction,
        "error": last_err or None,
        **llog,
    }


def save_checkpoint(data: dict) -> None:
    CHECKPOINT.write_text(json.dumps(data, indent=2, default=str))


def load_checkpoint() -> dict | None:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return None


def main() -> int:
    if not get_api_key():
        print("ERROR: No API key configured.")
        return 1

    material = json.loads(MATERIAL.read_text())
    taxonomy = TaxonomyExporter(ExtractorRegistry(PLUGINS)).to_dict()
    rng = random.Random(SEED)

    tmp_dir = Path(tempfile.mkdtemp(prefix="midi_llm_evaluation3_"))
    tax_path = tmp_dir / "taxonomy.json"
    db_path = tmp_dir / "analysis.db"
    tax_path.write_text(json.dumps(taxonomy, indent=2))
    with AnalysisDatabase(db_path) as db:
        db.create_tables()
    index = SearchIndex(db_path, tax_path)
    translator = LLMTranslator(index, include_semantic_analysis=False)

    checkpoint = load_checkpoint()
    if checkpoint:
        all_results = checkpoint["all_results"]
        existing_keys = {tuple(r["key"]) for r in all_results}
        print(f"Resuming from checkpoint: {len(all_results)} results saved")
    else:
        all_results = []
        existing_keys = set()

    # Build all trials deterministically.
    trials: list[tuple] = []
    for family in ["drums", "pitched"]:
        active = _active_concepts(taxonomy, material, family)
        print(f"=== {family.upper()} ({len(active)} concepts) ===")

        # Single trials for non-paired concepts. Grid and time-signature pairs are
        # tested together via the material's combined (pair_direction) entries.
        for cname in active:
            if ("grid_attempt_pct_" in cname or "grid_success_pct_" in cname
                    or cname in ("metadata_time_sig_num", "metadata_time_sig_den")):
                continue
            paras = _paraphrases_for(material, cname, family)
            if not paras:
                continue
            key = (family, "single", cname)
            if key not in existing_keys:
                entry = rng.choice(paras)
                trials.append((taxonomy, translator, family, key,
                               _with_prefix_note(entry["paraphrase"], family),
                               [(cname, entry["direction"])]))

        # Combined pair trials (grid attempt<->success, time-sig num<->den), read
        # directly from the material: each entry carrying a ``pair_direction`` is
        # one test case that asserts both concepts.
        for cname in active:
            for entry in material.get(cname, []):
                if not entry.get("pair_direction"):
                    continue
                pair = entry.get("pair")
                key = (family, "gridpair", entry["paraphrase"])
                if key in existing_keys or pair not in taxonomy:
                    continue
                trials.append((taxonomy, translator, family, key,
                               _with_prefix_note(entry["paraphrase"], family),
                               [(cname, entry["direction"]), (pair, entry["pair_direction"])]))

        # metadata_instrument_family is redundant inside a family-obvious combo
        # (it is implied by the family hint), so it is tested as a single only.
        combo_active = [c for c in active if c != "metadata_instrument_family"]

        all_combos: list[list[str]] = []
        for combo_size, num_sets in COMBO_BATCHES:
            if combo_size > len(combo_active):
                print(f"  combo={combo_size}: SKIPPED (only {len(combo_active)} concepts)")
                continue
            combos = _sample(combo_active, combo_size, num_sets, rng)
            all_combos.extend(combos)
            for ci, combo in enumerate(combos):
                key = (family, "combo", f"{combo_size}_{ci}")
                if key in existing_keys:
                    continue
                chosen = [rng.choice(_paraphrases_for(material, c, family)) for c in combo]
                prompt = _with_prefix_note(", ".join(e["paraphrase"] for e in chosen), family)
                expected = []
                for c, e in zip(combo, chosen):
                    expected.append((c, e["direction"]))
                    # combined grid entries assert the paired concept's level too
                    if e.get("pair_direction"):
                        expected.append((e["pair"], e["pair_direction"]))
                trials.append((taxonomy, translator, family, key, prompt, expected))

        # Guarantee every active concept appears in at least one combo, distributed
        # across sizes (not concentrated in a single size).
        extra = _distributed_cover(all_combos, combo_active, COVER_SIZES, rng)
        size_index = {k: n for k, n in COMBO_BATCHES}
        for combo in extra:
            k = len(combo)
            ci = size_index.get(k, 0)
            size_index[k] = ci + 1
            key = (family, "combo", f"{k}_{ci}")
            if key in existing_keys:
                continue
            chosen = [rng.choice(_paraphrases_for(material, c, family)) for c in combo]
            prompt = _with_prefix_note(", ".join(e["paraphrase"] for e in chosen), family)
            expected = []
            for c, e in zip(combo, chosen):
                expected.append((c, e["direction"]))
                if e.get("pair_direction"):
                    expected.append((e["pair"], e["pair_direction"]))
            trials.append((taxonomy, translator, family, key, prompt, expected))

    print(f"\nRunning {len(trials)} trials with concurrency={CONCURRENCY}...")
    try:
        translator.translate("warm up the prompt cache", "drums")
    except Exception:
        pass
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = [ex.submit(_run_one, *t) for t in trials]
        for i, fut in enumerate(futures, 1):
            all_results.append(fut.result())
            if i % 20 == 0 or i == len(futures):
                elapsed = time.perf_counter() - t_start
                passed_so_far = sum(1 for r in all_results if r["success"])
                print(f"  {i}/{len(futures)} done ({elapsed:.0f}s, {passed_so_far} pass)", flush=True)
                save_checkpoint({"all_results": all_results})
    print(f"All trials complete in {time.perf_counter() - t_start:.1f}s")
    save_checkpoint({"all_results": all_results})

    passed = sum(1 for r in all_results if r["success"])
    total = len(all_results)

    # direction accuracy over graded directions only
    graded = 0
    dir_correct = 0
    for r in all_results:
        for res in (r.get("direction") or {}).values():
            if res.get("ok") is not None:
                graded += 1
                if res["ok"]:
                    dir_correct += 1
    dir_accuracy = round(dir_correct / graded, 4) if graded else None

    # Lexical-distance quality gate: verify the material's paraphrases do not
    # reproduce their concept's distinctive system-prompt wording.
    distance = {"entries": 0, "distanced": 0, "distanced_frac": 0.0,
                "leaked_tokens_total": 0, "leaked_ngrams_total": 0}
    for cname, entries in material.items():
        if cname.startswith("__") or cname in ("llm_categories", "llm_subcategories"):
            continue
        for e in entries:
            d = distancing.score(e["paraphrase"], cname)
            distance["entries"] += 1
            distance["leaked_tokens_total"] += len(d["leaked_tokens"])
            distance["leaked_ngrams_total"] += len(d["leaked_ngrams"])
            if d["distanced"]:
                distance["distanced"] += 1
    distance["distanced_frac"] = round(distance["distanced"] / distance["entries"], 4) if distance["entries"] else 0.0

    families = {}
    kinds = {}
    combos = {}
    for r in all_results:
        fam = r["family"]
        kind = r["key"][1]
        families.setdefault(fam, {"total": 0, "passed": 0})
        families[fam]["total"] += 1
        families[fam]["passed"] += 1 if r["success"] else 0
        if kind == "combo":
            cs = r["key"][2].split("_")[0]
            combos.setdefault(cs, {"total": 0, "passed": 0})
            combos[cs]["total"] += 1
            combos[cs]["passed"] += 1 if r["success"] else 0
        kinds.setdefault(kind, {"total": 0, "passed": 0})
        kinds[kind]["total"] += 1
        kinds[kind]["passed"] += 1 if r["success"] else 0

    summary = {
        "phase": "evaluation_3",
        "description": "Fused single + combo paraphrase validation (evaluation_3_materials.json)",
        "total": total, "passed": passed, "failed": total - passed,
        "presence_accuracy": round(passed / total, 4) if total else 0,
        "direction_graded": graded, "direction_correct": dir_correct,
        "direction_accuracy": dir_accuracy,
        "distance_validation": distance,
        "families": {k: {**v, "accuracy": round(v["passed"] / v["total"], 4) if v["total"] else 0}
                     for k, v in families.items()},
        "kinds": {k: {**v, "accuracy": round(v["passed"] / v["total"], 4) if v["total"] else 0}
                  for k, v in kinds.items()},
        "combos": {k: {**v, "accuracy": round(v["passed"] / v["total"], 4) if v["total"] else 0}
                   for k, v in sorted(combos.items())},
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = Path(__file__).resolve().parent.parent.parent.parent / "experiments" / "evaluation_paraphrases_3" / timestamp
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (exp_dir / "results.json").write_text(json.dumps(all_results, indent=2, default=str))

    print(f"\n=== Test 3 complete: {passed}/{total} presence ({passed/total:.1%}) ===")
    if dir_accuracy is not None:
        print(f"    direction accuracy: {dir_correct}/{graded} ({dir_accuracy:.1%})")
    print(f"Archived: {exp_dir}")

    CHECKPOINT.unlink(missing_ok=True)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
