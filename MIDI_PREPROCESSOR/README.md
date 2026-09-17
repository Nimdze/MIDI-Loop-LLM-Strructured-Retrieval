# MIDI Preprocessor

Preprocessing pipeline for MIDI files before analysis.

## Purpose

Clean and transform raw MIDI files into analyzable, single-instrument loops.

## Installation

```bash
cd MIDI_RETRIEVE/MIDI_PREPROCESSOR
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest tests/ -v
```

## CLI usage

```bash
python -m midi_preprocessor process path/to/raw --output path/to/clean
```

Options:

- `--target-bpm 120`: normalize tempo to 120 BPM.
- `--slice-bars 8`: slice files into segments of 8 bars.
- `--no-split`: do not split multi-instrument files by instrument.

## Modules

- `validators.py`: check that files are valid MIDI with notes.
- `splitter.py`: split a multi-instrument file into one file per instrument.
- `tempo_normalizer.py`: time-stretch notes to a target BPM.
- `slicer.py`: cut files into fixed-length slices.

## Workflow

```text
raw MIDI folder
  → validate
  → split instruments
  → normalize tempo (optional)
  → slice loops (optional)
  → clean MIDI folder
```

The output can then be passed to `MIDI_ANALYZER_TAGGER`.

## Output naming

Split files preserve the original filename and add an instrument suffix:

```text
input/Song_Bridge_01.mid
  → output/Song_Bridge_01_Acoustic Grand Piano.mid
  → output/Song_Bridge_01_Electric Bass.mid
  → output/Song_Bridge_01_Drums.mid
```

## Future integration

After preprocessing, run the analyzer to generate `analysis.db` and `taxonomy.json`.
