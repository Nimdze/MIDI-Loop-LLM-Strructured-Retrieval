#!/usr/bin/env python3
"""Test 5 — Natural musical queries (far from the paraphrase material).

100 curated, natural musical queries: vibes/imagery, musical-technical phrasing
not present in the paraphrase material, genre names, and clear emotional-musical
cases. There are NO expected targets — outputs are evaluated manually and by an
LLM judge using the scoring rubric in ``evaluation_5_musical_queries_scoring.md``.

Semantic analysis is enabled so each tag records WHY the model
chose it. Family is passed as a neutral hint ("both") so the model self-classifies.

Runner writes: results.json (full), to_evaluate.json (judge input), and
distance_report.json (lexical novelty vs the system prompt) to the experiment dir.
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

from midi_llm_search_engine.config import get_api_key
from midi_llm_search_engine.index_loader import SearchIndex
from midi_llm_search_engine.llm_client import LLMTranslator
from midi_analyzer_tagger.storage.sqlite import AnalysisDatabase
from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.exporters.taxonomy import TaxonomyExporter
from midi_analyzer_tagger.extractors import PLUGINS

import eval_3_5_6_distancing as distancing

BANK = Path(__file__).resolve().parent / "evaluation_5_musical_queries.json"
SCORING_MD = Path(__file__).resolve().parent / "evaluation_5_musical_queries_scoring.md"
CHECKPOINT = Path(__file__).resolve().parent / ".evaluation_5_musical_queries_checkpoint.json"
PHASE = "evaluation_4"
EXP_DIR = "evaluation_musical_queries_5"
CONCURRENCY = 20


def _run_one(translator, item: dict) -> dict:
    qid, query = item["id"], item["query"]
    translation = None
    record = None
    last_err = ""
    for _ in range(3):
        try:
            translation, record = translator.translate(query, "both")
            break
        except Exception as e:
            last_err = str(e)
            record = getattr(e, "record", None)
            time.sleep(0.5)

    if translation is None:
        return {"id": qid, "query": query, "subtype": item.get("subtype"), "error": last_err,
                "targets": [], "semantic_analysis": [],
                "family_classification": None, "raw": None,
                "provider": None, "model": None, "tokens": None, "ms": None}

    return {
        "id": qid, "query": query, "subtype": item.get("subtype"), "error": None,
        "targets": [{"concept": t.concept_name, "level": t.level_name,
                     "importance": t.importance, "fallback": t.fallback} for t in translation.targets],
        "semantic_analysis": [dict(x) for x in translation.semantic_analysis],
        "family_classification": translation.family_classification,
        "raw": record.raw if record else None,
        "provider": record.provider if record else None,
        "model": record.model if record else None,
        "tokens": {"prompt": record.prompt_tokens, "completion": record.completion_tokens} if record else None,
        "ms": record.response_time_ms if record else None,
    }


def save_checkpoint(data: dict) -> None:
    CHECKPOINT.write_text(json.dumps(data, indent=2, default=str))


def load_checkpoint() -> dict | None:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return None


def _distance_report(bank: list[dict]) -> dict:
    rows = []
    total = 0.0
    for item in bank:
        nov = distancing.novelty(item["query"])
        total += nov
        rows.append({"id": item["id"], "query": item["query"], "novelty": round(nov, 4)})
    return {"queries": rows,
            "mean_novelty": round(total / len(rows), 4) if rows else 0}


def main() -> int:
    if not get_api_key():
        print("ERROR: No API key configured.")
        return 1
    bank = json.loads(BANK.read_text())
    if not bank:
        print("empty bank"); return 1

    taxonomy = TaxonomyExporter(ExtractorRegistry(PLUGINS)).to_dict()
    tmp_dir = Path(tempfile.mkdtemp(prefix="midi_llm_evaluation5q_"))
    tax_path = tmp_dir / "taxonomy.json"; db_path = tmp_dir / "analysis.db"
    tax_path.write_text(json.dumps(taxonomy, indent=2))
    with AnalysisDatabase(db_path) as db:
        db.create_tables()
    index = SearchIndex(db_path, tax_path)
    translator = LLMTranslator(index, include_semantic_analysis=True)

    checkpoint = load_checkpoint()
    if checkpoint:
        results = checkpoint["all_results"]
        done = {r["id"] for r in results}
        print(f"Resuming from checkpoint: {len(results)} results")
    else:
        results = []
        done = set()

    todo = [it for it in bank if it["id"] not in done]
    print(f"Bank: {len(bank)} queries; running {len(todo)} with concurrency={CONCURRENCY}")
    try:
        translator.translate("warm up the prompt cache", "drums")
    except Exception:
        pass
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = [ex.submit(_run_one, translator, it) for it in todo]
        for i, fut in enumerate(futures, 1):
            results.append(fut.result())
            if i % 20 == 0 or i == len(futures):
                print(f"  {i}/{len(todo)} done ({time.perf_counter()-t_start:.0f}s)", flush=True)
                save_checkpoint({"all_results": results})
    print(f"Complete in {time.perf_counter()-t_start:.1f}s")
    save_checkpoint({"all_results": results})

    results.sort(key=lambda r: r["id"])
    distance = _distance_report(bank)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = Path(__file__).resolve().parent.parent.parent.parent / "experiments" / EXP_DIR / timestamp
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))
    (exp_dir / "to_evaluate.json").write_text(json.dumps(results, indent=2, default=str))
    (exp_dir / "distance_report.json").write_text(json.dumps(distance, indent=2, default=str))
    shutil.copy(SCORING_MD, exp_dir / SCORING_MD.name)

    summary = {"phase": PHASE, "bank": BANK.name, "total": len(results),
               "errors": sum(1 for r in results if r["error"]),
               "with_targets": sum(1 for r in results if r["targets"]),
               "mean_novelty": distance["mean_novelty"]}
    (exp_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    print(f"\n=== {PHASE} complete: {len(results)} queries, "
          f"{summary['errors']} errors, mean lexical novelty {summary['mean_novelty']:.2f} ===")
    print(f"Archived: {exp_dir}")
    print(f"Judge input: {exp_dir / 'to_evaluate.json'}  |  rubric: {exp_dir / SCORING_MD.name}")

    CHECKPOINT.unlink(missing_ok=True)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
