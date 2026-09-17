"""Evaluation instrument for the paper.

Two tasks:
  * Feature Validation - filter files by tags in the sidebar and watch the
    visualizer mosaic update in real time, so evaluators can judge whether a
    tag / tag combination points to musically-correct files.
  * Search (e2e) - natural-language search, ported from the main app.

Run:  streamlit run src/midi_exploration/eval_app.py
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from midi_exploration.loader import load_feature_matrix_cached
from midi_exploration.orchestrator import ensure_default_libraries, library_paths, list_libraries
from midi_exploration.pages import feature_validation, search
from midi_exploration.utils import resolve_midi_path

st.set_page_config(page_title="MIDI Evaluation", layout="wide")
st.title("MIDI Evaluation")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # MIDI_RETRIEVE/
_CANONICAL_TAXONOMY = _PROJECT_ROOT / "taxonomy.json"
_ALL_LABEL = "All Libraries"


def _db_is_valid(path: str) -> bool:
    if not path or not Path(path).exists():
        return False
    try:
        conn = sqlite3.connect(path)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        return {"files", "tags", "raw_features", "normalized_features"}.issubset(tables)
    except Exception:  # noqa: BLE001
        return False


def _load_library_matrix(label: str) -> tuple[pd.DataFrame, dict, Path | None]:
    """Load a single library's feature matrix, taxonomy, and midi root."""
    lp = library_paths(label)
    if lp is None:
        return pd.DataFrame(), {}, None
    tax = json.loads(lp["taxonomy_path"].read_text()) if lp["taxonomy_path"].exists() else {}
    matrix = load_feature_matrix_cached(str(lp["db_path"]), json.dumps(tax))
    return matrix, tax, lp["midi_root"]


def _clear_fv_state() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith("fv_") or k in ("_fv_tags", "_fv_idx", feature_validation.COMBOS_KEY):
            del st.session_state[k]
    # clean up combined symlink root
    _cleanup_combined_root()


def _cleanup_combined_root() -> None:
    key = "_combined_root"
    root = st.session_state.pop(key, None)
    if root:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


def _build_combined_root(library_map: dict[str, Path]) -> Path:
    """Create a temp dir with symlinks so paths from any library resolve correctly.

    DB paths are ``<library>/<subdir>/<file>`` and each library's ``midi_root`` is
    ``<workspace>/<library>/clean``.  We symlink ``<tmp>/<library>`` →
    ``<workspace>/<library>/clean/<library>`` so that ``resolve_midi_path`` finds
    every file under a single root.
    """
    key = "_combined_root"
    old = st.session_state.get(key)
    if old:
        import shutil
        shutil.rmtree(old, ignore_errors=True)
    root = Path(tempfile.mkdtemp(prefix="midi_combined_"))
    for lib, src in library_map.items():
        dst = root / lib
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src / lib, target_is_directory=True)
    st.session_state[key] = root
    return root


def _build_combined() -> tuple[pd.DataFrame, dict, Path]:
    """Concatenate all workspace libraries into one combined matrix / taxonomy."""
    combined_matrix: list[pd.DataFrame] = []
    merged_tax: dict = {}
    library_map: dict[str, Path] = {}
    for label in list_libraries():
        lp = library_paths(label)
        if lp is None:
            continue
        matrix, tax, _ = _load_library_matrix(label)
        if matrix.empty:
            continue
        matrix = matrix.copy()
        matrix.insert(0, "library", label)
        matrix["file_id"] = matrix["file_id"].apply(lambda fid, lb=label: f"{lb}_{fid}")
        combined_matrix.append(matrix)
        merged_tax.update(tax)
        library_map[label] = lp["midi_root"]
    if not combined_matrix:
        return pd.DataFrame(), {}, Path(".")
    combined_root = _build_combined_root(library_map)
    return pd.concat(combined_matrix, ignore_index=True), merged_tax, combined_root


ensure_default_libraries()

with st.sidebar:
    available = list_libraries()
    env_db = os.getenv("MIDI_RETRIEVE_DB", "")
    env_root = os.getenv("MIDI_RETRIEVE_ROOT", "")

    if env_db:
        st.caption(f"Using MIDI_RETRIEVE_DB override: `{env_db}`")
        sel_label = "__env_override__"
        _cur_root = Path(env_root) if env_root else None
        _cur_db = env_db
    else:
        lib_options = [_ALL_LABEL] + available if available else []
        prev = st.session_state.get("eval_library", _ALL_LABEL)
        prev_idx = lib_options.index(prev) if prev in lib_options else 0
        sel_label = st.selectbox("Library", lib_options, index=prev_idx, key="eval_library") if lib_options else None
        if sel_label and sel_label != _ALL_LABEL:
            lp = library_paths(sel_label)
            _cur_db = str(lp["db_path"]) if lp else None
            _cur_root = lp["midi_root"] if lp else None
        else:
            _cur_db = None
            _cur_root = None

    with st.expander("Override Paths", expanded=False):
        _override_db = st.text_input("Database path", value=(_cur_db or ""))
        _override_root = st.text_input("MIDI root folder", value=(str(_cur_root) if _cur_root else ""))

# Detect library change and clear feature-validation state
_last_label = st.session_state.get("_last_eval_label")
if sel_label != _last_label:
    _clear_fv_state()
    st.session_state["_last_eval_label"] = sel_label

# --- resolve sources ---
if _override_db.strip() and _db_is_valid(_override_db.strip()):
    # Manual override always wins
    src_db = _override_db.strip()
    src_root = Path(_override_root.strip()) if _override_root.strip() else None
    src_mode = "single"
elif env_db:
    src_db = env_db
    src_root = Path(env_root) if env_root else None
    src_mode = "single"
elif sel_label == _ALL_LABEL:
    src_mode = "all"
else:
    src_db = _cur_db
    src_root = _cur_root
    src_mode = "single"

# --- build matrix / taxonomy ---
if src_mode == "all":
    matrix, taxonomy, root_path = _build_combined()
    if matrix.empty:
        st.info("No libraries available. Import datasets via the main app first.")
        st.stop()
    first_lib = list_libraries()
    _search_db = str(library_paths(first_lib[0])["db_path"]) if first_lib else None
    _search_tax = str(library_paths(first_lib[0])["taxonomy_path"]) if first_lib else None
    _search_label = first_lib[0] if first_lib else None
else:
    if not _db_is_valid(src_db):
        st.info("No valid database. Import a library via the main app or enter a database path in the sidebar.")
        st.stop()
    root_path = src_root
    display_tax = None
    if _CANONICAL_TAXONOMY.exists():
        display_tax = _CANONICAL_TAXONOMY
    else:
        adjacent = Path(src_db).parent / "taxonomy.json"
        if adjacent.exists():
            display_tax = adjacent
    taxonomy = json.loads(display_tax.read_text()) if display_tax else {}
    matrix = load_feature_matrix_cached(src_db, json.dumps(taxonomy))
    if matrix.empty:
        st.info("Database is valid but contains no files.")
        st.stop()
    _search_db = src_db
    _search_tax = str(display_tax) if display_tax else str(Path(src_db).parent / "taxonomy.json")
    _search_label = sel_label

# Debug: verify a Dubstep file resolves
if src_mode == "all":
    _ds = matrix[matrix["library"] == "Dubstep"]
    if len(_ds):
        _p = _ds.iloc[0]["path"]
        _resolved = resolve_midi_path(_p, root_path)
        st.caption(f"All mode root: `{root_path}`  |  sample path: `{_p}`  |  resolved: `{_resolved}`  |  exists: `{_resolved.exists() if _resolved else 'N/A'}`")

tab_feat, tab_search = st.tabs(["Feature Validation", "Search"])

with tab_feat:
    feature_validation.render(matrix, root_path, taxonomy)

with tab_search:
    _search_root = None if src_mode == "all" else root_path
    api_key = st.text_input(
        "API key (OpenAI-compatible provider, bring your own)",
        type="password",
        value=st.session_state.get("_eval_api_key", ""),
        help="Any OpenAI-compatible provider key. Leave empty to use the server-configured key or a local provider (e.g. Ollama).",
    )
    st.session_state["_eval_api_key"] = api_key
    base_url = st.text_input(
        "Base URL (OpenAI-compatible)",
        value=os.getenv("MIDI_SEARCH_BASE_URL", "https://api.deepseek.com"),
        help="e.g. https://api.deepseek.com, https://api.openai.com/v1, or a local Ollama endpoint.",
    )
    model = st.text_input(
        "Model",
        value=os.getenv("MIDI_SEARCH_MODEL", "deepseek-v4-flash"),
        help="The model name at the provider (e.g. deepseek-v4-flash, gpt-4o, llama3, etc.).",
    )
    if src_mode == "all" and _search_db:
        st.caption(f"Search uses the first library ({_search_label}) index. Switch to a specific library for targeted search.")
        search.render(_search_db, _search_tax, _search_root, api_key=api_key, base_url=base_url, model=model)
    elif src_mode == "single":
        search.render(_search_db, _search_tax, _search_root, api_key=api_key, base_url=base_url, model=model)
    else:
        st.info("No library available for search.")
