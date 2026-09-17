"""Natural-language search over the analyzed library via the LLM search engine."""

import re
from pathlib import Path
from typing import Any

import pretty_midi
import streamlit as st
from midi_llm_search_engine.llm_client import LLMTranslator
from midi_llm_search_engine.search import SearchError
from midi_llm_search_engine.prompt_builder import SystemPromptBuilder

from midi_exploration.combined import _corpus_prompt, corpus_search
from midi_exploration.playback import midi_to_wav_bytes
from midi_exploration.plotting.piano_rolls import plot_inspector_roll_to_base64
from midi_exploration.utils import resolve_midi_path
from midi_llm_search_engine import FileScorer, SearchEngine, SearchIndex

_STEP_RE = re.compile(r"\((\d+) step\(s\)")

_PROVIDERS = {
    "DeepSeek": "https://api.deepseek.com",
    "OpenAI": "https://api.openai.com/v1",
    "Mistral": "https://api.mistral.ai/v1",
    "Groq": "https://api.groq.com/openai/v1",
    "Together AI": "https://api.together.xyz/v1",
    "Fireworks AI": "https://api.fireworks.ai/v1",
    "Local (Ollama)": "http://localhost:11434/v1",
    "Custom": None,
}


@st.cache_resource(show_spinner=False)
def _get_index(db_path: str, taxonomy_path: str) -> SearchIndex:
    """Cache the (heavy) index; the engine is rebuilt per call with the key."""
    return SearchIndex(db_path, taxonomy_path)


@st.cache_resource(show_spinner=False)
def _get_system_prompt(db_path: str, taxonomy_path: str, semantic: bool) -> str:
    """Cache the system prompt string (deterministic for a given index+semantic).

    Only the prompt text is cached — never the key-holding translator — so a
    user-supplied key (BYOK) is never held in the cache.
    """
    return SystemPromptBuilder(_get_index(db_path, taxonomy_path)).build(
        include_semantic_analysis=semantic
    )


def _get_engine(db_path: str, taxonomy_path: str, semantic: bool, api_key: str = "",
                base_url: str | None = None, model: str | None = None) -> SearchEngine:
    """Build a search engine for the given DB + caller API key.

    The index and system prompt are built from the DB's own taxonomy
    (``<db_dir>/taxonomy.json``), exactly the way the system prompt is exported to
    ``system_prompt.txt`` — NOT from the project-settings taxonomy path (which may
    be empty/stale). The index and prompt are cached; the translator is rebuilt per
    call so a user-supplied key (BYOK) is never held in the cache.
    """
    db_tax = str(Path(db_path).parent / "taxonomy.json")
    index = _get_index(db_path, db_tax)
    prompt = _get_system_prompt(db_path, db_tax, semantic)
    translator = LLMTranslator(index, api_key=api_key or None,
                               base_url=base_url or None, model=model or None,
                               include_semantic_analysis=semantic, system_prompt=prompt)
    return SearchEngine(index, translator=translator, scorer=FileScorer(index))


def _run_corpus_search(query: str, api_key: str, base_url: str | None, model: str,
                        semantic: bool = False) -> Any:
    """Run a full-corpus search across ALL workspace libraries."""
    try:
        from midi_llm_search_engine.search import SearchError as _SE
        return corpus_search(query, api_key=api_key, base_url=(base_url or None),
                             model=(model or None), limit=20,
                             include_semantic_analysis=semantic)
    except _SE:
        raise
    except Exception as exc:
        raise SearchError(f"Failed to translate query {query!r}: {exc}") from exc


def _semantic_analysis(response) -> list[dict[str, Any]]:
    record = getattr(response, "llm_call_record", None)
    translation = getattr(record, "translation", None) if record else None
    return (translation.semantic_analysis or []) if translation else []


def _split_exact_fallback(reasons: list[str]) -> tuple[list[str], list[str]]:
    """Split matched concepts into exact matches (0 steps) vs fallback (>0)."""
    exact: list[str] = []
    fallback: list[str] = []
    for reason in reasons:
        concept = reason.split(":", 1)[0].strip()
        match = _STEP_RE.search(reason)
        steps = int(match.group(1)) if match else 0
        (exact if steps == 0 else fallback).append(concept)
    return exact, fallback


def _render_translation(response) -> None:
    st.subheader("A. LLM Translation")
    st.write(f"**Family classification:** `{response.instrument_family or 'n/a'}`")
    if not response.targets:
        st.info("No concept targets returned.")
        return
    rows = [
        {
            "concept": target.concept_name,
            "level": target.level_name,
            "importance": target.importance,
            "fallback": target.fallback,
        }
        for target in response.targets
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


def _render_raw(response) -> None:
    record = getattr(response, "llm_call_record", None)
    raw = getattr(record, "raw", None) if record else None
    if not raw:
        st.info("No raw LLM response recorded.")
        return
    st.subheader("B. Raw LLM Response")
    st.code(raw, language="json")


def _render_semantic(response) -> None:
    analysis = _semantic_analysis(response)
    st.subheader("C. Semantic Analysis")
    if not analysis:
        st.info("No query interpretation available. Enable query interpretation and re-run the search.")
        return
    rows = [
        {
            "concept": item.get("concept_name", ""),
            "level": item.get("level_name", ""),
            "why": item.get("why", ""),
        }
        for item in analysis
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


def _render_result_detail(result, midi_root: Path | None) -> None:
    st.write(f"### {result.file_path}")

    exact, fallback = _split_exact_fallback(result.match_reasons)
    c_score, c_raw, c_max, c_exact, c_fb = st.columns(5)
    c_score.metric("Score", f"{result.score:.3f}")
    c_raw.metric("Raw", f"{result.raw_score:.2f}")
    c_max.metric("Max", f"{result.max_possible:.1f}")
    c_exact.write(f"**Exact ({len(exact)}):**\n\n" + (", ".join(exact) if exact else "—"))
    c_fb.write(f"**Fallback ({len(fallback)}):**\n\n" + (", ".join(fallback) if fallback else "—"))

    midi_path = resolve_midi_path(result.file_path, midi_root)
    col_img, col_tag = st.columns([2, 1])
    with col_img:
        if midi_path and midi_path.exists():
            try:
                pm = pretty_midi.PrettyMIDI(str(midi_path))
                b64 = plot_inspector_roll_to_base64(pm, title=result.file_path)
                st.markdown(
                    f'<img src="data:image/png;base64,{b64}" '
                    f'style="width:100%; border-radius:8px; border:1px solid #333; display:block;">',
                    unsafe_allow_html=True,
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not render piano roll: {exc}")
            wav = midi_to_wav_bytes(midi_path) if midi_path and midi_path.exists() else None
            if wav:
                st.audio(wav, format="audio/wav")
            else:
                st.caption("Playback unavailable (FluidSynth / soundfont not set up).")
        else:
            st.info(f"MIDI file not found at: {midi_path}")

    with col_tag:
        st.subheader("D. File Tags")
        if result.all_tags:
            st.dataframe(
                [{"concept": k, "level": v} for k, v in result.all_tags.items()],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No tags.")


def render(db_path: str = "", taxonomy_path: str = "", midi_root: Path | None = None,
           api_key: str = "", base_url: str | None = None, model: str | None = None,
           corpus: bool = False, corpus_root: Path | None = None) -> None:
    st.header("Search")
    if not corpus and (not db_path or not Path(db_path).exists()):
        st.info("No database loaded. Import a library using the Input tab.")
        return
    if corpus:
        st.caption("Searching across ALL datasets (full corpus, not the 1000-file comparison pool).")
        search_root = corpus_root
    else:
        search_root = midi_root

    # --- search history for <- / -> navigation (results are cached, never re-run) ---
    history = st.session_state.setdefault("search_history", [])
    idx = st.session_state.get("search_index", -1)

    def _load(entry: dict) -> None:
        st.session_state["search_query"] = entry["query"]
        st.session_state["search_instructions"] = entry.get("instructions", "")
        st.session_state["search_semantic"] = entry["semantic"]
        st.session_state["search_response"] = entry["response"]

    col_back, col_fwd = st.columns([1, 1])
    if col_back.button("<-", disabled=not (idx > 0), key="_nav_back"):
        idx -= 1
        _load(history[idx])
    if col_fwd.button("->", disabled=not (0 <= idx < len(history) - 1), key="_nav_fwd"):
        idx += 1
        _load(history[idx])
    st.session_state["search_index"] = idx

    query = st.text_input(
        " ",
        label_visibility="collapsed",
        value=st.session_state.get("search_query", ""),
    )
    _show_instructions = st.toggle(
        "search instructions",
        value=bool(st.session_state.get("_search_show_instructions", False)),
    )
    st.session_state["_search_show_instructions"] = _show_instructions
    if _show_instructions:
        search_instructions = st.text_input(
            "search instructions",
            value=st.session_state.get("search_instructions", ""),
        )
    else:
        search_instructions = st.session_state.get("search_instructions", "")
    semantic_activation = st.toggle(
        'Show query interpretation ("why" column)',
        value=bool(st.session_state.get("search_semantic", False)),
    )

    if st.button("Search", type="primary"):
        if not query.strip():
            st.warning("Enter a query first.")
        else:
            # Provider / API config is entered below the button (session_state is
            # populated by Streamlit before this run).
            _key = st.session_state.get("_search_api_key", "") or api_key
            _provider = st.session_state.get("_search_provider", "DeepSeek")
            if _provider == "Custom":
                _base = st.session_state.get("_search_custom_url", "") or base_url or ""
            else:
                _base = _PROVIDERS.get(_provider) or base_url or ""
            _model = st.session_state.get("_search_model", "") or model or "deepseek-v4-flash"
            try:
                with st.spinner("Translating and scoring ..."):
                    full_query = query
                    if search_instructions.strip():
                        full_query = f"{query}\n{search_instructions.strip()}"
                    if corpus:
                        response = _run_corpus_search(full_query, _key, _base, _model, semantic=semantic_activation)
                    else:
                        engine = _get_engine(str(db_path), str(taxonomy_path), semantic_activation, _key, _base, _model)
                        response = engine.search(full_query, limit=20)
            except SearchError as exc:
                st.error(f"Search failed: {exc}")
                cause = getattr(exc, "__cause__", None)
                raw = getattr(cause, "raw", None)
                if raw:
                    st.code(f"RAW MODEL OUTPUT:\n{raw[:2000]}")
                st.session_state.pop("search_response", None)
                return
            # append as a new history entry, dropping any forward history
            entry = {"query": query, "instructions": search_instructions,
                     "semantic": semantic_activation, "response": response}
            history = history[: idx + 1] + [entry]
            idx = len(history) - 1
            st.session_state["search_history"] = history
            st.session_state["search_index"] = idx
            st.session_state["search_query"] = query
            st.session_state["search_instructions"] = search_instructions
            st.session_state["search_semantic"] = semantic_activation
            st.session_state["search_response"] = response

    # --- provider / API config + system prompt (shown below the Search button) ---
    _prov_list = list(_PROVIDERS.keys())
    _prov_default = st.session_state.get("_search_provider", "DeepSeek")
    _prov_idx = _prov_list.index(_prov_default) if _prov_default in _prov_list else 0
    st.text_input(
        "API key (OpenAI-compatible provider, bring your own)",
        type="password",
        value=st.session_state.get("_search_api_key", api_key),
        key="_search_api_key",
        help="Any OpenAI-compatible provider key. Leave empty to use the server-configured key or a local provider (e.g. Ollama).",
    )
    _provider = st.selectbox("Provider", _prov_list, index=_prov_idx, key="_search_provider")
    if _provider == "Custom":
        st.text_input(
            "Base URL",
            value=st.session_state.get("_search_custom_url", ""),
            key="_search_custom_url",
            help="Full OpenAI-compatible base URL, e.g. https://api.openai.com/v1.",
        )
    st.text_input(
        "Model",
        value=st.session_state.get("_search_model", "deepseek-v4-flash"),
        key="_search_model",
        help="The model name at the provider (e.g. deepseek-v4-flash, gpt-4o, llama3, etc.).",
    )

    with st.expander("Show system prompt"):
        if corpus:
            st.caption("Full-corpus index spans all libraries (system prompt merged from first available library).")
            _prompt = _corpus_prompt(semantic_activation)
            if _prompt:
                st.code(_prompt)
            else:
                st.info("No libraries loaded.")
        else:
            _db_tax = str(Path(db_path).parent / "taxonomy.json")
            st.write(f"DB: `{db_path}`")
            st.write(f"Taxonomy: `{_db_tax}`")
            _index = _get_index(str(db_path), _db_tax)
            _p = len(_index.concept_names_for_family("pitched", search_relevant_only=False))
            _d = len(_index.concept_names_for_family("drums", search_relevant_only=False))
            st.write(f"Active concepts — pitched: {_p}, drums: {_d}")
            st.code(_get_system_prompt(str(db_path), _db_tax, semantic_activation))

    response = st.session_state.get("search_response")
    if response is None:
        st.caption("Run a search to see results.")
        return

    _render_translation(response)

    if st.toggle("Show raw LLM response", value=False):
        _render_raw(response)
    if st.toggle("Show query interpretation", value=False):
        _render_semantic(response)

    st.subheader("Retrieved Files")
    if not response.results:
        st.info("No files matched.")
        return

    table = []
    for result in response.results:
        exact, fallback = _split_exact_fallback(result.match_reasons)
        table.append(
            {
                "file": result.file_path,
                "score": round(result.score, 3),
                "exact": len(exact),
                "fallback": len(fallback),
            }
        )
    st.dataframe(table, width="stretch", hide_index=True)

    selected = st.selectbox("Inspect a result", options=[r.file_path for r in response.results])
    for result in response.results:
        if result.file_path == selected:
            _render_result_detail(result, search_root)
            break
