#!/usr/bin/env python3
"""Test 1 — Literal tag reproduction at combos 1-10.

For each active concept, constructs `concept_name: level_name` prompts,
combines N of them, and verifies the LLM returns exactly those N pairs.
No paraphrases, no interpretation — pure taxonomy reproduction.
"""
from __future__ import annotations

import json
import math
import random
import shutil
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any


def _norm(cname: str) -> str:
    """Normalize concept names: strip zero-padding from numeric segments."""
    import re
    return re.sub(r'(?<=_)(\d+)(?=_)', lambda m: str(int(m.group(1))), cname)


def _is_paired_extra(extra_concept: str, all_expected_names: set[str]) -> bool:
    """Return True if extra_concept is a paired variant of an expected concept."""
    # grid_attempt_pct_X ↔ grid_success_pct_X
    for ex in all_expected_names:
        for a, b in [("_attempt_pct_", "_success_pct_"), ("_success_pct_", "_attempt_pct_")]:
            if a in ex and b in extra_concept:
                prefix_a = ex.split(a)[0]
                suffix_a = ex.split(a)[1]
                prefix_b = extra_concept.split(b)[0] if b in extra_concept else ""
                suffix_b = extra_concept.split(b)[1] if b in extra_concept else ""
                if prefix_a == prefix_b and suffix_a == suffix_b:
                    return True
    # metadata_time_sig_num ↔ metadata_time_sig_den
    if ("metadata_time_sig_num" in extra_concept and "metadata_time_sig_den" in all_expected_names):
        return True
    if ("metadata_time_sig_den" in extra_concept and "metadata_time_sig_num" in all_expected_names):
        return True
    return False

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


BATCHES = {
    1: 20, 2: 20, 3: 20, 4: 20, 5: 20,
    6: 10, 7: 10, 8: 10, 9: 10, 10: 10,
}
SEED = 42
CONCURRENCY = 50
CK = Path(__file__).resolve().parent / ".evaluation1_checkpoint.json"


def _build_taxonomy() -> dict[str, Any]:
    registry = ExtractorRegistry(PLUGINS)
    exporter = TaxonomyExporter(registry)
    return exporter.to_dict()


def _active_concepts(tax: dict[str, Any], family: str) -> list[str]:
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
        if family in fams:
            result.append(cname)
    return sorted(result)


def _sample(concepts: list[str], k: int, n: int, rng: random.Random) -> list[list[str]]:
    """Sample k-sized subsets. Reservoir sample if total combos too large."""
    if k > len(concepts):
        return []
    total = math.comb(len(concepts), k)
    needed = min(n, total)
    if total <= needed * 10:
        return [list(c) for c in rng.sample(list(combinations(concepts, k)), needed)]
    selected: set[tuple[str, ...]] = set()
    result: list[list[str]] = []
    max_attempts = needed * 100
    attempts = 0
    while len(result) < needed and attempts < max_attempts:
        sample = tuple(sorted(rng.sample(concepts, k)))
        if sample not in selected:
            selected.add(sample)
            result.append(list(sample))
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


def _run_trial(taxonomy, index, translator, family, combo_size, ci, combo, start_offset):
    """Execute one trial: build the literal prompt, call the LLM, and score it."""
    expected_pairs: list[tuple[str, str]] = []
    parts: list[str] = []
    for con_i, cname in enumerate(combo):
        levels = index.level_names(cname)
        # metadata_instrument_family levels are mostly pitched instruments; only
        # "Drum Kit" is a valid level for a drums combo. Sample family-appropriate
        # levels so the literal echo is actually achievable.
        if cname == "metadata_instrument_family":
            if family == "drums":
                levels = [l for l in levels if l == "Drum Kit"] or levels
            else:
                levels = [l for l in levels if l != "Drum Kit"] or levels
        level_idx = (start_offset + con_i) % len(levels)
        level_name = levels[level_idx]
        parts.append(f"{cname}: {level_name}")
        expected_pairs.append((cname, level_name))
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

    llog = log_call(translation, record)
    if translation is None:
        return {
            "combo_size": combo_size, "set_index": ci, "family": family,
            "prompt": prompt, "expected": expected_pairs,
            "returned": [], "success": False, "error": last_err,
            **llog,
        }

    returned = [(t.concept_name, t.level_name) for t in translation.targets]
    expected_norm = {(_norm(c), l) for c, l in expected_pairs}
    returned_norm = {(_norm(c), l) for c, l in returned}
    missing_concepts = [c for c, l in expected_pairs if (_norm(c), l) not in returned_norm]
    raw_extras = [t for t in returned if (_norm(t[0]), t[1]) not in expected_norm]
    expected_names = {c for c, l in expected_pairs}
    filtered_extras = [e for e in raw_extras if not _is_paired_extra(e[0], expected_names)]
    wrong_family = []
    for t in translation.targets:
        tf = taxonomy.get(t.concept_name, {}).get("llm", {}).get("instrument_family", [])
        if isinstance(tf, str):
            tf = [tf]
        if family == "drums" and "drums" not in tf:
            wrong_family.append(t.concept_name)
        elif family == "pitched" and "pitched" not in tf:
            wrong_family.append(t.concept_name)
    success = not missing_concepts and not filtered_extras and not wrong_family
    return {
        "combo_size": combo_size, "set_index": ci, "family": family,
        "prompt": prompt, "expected": expected_pairs,
        "returned": returned, "success": success,
        "missing": list(missing_concepts), "extras": raw_extras,
        "filtered_out": filtered_extras, "wrong_family": wrong_family, "error": None,
        **llog,
    }


def main() -> int:
    if not get_api_key():
        print("ERROR: No API key configured.")
        return 1

    # Build taxonomy
    taxonomy = _build_taxonomy()
    rng = random.Random(SEED)

    # Count active concepts per family
    active_drums = _active_concepts(taxonomy, "drums")
    active_pitched = _active_concepts(taxonomy, "pitched")
    print(f"Active concepts: drums={len(active_drums)}, pitched={len(active_pitched)}")

    expected_combos = sum(BATCHES.values()) * 2  # both families
    total_expected = sum(
        cs * count * 2 for cs, count in BATCHES.items()
    )
    print(f"Expected: {expected_combos} combos, {total_expected} total targets")

    # Verify coverage — every concept should appear at least once
    combos_needed = sum(BATCHES.values())
    if len(active_drums) < max(BATCHES.keys()):
        print(f"WARNING: Only {len(active_drums)} drum concepts; cannot make combos > {len(active_drums)}")
    if len(active_pitched) < max(BATCHES.keys()):
        print(f"WARNING: Only {len(active_pitched)} pitched concepts; cannot make combos > {len(active_pitched)}")

    # Build temporary DB + taxonomy file for SearchIndex
    tmp_dir = Path(tempfile.mkdtemp(prefix="midi_llm_evaluation1_"))
    tax_path = tmp_dir / "taxonomy.json"
    db_path = tmp_dir / "analysis.db"
    tax_path.write_text(json.dumps(taxonomy, indent=2))
    with AnalysisDatabase(db_path) as db:
        db.create_tables()
    index = SearchIndex(db_path, tax_path)
    translator = LLMTranslator(index)

    results: list[dict[str, Any]] = []
    if CK.exists():
        results = json.loads(CK.read_text())
        print(f"Loaded {len(results)} results from checkpoint, resuming...")

    done_keys: set[tuple[str, int, int]] = set()
    for r in results:
        done_keys.add((r["family"], r["combo_size"], r["set_index"]))

    # Build all trials deterministically (replicating the sequential level
    # selection), then run them concurrently.
    trials: list[tuple] = []
    start_offset = 0
    for family, active in [("drums", active_drums), ("pitched", active_pitched)]:
        print(f"\n=== {family.upper()} ===")
        all_combos: list[list[str]] = []
        for combo_size, num_sets in sorted(BATCHES.items()):
            if combo_size > len(active):
                print(f"  combo={combo_size}: SKIPPED (only {len(active)} concepts)")
                continue
            combos = _sample(active, combo_size, num_sets, rng)
            print(f"  combo={combo_size}: {len(combos)} sets")
            all_combos.extend(combos)
            for ci, combo in enumerate(combos):
                key = (family, combo_size, ci)
                if key in done_keys:
                    continue
                trials.append((family, combo_size, ci, combo, start_offset))
                start_offset += len(combo)
        # Guarantee every active concept appears in at least one combo (top-up at size 2).
        extra = _ensure_covered(all_combos, active, 2, rng)
        size2_count = BATCHES.get(2, 0) if 2 <= len(active) else 0
        for ci, combo in enumerate(extra, start=size2_count):
            key = (family, 2, ci)
            if key in done_keys:
                continue
            trials.append((family, 2, ci, combo, start_offset))
            start_offset += len(combo)

    print(f"\nRunning {len(trials)} trials with concurrency={CONCURRENCY}...")
    try:
        translator.translate("warm up the prompt cache", "drums")
    except Exception:
        pass
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = [ex.submit(_run_trial, taxonomy, index, translator, *t) for t in trials]
        for fut in futures:
            results.append(fut.result())
    print(f"All trials complete in {time.perf_counter() - t_start:.1f}s")
    CK.write_text(json.dumps(results, indent=2, default=str))

    # Compute statistics
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    families = {"drums": {"total": 0, "passed": 0}, "pitched": {"total": 0, "passed": 0}}
    combo_stats: dict[int, dict] = {}
    for r in results:
        cs = r["combo_size"]
        families[r["family"]]["total"] += 1
        families[r["family"]]["passed"] += 1 if r["success"] else 0
        combo_stats.setdefault(cs, {"total": 0, "passed": 0})
        combo_stats[cs]["total"] += 1
        combo_stats[cs]["passed"] += 1 if r["success"] else 0

    summary = {
        "phase": "evaluation1", "description": "Literal tag reproduction at combos 1-10",
        "total_combos": total, "passed": passed, "failed": total - passed,
        "accuracy": round(passed / total, 4) if total else 0,
        "families": {k: {**v, "accuracy": round(v["passed"] / v["total"], 4) if v["total"] else 0}
                     for k, v in families.items()},
        "combos": {str(cs): {"total": v["total"], "passed": v["passed"],
                             "accuracy": round(v["passed"] / v["total"], 4) if v["total"] else 0}
                   for cs, v in sorted(combo_stats.items())},
    }

    CK.unlink(missing_ok=True)

    # Write outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = Path(__file__).resolve().parent.parent.parent.parent / "experiments" / "evaluation_literal_1" / timestamp
    exp_dir.mkdir(parents=True, exist_ok=True)

    (exp_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (exp_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    print(f"\n=== Test 1 complete: {passed}/{total} ({passed/total:.1%}) ===")
    print(f"Archived: {exp_dir}")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
