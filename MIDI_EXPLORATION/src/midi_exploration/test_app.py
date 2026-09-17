"""Minimal test app to check library access."""
import sqlite3
from pathlib import Path

import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "MIDI_EXPLORATION" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "MIDI_LLM_SEARCH_ENGINE" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "MIDI_PREPROCESSOR" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "MIDI_ANALYZER_TAGGER" / "src"))

from midi_exploration.orchestrator import list_libraries, library_paths

st.set_page_config(page_title="Test App")
st.title("Test App")

libs = list_libraries()
st.write(f"Libraries found: {libs}")

if libs:
    sel = st.selectbox("Library", libs)
    st.write(f"Selected: {sel}")
    lp = library_paths(sel)
    st.write(f"DB: {lp['db_path']}")
    st.write(f"DB exists: {lp['db_path'].exists()}")
    
    if lp['db_path'].exists():
        conn = sqlite3.connect(str(lp['db_path']))
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        st.write(f"Tables: {tables}")
        st.write(f"Valid: {all(t in tables for t in ('files', 'tags', 'raw_features', 'normalized_features'))}")
    
    st.write(f"Midi root: {lp['midi_root']}")
    st.write(f"Midi root exists: {lp['midi_root'].exists()}")
    
    if lp['midi_root'].exists():
        mids = list(lp['midi_root'].rglob("*.mid"))[:3]
        st.write(f"Sample MIDIs: {[m.name for m in mids]}")
else:
    st.error("No libraries found!")
