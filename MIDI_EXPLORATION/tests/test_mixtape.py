import tempfile
from pathlib import Path

import pandas as pd
import pretty_midi

from midi_exploration.components.batch_export.mixtape import generate_mixtape


def _write_midi(path: Path, note_count: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    for i in range(note_count):
        inst.notes.append(
            pretty_midi.Note(velocity=100, pitch=60, start=i * 0.1, end=i * 0.1 + 0.05)
        )
    midi.instruments.append(inst)
    midi.write(str(path))


def test_generate_mixtape_creates_single_midi():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        root.mkdir()
        _write_midi(root / "a.mid", note_count=2)
        _write_midi(root / "b.mid", note_count=1)

        matrix = pd.DataFrame({"path": ["a.mid", "b.mid"]})
        destination = Path(tmp) / "out"

        result = generate_mixtape(matrix, root, destination, "my_export")
        assert result["output_path"] is not None
        assert result["output_path"].exists()
        assert result["included"] == 2
        assert result["skipped"] == 0

        combined = pretty_midi.PrettyMIDI(str(result["output_path"]))
        assert len(combined.instruments) == 1
        assert len(combined.instruments[0].notes) >= 3


def test_generate_mixtape_skips_missing_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        root.mkdir()
        _write_midi(root / "a.mid")

        matrix = pd.DataFrame({"path": ["a.mid", "missing.mid"]})
        destination = Path(tmp) / "out"

        result = generate_mixtape(matrix, root, destination, "export")
        assert result["output_path"] is not None
        assert result["included"] == 1
        assert result["skipped"] == 1
