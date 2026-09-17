# MIDI Inspection

Visualization and validation UI for analyzed MIDI libraries.

This package provides a Streamlit front end for the `MIDI_RETRIEVE` pipeline. It lets you import a folder of MIDI files, browse extracted features, inspect individual files, and inspect correlations between concepts.

## Running the app

From this directory:

```bash
streamlit run src/midi_exploration/app.py
```

The app relies on environment variables or the sidebar for the project database, MIDI root folder, and taxonomy path.

## Dependencies

Core dependencies are declared in `pyproject.toml` and include `streamlit`, `pandas`, `plotly`, `pretty_midi`, and `matplotlib`.

The **Input / Import** tab also requires the sibling packages:

- `midi_preprocessor`
- `midi_analyzer_tagger`

You can install them manually from the sibling directories:

```bash
.venv/bin/python -m pip install -e ../MIDI_PREPROCESSOR
.venv/bin/python -m pip install -e ../MIDI_ANALYZER_TAGGER
```

Or install the optional extra:

```bash
.venv/bin/python -m pip install -e ".[import]"
```

This assumes the sibling packages are editable installs available in the active environment.

## Workspace

Imported libraries are stored under `${HOME}/midi_exploration/workspace` by default. Override this location by setting the environment variable:

```bash
export MIDI_EXPLORATION_WORKSPACE="/path/to/workspace"
```

Persisted project settings are stored inside the workspace at `.state/settings.json`.

## Testing

```bash
.venv/bin/python -m pytest
```

## Project layout

- `app.py` — Streamlit entry point
- `pages/` — Tab pages: Input, Overview, Visualizer, Inspector, Correlations
- `components/` — Sidebar filters, charts, batch export, mixtape generation
- `loader.py` — Database loading utilities
- `plotting/` — Piano-roll and grid-debug matplotlib renderers
- `orchestrator.py` — ZIP import / analysis pipeline orchestration
