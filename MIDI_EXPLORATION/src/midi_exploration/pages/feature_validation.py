"""Feature-validation workflow: verify that tags point to musically-correct files.

For a chosen target concept the sidebar shows its resolved levels (the two
intensity extremes, stepped inward when a tag is sparse) and lets the validator
pick which level to inspect. Additional tags can be combined (AND) — important
for grid attempt/success pairs. The main area shows a live mosaic of exactly the
files matching the active tag combination, with per-file playback, and a rating
per primary tag. Ratings are stored in session state and can be exported.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pretty_midi
import streamlit as st

from midi_exploration.feature_explanations import feature_explanation
from midi_exploration.playback import midi_to_wav_bytes
from midi_exploration.plotting.piano_rolls import plot_inspector_roll_to_base64
from midi_exploration.pages import visualizer
from midi_exploration.utils import resolve_midi_path
from midi_exploration.validation_concepts import build_target_concepts
from midi_exploration.validation_targets import resolve_extreme_tags

RATINGS_KEY = "fv_ratings"
COMBOS_KEY = "fv_combos"
MOSAIC_MAX = 30
PLAY_LIST_MAX = 50


def _ratings_path() -> Path:
    """Durable shared ratings file, next to the analysis DB (or project root)."""
    db = os.environ.get("MIDI_RETRIEVE_DB")
    if db:
        return Path(db).parent / "ratings.json"
    return Path(__file__).resolve().parent.parent.parent.parent / "ratings.json"


def _load_ratings() -> dict:
    p = _ratings_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _save_ratings(ratings: dict) -> None:
    try:
        p = _ratings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(ratings, indent=2))
    except Exception:  # noqa: BLE001
        pass


def _erase_ratings() -> None:
    try:
        _ratings_path().unlink(missing_ok=True)
    except Exception:  # noqa: BLE001
        pass


def _tag_id(concept: str, level: str) -> str:
    return f"{concept}::{level}"


def _all_tags(matrix, taxonomy, concepts):
    """Resolve target tags once per session (file counts are stable)."""
    if "_fv_tags" not in st.session_state:
        st.session_state["_fv_tags"] = resolve_extreme_tags(matrix, taxonomy, concepts)
    return st.session_state["_fv_tags"]


def _render_file(midi_path: Path | None, stored_path: str) -> None:
    if midi_path and midi_path.exists():
        try:
            pm = pretty_midi.PrettyMIDI(str(midi_path))
            b64 = plot_inspector_roll_to_base64(pm, title=stored_path.split("/")[-1])
            st.markdown(
                f'<img src="data:image/png;base64,{b64}" '
                f'style="width:100%; border-radius:8px; border:1px solid #333; display:block;">',
                unsafe_allow_html=True,
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not render piano roll: {exc}")
        wav = midi_to_wav_bytes(midi_path)
        if wav:
            st.audio(wav, format="audio/wav")
        else:
            st.caption("Playback unavailable (FluidSynth / soundfont).")
    else:
        st.info(f"MIDI file not found: {midi_path}")


def _apply_filter(matrix, tags, taxonomy):
    out = matrix
    for concept, level in tags:
        col = f"{concept}_tag"
        if col not in out.columns:
            continue
        levels = (taxonomy.get(concept, {}).get("llm", {}) or {}).get("levels") or []
        idx = next((i for i, lv in enumerate(levels) if isinstance(lv, (list, tuple)) and len(lv) >= 2 and lv[1] == level), None)
        if idx is None:
            continue
        out = out[out[col] == idx]
    return out


def _render_explanation(taxonomy: dict[str, Any], concept: str, current_level: str) -> None:
    data = (taxonomy.get(concept, {}) or {}).get("llm", {}) or {}
    cat = data.get("category")
    sub = data.get("subcategory")
    text = feature_explanation(taxonomy, concept)
    with st.expander("About this feature", expanded=True):
        st.markdown(f"**{concept.replace('_', ' ')}**")
        if text:
            st.markdown(text)
        else:
            st.markdown("*No description yet.*")
        parts = [p for p in [cat, sub] if p]
        if parts:
            st.caption(" · ".join(parts))


def render(matrix, midi_root: Path | None, taxonomy: dict[str, Any]) -> None:
    st.header("Feature Validation")

    concepts = build_target_concepts(taxonomy)
    tags = _all_tags(matrix, taxonomy, concepts)
    by_concept: dict[str, list] = {}
    for tag in tags:
        by_concept.setdefault(tag["concept"], []).append(tag)
    concepts_with_tags = list(by_concept.keys())
    if not concepts_with_tags:
        st.info("No target tags resolved (no files in the database?).")
        return

    ratings = _load_ratings()
    combos = st.session_state.setdefault(COMBOS_KEY, [])
    rated = sum(1 for c in concepts_with_tags if all(_tag_id(t["concept"], t["level"]) in ratings for t in by_concept[c]))

    # ---- sidebar: navigation, level pick, tag combination ----
    default_idx = min(st.session_state.get("_fv_idx", 0), len(concepts_with_tags) - 1)
    with st.sidebar:
        st.markdown("### Target concept")
        concept = st.selectbox(
            "Concept",
            options=concepts_with_tags,
            index=default_idx,
            key="fv_concept_sel",
            label_visibility="collapsed",
            format_func=lambda c: f"✓ {c}" if all(_tag_id(t["concept"], t["level"]) in ratings for t in by_concept[c]) else c,
        )
        c1, c2 = st.columns(2)
        if c1.button("← Prev", key="fv_prev", disabled=default_idx == 0):
            st.session_state["_fv_idx"] = max(0, default_idx - 1)
            st.rerun()
        if c2.button("Next →", key="fv_next", disabled=default_idx >= len(concepts_with_tags) - 1):
            st.session_state["_fv_idx"] = min(len(concepts_with_tags) - 1, default_idx + 1)
            st.rerun()

        # Level pick (the resolved extreme levels for this concept)
        level_opts = by_concept[concept]
        labels = [f"{t['level']}  ({t['file_count']} files)" for t in level_opts]
        st.markdown("### Level")
        if len(level_opts) > 1:
            pick = st.radio("Level", options=range(len(labels)), format_func=lambda i: labels[i], key="fv_level_pick")
            level = level_opts[pick]["level"]
        else:
            level = level_opts[0]["level"]
            st.caption(labels[0])

        # Tag combination (AND)
        st.markdown("### Combine tags (AND)")
        other_concepts = [c for c in concepts_with_tags if c != concept]
        if combos:
            for combo in list(combos):
                cc, cl, cf = combo
                rc, rl = st.columns([4, 1])
                rc.caption(f"{cc}: {cl}")
                if rl.button("✕", key=f"rm_{cc}_{cl}"):
                    combos.remove(combo)
                    st.rerun()
        if other_concepts:
            combo_concept = st.selectbox("Add concept", other_concepts, key="fv_combo_concept")
            combo_opts = by_concept.get(combo_concept, [])
            if combo_opts:
                combo_label = [f"{t['level']}  ({t['file_count']} files)" for t in combo_opts]
                combo_i = st.selectbox("level", range(len(combo_label)), format_func=lambda i: combo_label[i], key="fv_combo_level")
                if st.button("Add", key="fv_combo_add"):
                    ct = combo_opts[combo_i]
                    combo = (combo_concept, ct["level"], ct["file_count"])
                    if combo not in combos:
                        combos.append(combo)
                    st.rerun()
        if combos and st.button("Clear all", key="fv_combo_clear"):
            combos.clear()
            st.rerun()

        st.caption(f"Rated: **{rated} / {len(concepts_with_tags)}**")

    # ---- main: explanation, live files for the active tag combination + rating ----
    active_tags = [(concept, level)] + [(c, l) for (c, l, _) in combos]
    filtered = _apply_filter(matrix, active_tags, taxonomy)
    n_files = len(filtered)

    _render_explanation(taxonomy, concept, level)

    st.subheader(f"{concept} — **{level}**")
    if combos:
        st.caption("AND " + " · ".join(f"{c}: {l}" for c, l, _ in combos))
    st.caption(f"**{n_files}** file(s) match the current tag combination.")

    if n_files == 0:
        st.warning("No files match this combination. Adjust the level or clear combo tags.")
    else:
        active_cols = [f"{c}_tag" for c, _ in active_tags if f"{c}_tag" in matrix.columns]
        # Cap the mosaic preview: rendering thousands of piano rolls for a common
        # tag hangs/crashes the browser (worse over a tunnel). The per-file list
        # below is for close inspection.
        mosaic = filtered.head(MOSAIC_MAX)
        visualizer.render(mosaic.reset_index(drop=True), midi_root, taxonomy, active_cols)

        st.subheader("Play a file")
        paths = filtered["path"].head(PLAY_LIST_MAX).tolist()
        sel = st.selectbox("File", paths, format_func=lambda p: p.split("/")[-1], key="fv_file_sel")
        _render_file(resolve_midi_path(sel, midi_root), sel)

    # rating for the primary tag
    st.divider()
    tid = _tag_id(concept, level)
    current = ratings.get(tid, {})
    rating = st.slider(
        "How well do these files match the tag's meaning?",
        min_value=1, max_value=5,
        value=current.get("rating", 3),
        key=f"fv_rating_{tid}",
        help="1 = files clearly do NOT match · 3 = uncertain / partial · 5 = files clearly match",
    )
    note = st.text_input("Note (optional)", value=current.get("note", ""), key=f"fv_note_{tid}")
    if st.button("Save rating", key=f"fv_save_{tid}"):
        ratings[tid] = {"rating": rating, "note": note, "tags": active_tags}
        _save_ratings(ratings)
        st.success("Saved.")

    if st.button("Export ratings (JSON)"):
        st.download_button(
            "Download ratings.json", data=json.dumps(ratings, indent=2),
            file_name="feature_validation_ratings.json", mime="application/json",
        )

    # Coordinator reset: start fresh for a new evaluator.
    with st.expander("Coordinator — reset for a new evaluator"):
        st.warning("This deletes ALL saved ratings (shared across evaluators).")
        if st.checkbox("I understand, I want to erase everything"):
            if st.button("Erase all ratings"):
                _erase_ratings()
                st.rerun()
