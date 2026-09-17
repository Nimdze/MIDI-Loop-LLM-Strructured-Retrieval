#!/usr/bin/env python3
"""Shared exhaustive per-trial logging for the LLM translator tests.

Every test archives whatever the LLM emitted for each translate() call:
the raw model output, the full validated translation (interpretation, family
classification, semantic analysis, every target's concept/level/importance/
fallback, excluded concepts), and call metadata (provider, model, token
counts, response time).

Tests merge the dict returned by ``log_call()`` into each result record so the
archived ``results.json`` contains everything, regardless of which test wrote it.
"""
from __future__ import annotations


def log_call(translation, record) -> dict:
    """Return an exhaustive log of one translate() call.

    ``translation`` is a ``QueryTranslation`` (or None), ``record`` is the
    matching ``LLMCallRecord`` (or None). Keys are safe to JSON-serialize.
    """
    translation_log = None
    if translation is not None:
        translation_log = {
            "family_classification": translation.family_classification,
            "semantic_analysis": [dict(x) for x in translation.semantic_analysis],
            "targets": [
                {
                    "concept_name": t.concept_name,
                    "level_name": t.level_name,
                    "importance": t.importance,
                    "fallback": t.fallback,
                }
                for t in translation.targets
            ],
        }
    call_log = None
    if record is not None:
        call_log = {
            "provider": record.provider,
            "model": record.model,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "cached_tokens": record.cached_tokens,
            "reasoning_tokens": record.reasoning_tokens,
            "response_time_ms": record.response_time_ms,
            "error": record.error,
            "timestamp": str(record.timestamp),
        }
    return {
        "raw": record.raw if record is not None else None,
        "attempts": record.attempts if record is not None else None,
        "translation": translation_log,
        "call": call_log,
    }
