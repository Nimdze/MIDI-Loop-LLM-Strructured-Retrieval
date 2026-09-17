#!/usr/bin/env python3
"""Test 2 — Taxonomy example validation, singles + combos 1-10.

Fuses the former test 2 (single-concept example health check) and test 3
(example combos) into one script. For each active concept with at least one
``llm_example``, the first example is the prompt. Singles verify each concept in
isolation; combos of size 2-10 verify that all expected concepts are returned.

Presence scoring (extras allowed) plus a level check per expected concept:
each concept's returned level is compared against the expected direction bucket
(high/mid/low, driven by ``evaluation_2_directions.json``) or, for categorical
metadata, an exact expected level value.
Fully parallel, checkpoint-resumable, deterministic combo sampling.
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
from drum_selection import select_drum_representatives
from midi_llm_search_engine.config import get_api_key
from midi_llm_search_engine.index_loader import SearchIndex
from midi_llm_search_engine.llm_client import LLMTranslator
from midi_analyzer_tagger.storage.sqlite import AnalysisDatabase
from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.exporters.taxonomy import TaxonomyExporter
from midi_analyzer_tagger.extractors import PLUGINS

SEED = 42
CONCURRENCY = 20
CHECKPOINT = Path(__file__).resolve().parent / ".evaluation_2_checkpoint.json"

# Per-concept expected level: bucket (high/mid/low) for intensity-ordered
# concepts, or exact level for categorical metadata. Loaded once; a missing
# concept simply gets no level assertion.
_DIRECTIONS_FILE = Path(__file__).resolve().parent / "evaluation_2_directions.json"
_DIRECTIONS = json.loads(_DIRECTIONS_FILE.read_text()) if _DIRECTIONS_FILE.exists() else {}


def _level_bucket(taxonomy: dict, concept: str, level_name: str) -> str | None:
    """Bucket a returned level into high/mid/low by its position in the
    taxonomy's intensity-ordered ``levels`` (index 0 = most intense). Mirrors
    evaluation_3._level_bucket so both evals bucket identically.
    """
    levels = (taxonomy.get(concept, {}).get("llm") or {}).get("levels") or []
    idx = next((i for i, lv in enumerate(levels) if len(lv) > 1 and lv[1] == level_name), None)
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


# Combo sizes 1-10, sampled (size 1 via the same combo machinery, like test 1).
BATCHES = [
    (1, 20), (2, 16), (3, 12), (4, 10), (5, 10),
    (6, 8), (7, 6), (8, 5), (9, 4), (10, 4),
]


def _active_with_examples(tax: dict, family: str) -> list[str]:
    result = []
    for cname, data in tax.items():
        if cname in ("llm_categories", "llm_subcategories"):
            continue
        w = data.get("base_weight", data.get("default_weight", 1.0))
        if not w:
            continue
        fams = data.get("llm", {}).get("instrument_family", [])
        if isinstance(fams, str):
            fams = [fams]
        # Prefer pitched for both-family concepts (e.g. metadata_instrument_family),
        # matching the former test2. Drums-only concepts stay drums.
        if family == "drums":
            if "drums" not in fams or "pitched" in fams:
                continue
        else:  # pitched
            if "pitched" not in fams:
                continue
        ex = (data.get("llm") or {}).get("examples", [])
        if not ex:
            continue
        result.append(cname)
    if family == "drums":
        # One representative kit piece per drum base stat (uniform across the
        # kit-piece families, subcategories mixed), intersected with concepts
        # that actually have an example.
        reps = set(select_drum_representatives(tax))
        result = [c for c in result if c in reps]
    return sorted(result)


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


def _grid_pair(cname: str) -> str | None:
    """Return the paired grid concept for an attempt/success concept (or None)."""
    if "grid_attempt_pct_" in cname:
        return cname.replace("grid_attempt_pct_", "grid_success_pct_")
    if "grid_success_pct_" in cname:
        return cname.replace("grid_success_pct_", "grid_attempt_pct_")
    return None


def _run_one(taxonomy, translator, family, combo_size, ci, combo):
    """Build the prompt from the first example of each concept; presence check.

    Grid attempt/success are a semantic pair (the system prompt treats grid
    holistically), so a grid concept's paired counterpart is included in both the
    prompt and the expected set — matching test 3's pairing.
    """
    parts: list[str] = []
    expected: list[str] = []
    for cname in combo:
        ex = (taxonomy[cname].get("llm") or {}).get("examples", ["?"])[0]
        parts.append(ex)
        expected.append(cname)
        # Paired concepts (grid attempt/success, time-sig num/den) are kept in the
        # expected set, but their example is NOT injected into the prompt. The
        # translator itself now completes missing pairs (correction retry), so the
        # eval measures the real system rather than a harness-patched prompt.
        pair = _grid_pair(cname)
        if pair and pair in taxonomy and pair not in expected and pair not in combo:
            expected.append(pair)
    prompt = ", ".join(parts)

    translation = None
    record = None
    last_err = ""
    for _ in range(3):
        try:
            translation, record = translator.translate(prompt, family)
            break
        except Exception as e:
            last_err = str(e)
            time.sleep(0.5)

    ok = False
    returned: list = []
    level_status = {"ok": None, "checked": False, "details": {}}
    if translation:
        returned = [(t.concept_name, t.level_name) for t in translation.targets]
        returned_set = {t.concept_name for t in translation.targets}
        ok = all(c in returned_set for c in expected)

        # Level check: exact for categorical metadata, bucket for intensity concepts.
        level_by = dict(returned)
        details: dict = {}
        level_ok = True
        checked = False
        for cname in expected:
            meta = _DIRECTIONS.get(cname, {})
            exp_level = meta.get("expected_level")
            direction = meta.get("direction")
            got = level_by.get(cname)
            row_ok = None
            if exp_level is not None:
                checked = True
                row_ok = bool(got == exp_level)
            elif direction is not None:
                checked = True
                got_bucket = _level_bucket(taxonomy, cname, got) if got else None
                row_ok = bool(got_bucket == direction)
            details[cname] = {
                "expected": exp_level if exp_level is not None else direction,
                "returned": got,
                "ok": row_ok,
            }
            if row_ok is False:
                level_ok = False
        level_status = {"ok": level_ok, "checked": checked, "details": details}

    llog = log_call(translation, record)
    return {
        "combo_size": combo_size, "set_index": ci, "family": family,
        "prompt": prompt, "expected": expected,
        "returned": returned, "success": ok, "error": last_err or None,
        "level_status": level_status,
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

    taxonomy = TaxonomyExporter(ExtractorRegistry(PLUGINS)).to_dict()
    rng = random.Random(SEED)

    tmp_dir = Path(tempfile.mkdtemp(prefix="midi_llm_evaluation2_"))
    tax_path = tmp_dir / "taxonomy.json"
    db_path = tmp_dir / "analysis.db"
    tax_path.write_text(json.dumps(taxonomy, indent=2))
    with AnalysisDatabase(db_path) as db:
        db.create_tables()
    index = SearchIndex(db_path, tax_path)
    translator = LLMTranslator(index)

    checkpoint = load_checkpoint()
    if checkpoint:
        all_results = checkpoint["all_results"]
        existing_keys = {(r["family"], r["combo_size"], r["set_index"]) for r in all_results}
        print(f"Resuming from checkpoint: {len(all_results)} results saved")
    else:
        all_results = []
        existing_keys = set()

    trials: list[tuple] = []
    for family in ["drums", "pitched"]:
        active = _active_with_examples(taxonomy, family)
        print(f"=== {family.upper()} ({len(active)} concepts with examples) ===")

        # Combos 1-10 (size 1 sampled via the combo machinery, like test 1).
        all_combos: list[list[str]] = []
        for combo_size, num_sets in BATCHES:
            if combo_size > len(active):
                print(f"  combo={combo_size}: SKIPPED (only {len(active)} concepts)")
                continue
            combos = _sample(active, combo_size, num_sets, rng)
            all_combos.extend(combos)
            for ci, combo in enumerate(combos):
                key = (family, combo_size, ci)
                if key in existing_keys:
                    continue
                trials.append((family, combo_size, ci, combo))
        # Guarantee every active concept appears in at least one combo (top-up at size 2).
        extra = _ensure_covered(all_combos, active, 2, rng)
        size2_count = dict(BATCHES).get(2, 0) if 2 <= len(active) else 0
        for ci, combo in enumerate(extra, start=size2_count):
            key = (family, 2, ci)
            if key in existing_keys:
                continue
            trials.append((family, 2, ci, combo))

    print(f"\nRunning {len(trials)} trials with concurrency={CONCURRENCY}...")
    try:
        translator.translate("warm up the prompt cache", "drums")
    except Exception:
        pass
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = [ex.submit(_run_one, taxonomy, translator, *t) for t in trials]
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

    # Level-check aggregation (exact metadata values + direction buckets).
    level_checked = sum(1 for r in all_results for d in r.get("level_status", {}).get("details", {}).values() if d["ok"] is not None)
    level_passed = sum(1 for r in all_results for d in r.get("level_status", {}).get("details", {}).values() if d["ok"] is True)
    level_ok_results = sum(1 for r in all_results if r.get("level_status", {}).get("checked") and r.get("level_status", {}).get("ok"))

    families = {}
    combos = {}
    for r in all_results:
        fam = r["family"]
        cs = r["combo_size"]
        families.setdefault(fam, {"total": 0, "passed": 0})
        families[fam]["total"] += 1
        families[fam]["passed"] += 1 if r["success"] else 0
        combos.setdefault(cs, {"total": 0, "passed": 0})
        combos[cs]["total"] += 1
        combos[cs]["passed"] += 1 if r["success"] else 0

    summary = {
        "phase": "evaluation_2",
        "description": "Taxonomy examples, singles + combos 1-10",
        "total": total, "passed": passed, "failed": total - passed,
        "accuracy": round(passed / total, 4) if total else 0,
        "level": {
            "checked": level_checked,
            "passed": level_passed,
            "accuracy": round(level_passed / level_checked, 4) if level_checked else None,
            "results_ok": level_ok_results,
            "results_checked": sum(1 for r in all_results if r.get("level_status", {}).get("checked")),
        },
        "families": {k: {**v, "accuracy": round(v["passed"] / v["total"], 4) if v["total"] else 0}
                     for k, v in families.items()},
        "combos": {str(k): {**v, "accuracy": round(v["passed"] / v["total"], 4) if v["total"] else 0}
                   for k, v in sorted(combos.items())},
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = Path(__file__).resolve().parent.parent.parent.parent / "experiments" / "evaluation_examples_2" / timestamp
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (exp_dir / "results.json").write_text(json.dumps(all_results, indent=2, default=str))

    print(f"\n=== Test 2 complete: {passed}/{total} ({passed/total:.1%}) ===")
    print(f"Archived: {exp_dir}")

    CHECKPOINT.unlink(missing_ok=True)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
