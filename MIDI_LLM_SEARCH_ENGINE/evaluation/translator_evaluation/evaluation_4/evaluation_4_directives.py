#!/usr/bin/env python3
"""Evaluation 4 — Importance & fallback directives.

Tests whether the translator derives *relative importance* and *fallback
direction* from the query structure, using templates whose expectations are
known a priori (so the eval is automatic, no humans):

- **relative importance** as RANKED GROUPS: ``case["importance"]`` is a list of
  groups in DESCENDING importance. Within a group all concepts must TIE (equal
  importance); every concept in a higher group must beat every concept in a lower
  group. This tests both ordering and ties ("above all A, then B / optionally B").
- **fallback**: "at least X" -> ``down``; "at most / not too X" -> ``up``;
  "around / about X" -> ``nearest``.

Deliberately no absolute importance anchors (must-have / optional); only relative
orderings/ties and directional fallbacks are asserted. Presence of the expected
concepts is also checked (as in the routing evals).

Each case records the returned targets and per-assertion pass/fail, so results
are inspectable. Reuses the translator and ``_logging``; automatic, parallel,
checkpoint-resumable.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

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

CHECKPOINT = Path(__file__).resolve().parent / ".evaluation_4_directives_checkpoint.json"
CONCURRENCY = 20
PHASE = "evaluation_4"
EXP_DIR = "evaluation_directives_4"

_DIRECTIVES_FILE = Path(__file__).resolve().parent / "evaluation_4_directives.json"
DIRECTIVES: list[dict] = json.loads(_DIRECTIVES_FILE.read_text()) if _DIRECTIVES_FILE.exists() else []


def _run_one(translator, case: dict) -> dict:
    translation = None
    record = None
    last_err = ""
    for _ in range(3):
        try:
            translation, record = translator.translate(case["query"], "both")
            break
        except Exception as e:
            last_err = str(e)
            record = getattr(e, "record", None)
            time.sleep(0.5)

    if translation is None:
        return {
            "id": case["id"], "query": case["query"], "error": last_err,
            "targets": [], "checks": {}, "ok": False, "raw": None, "call": None,
        }

    by = {t.concept_name: t for t in translation.targets}
    checks: dict = {}
    ok = True

    # presence
    present = [c for c in case["presence"] if c in by]
    p_ok = set(case["presence"]) <= set(present)
    checks["presence"] = {"required": case["presence"], "present": present, "ok": p_ok}
    ok = ok and p_ok

    # Ranked importance groups. ``case["importance"]`` is a list of groups in
    # DESCENDING importance. Within a group all concepts must TIE (equal
    # importance); every concept in a higher group must beat every concept in a
    # lower group (min(higher) > max(lower)).
    for gi, group in enumerate(case["importance"]):
        imps = [by[c].importance for c in group if c in by]
        present_ok = len(imps) == len(group)
        tie_ok = present_ok and len(set(imps)) == 1
        checks[f"tie group {gi} ({','.join(group)})"] = {"imps": imps, "ok": present_ok and tie_ok}
        ok = ok and present_ok and tie_ok
        for gj in range(gi + 1, len(case["importance"])):
            lower = [by[c].importance for c in case["importance"][gj] if c in by]
            if imps and lower:
                ord_ok = min(imps) > max(lower)
                checks[f"importance group {gi} > {gj}"] = {"higher": imps, "lower": lower, "ok": ord_ok}
                ok = ok and ord_ok

    # fallback direction (only non-default expected)
    for cname, exp in case["fallback"].items():
        got = by[cname].fallback if cname in by else None
        c_ok = (got == exp)
        checks[f"fallback {cname}"] = {"expected": exp, "got": got, "ok": c_ok}
        ok = ok and c_ok

    targets = [{"concept": t.concept_name, "level": t.level_name,
                "importance": t.importance, "fallback": t.fallback} for t in translation.targets]
    return {
        "id": case["id"], "query": case["query"], "error": None,
        "targets": targets, "checks": checks, "ok": ok,
        **log_call(translation, record),
    }


def main() -> int:
    if not get_api_key():
        print("ERROR: No API key configured.")
        return 1

    taxonomy = TaxonomyExporter(ExtractorRegistry(PLUGINS)).to_dict()
    tmp_dir = Path(tempfile.mkdtemp(prefix="midi_llm_evaluation4_"))
    tax_path = tmp_dir / "taxonomy.json"
    db_path = tmp_dir / "analysis.db"
    tax_path.write_text(json.dumps(taxonomy, indent=2))
    with AnalysisDatabase(db_path) as db:
        db.create_tables()
    index = SearchIndex(db_path, tax_path)
    translator = LLMTranslator(index)

    try:
        translator.translate("warm up the prompt cache", "pitched")
    except Exception:
        pass

    t_start = time.perf_counter()
    results: list[dict] = []
    checkpoint_data = {"all_results": []}
    if CHECKPOINT.exists():
        try:
            checkpoint_data = json.loads(CHECKPOINT.read_text())
            results = checkpoint_data.get("all_results", [])
            done_ids = {r["id"] for r in results}
            print(f"  Resuming from checkpoint ({len(results)} results saved)", flush=True)
        except Exception:
            done_ids = set()
    else:
        done_ids = set()

    pending = [c for c in DIRECTIVES if c["id"] not in done_ids]
    if not pending:
        print("  All cases already done in checkpoint.", flush=True)
        results = checkpoint_data["all_results"]
    else:
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
            fut_by_id = {ex.submit(_run_one, translator, c): c["id"] for c in pending}
            from concurrent.futures import as_completed
            for fut in as_completed(fut_by_id):
                r = fut.result()
                results.append(r)
                if len(results) % 10 == 0 or len(results) == len(DIRECTIVES):
                    checkpoint_data["all_results"] = results
                    CHECKPOINT.write_text(json.dumps(checkpoint_data, default=str))
                    print(f"  {len(results)}/{len(DIRECTIVES)} done ({time.perf_counter()-t_start:.0f}s)", flush=True)
        # final save
        checkpoint_data["all_results"] = results
        CHECKPOINT.write_text(json.dumps(checkpoint_data, default=str))

    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    imp_ok = sum(1 for r in results for k, v in r["checks"].items()
                 if k.startswith(("importance", "tie")) and v["ok"])
    imp_total = sum(1 for r in results for k in r["checks"]
                    if k.startswith(("importance", "tie")))
    fb_ok = sum(1 for r in results for k, v in r["checks"].items() if k.startswith("fallback") and v["ok"])
    fb_total = sum(1 for r in results for k in r["checks"] if k.startswith("fallback"))

    summary = {
        "phase": PHASE,
        "description": "Importance & fallback directives (relative importance + directional fallback)",
        "total": total, "passed": passed, "failed": total - passed,
        "importance": {"checked": imp_total, "passed": imp_ok,
                       "accuracy": round(imp_ok / imp_total, 4) if imp_total else None},
        "fallback": {"checked": fb_total, "passed": fb_ok,
                     "accuracy": round(fb_ok / fb_total, 4) if fb_total else None},
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = Path(__file__).resolve().parent.parent.parent.parent / "experiments" / EXP_DIR / timestamp
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (exp_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    print(f"\n=== Evaluation 4 complete: {passed}/{total} cases ===")
    print(f"  importance: {imp_ok}/{imp_total} | fallback: {fb_ok}/{fb_total}")
    print(f"Archived: {exp_dir}")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
