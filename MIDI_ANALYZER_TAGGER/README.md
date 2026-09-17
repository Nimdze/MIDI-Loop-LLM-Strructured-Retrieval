# MIDI Analyzer Tagger

Plugin-based MIDI feature extraction and tagging pipeline. This is the producer side of the MIDI retrieval system.

## Purpose

Analyze MIDI files, compute measurable musical features, quantize them into semantic tags, and store the results in a SQLite database plus a JSON taxonomy.

## Installation

```bash
cd MIDI_RETRIEVE/MIDI_ANALYZER_TAGGER
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest tests/ -v
```

## CLI usage

Analyze a single file:

```bash
python -m midi_analyzer_tagger analyze path/to/file.mid --output ./output
```

Analyze a folder recursively:

```bash
python -m midi_analyzer_tagger analyze-folder path/to/folder --output ./output
```

This produces:

- `output/analysis.db`
- `output/taxonomy.json`

## Architecture

### Core data model

- `Level`: one label inside a concept.
- `Concept`: a measurable musical dimension, e.g. `rhythmic_density`.
- `Quantizer`: maps raw feature values to `Level`s.
- `Normalizer`: maps raw feature values or levels to a normalized scalar.
- `FeatureExtractor`: plugin that defines concepts and implements `extract()`.

### Pipeline

```text
MIDI file
  → MidiData
  → ExtractorRegistry (filters by family)
  → FeatureExtractor.extract()
  → Concept.quantize()
  → Normalizer.normalize()
  → AnalysisPayload
  → SQLite database
```

### Plugin system

Extractors live in `src/midi_analyzer_tagger/extractors/`. Add a class to `PLUGINS` in `extractors/__init__.py`.

Example extractor:

```python
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.quantizers import ContinuousQuantizer


class MyExtractor(FeatureExtractor):
    def __init__(self):
        levels = [Level("Low", 1), Level("High", 2)]
        super().__init__("my_extractor", [
            Concept(
                name="my_feature",
                category="test",
                family=["pitched"],
                levels=levels,
                quantizer=ContinuousQuantizer([
                    (1.0, levels[0]),
                    (float("inf"), levels[1]),
                ]),
            )
        ])

    def extract(self, midi_data):
        return {"my_feature": 1.5}
```

## Output schema

The SQLite database contains: `files`, `tags`, `raw_features`, `normalized_features`.

The taxonomy JSON describes every concept, its levels, and global indices.

## Extending

To add a new feature:

1. Create a new `FeatureExtractor` in `extractors/`.
2. Add it to `PLUGINS`.
3. Run tests.

## Future consumers

- `MIDI_SEARCH_ENGINE`: reads `analysis.db` and `taxonomy.json`.
- `MIDI_EXPLORATION`: reads `analysis.db` for visualization and validation.
- GenLoop: reads a generated `search_index.json` and `taxonomy.js`.
