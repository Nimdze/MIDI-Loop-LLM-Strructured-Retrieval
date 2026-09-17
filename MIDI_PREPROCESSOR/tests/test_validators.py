import tempfile
from pathlib import Path

import pretty_midi

from midi_preprocessor.validators import validate_midis


def _write_valid_midi(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    inst.notes.append(pretty_midi.Note(pitch=60, velocity=100, start=0, end=0.5))
    midi.instruments.append(inst)
    midi.write(str(path))


def test_validate_midis_finds_valid_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_valid_midi(root / "test.mid")
        valid, invalid = validate_midis(root)
        assert len(valid) == 1
        assert len(invalid) == 0