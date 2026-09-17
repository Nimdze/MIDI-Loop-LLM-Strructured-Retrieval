import tempfile
from pathlib import Path

import pandas as pd
import pretty_midi

from midi_exploration.components.batch_export.exporter import export_filtered_files


def _write_midi(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    inst.notes.append(pretty_midi.Note(velocity=100, pitch=60, start=0, end=0.1))
    midi.instruments.append(inst)
    midi.write(str(path))


def test_export_filtered_files_copies_matching_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        root.mkdir()
        _write_midi(root / "a.mid")
        _write_midi(root / "b.mid")

        matrix = pd.DataFrame({
            "path": ["a.mid", "b.mid", "missing.mid"],  # last one intentionally missing
        })
        export_dir = Path(tmp) / "out"
        result = export_filtered_files(matrix, root, "my_export", export_dir)

        assert result["copied"] == 2
        assert result["skipped"] == 1
        assert "missing.mid" in result["missing"]
        assert (export_dir / "a.mid").exists()
        assert (export_dir / "b.mid").exists()
