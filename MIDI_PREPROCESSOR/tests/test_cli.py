import tempfile
from pathlib import Path

import pretty_midi

from midi_preprocessor.cli import main


def _write_multi_instrument_file(path: Path, tempo: float = 120, beats: int = 16):
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)

    piano = pretty_midi.Instrument(program=0)
    for i in range(beats):
        piano.notes.append(pretty_midi.Note(pitch=60, velocity=100, start=i * 0.5, end=i * 0.5 + 0.4))
    midi.instruments.append(piano)

    bass = pretty_midi.Instrument(program=32)
    for i in range(beats):
        bass.notes.append(pretty_midi.Note(pitch=40, velocity=100, start=i * 0.5, end=i * 0.5 + 0.4))
    midi.instruments.append(bass)

    midi.write(str(path))


def test_cli_process_splits_instruments():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_folder = Path(tmpdir) / "raw"
        input_folder.mkdir()
        _write_multi_instrument_file(input_folder / "multi_0.mid")

        output_folder = Path(tmpdir) / "clean"

        assert main(["process", str(input_folder), "--output", str(output_folder)]) == 0

        written = list(output_folder.rglob("*.mid"))
        assert len(written) >= 2