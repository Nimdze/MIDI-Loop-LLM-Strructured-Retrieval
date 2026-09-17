import tempfile
from pathlib import Path

import pretty_midi
import pytest

from midi_preprocessor.splitter import split_instruments


def _write_multi_instrument_midi(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI()

    piano = pretty_midi.Instrument(program=0)
    for i in range(4):
        piano.notes.append(pretty_midi.Note(pitch=60 + i, velocity=100, start=i * 0.5, end=i * 0.5 + 0.4))
    midi.instruments.append(piano)

    bass = pretty_midi.Instrument(program=32)
    for i in range(4):
        bass.notes.append(pretty_midi.Note(pitch=40 + i, velocity=100, start=i * 0.5, end=i * 0.5 + 0.4))
    midi.instruments.append(bass)

    drums = pretty_midi.Instrument(program=0, is_drum=True)
    for i in range(4):
        drums.notes.append(pretty_midi.Note(pitch=36, velocity=100, start=i * 0.5, end=i * 0.5 + 0.1))
    midi.instruments.append(drums)

    midi.write(str(path))


def test_split_instruments_creates_one_file_per_instrument():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "multi.mid"
        output_folder = Path(tmpdir) / "out"
        _write_multi_instrument_midi(input_path)

        written = split_instruments(input_path, output_folder)

        assert len(written) == 3
        names = {p.name for p in written}
        assert any("Acoustic" in n or "Piano" in n for n in names)
        assert any("Bass" in n for n in names)
        assert any("Drums" in n for n in names)


def test_split_instruments_preserves_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "multi.mid"
        output_folder = Path(tmpdir) / "out"

        midi = pretty_midi.PrettyMIDI(initial_tempo=90)
        midi.time_signature_changes = [pretty_midi.TimeSignature(4, 4, 0.0)]
        piano = pretty_midi.Instrument(program=0)
        piano.notes.append(pretty_midi.Note(pitch=60, velocity=100, start=0, end=0.5))
        midi.instruments.append(piano)
        midi.write(str(input_path))

        written = split_instruments(input_path, output_folder)

        assert len(written) == 1
        out = pretty_midi.PrettyMIDI(str(written[0]))
        _, tempos = out.get_tempo_changes()
        assert tempos[0] == pytest.approx(90.0, rel=1e-4)
        assert out.time_signature_changes[0].numerator == 4
        assert out.time_signature_changes[0].denominator == 4


def test_split_instruments_preserves_pitch_bends_and_control_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "multi.mid"
        output_folder = Path(tmpdir) / "out"
        path = Path(input_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        midi = pretty_midi.PrettyMIDI(initial_tempo=120)
        inst = pretty_midi.Instrument(program=0)
        inst.notes.append(pretty_midi.Note(pitch=60, velocity=100, start=0, end=0.5))
        inst.pitch_bends = [pretty_midi.PitchBend(pitch=100, time=0.1)]
        inst.control_changes = [pretty_midi.ControlChange(number=7, value=100, time=0.2)]
        midi.instruments.append(inst)
        midi.lyrics = [pretty_midi.Lyric(text="hi", time=0.3)]
        midi.text_events = [pretty_midi.Text(text="hello", time=0.4)]
        midi.write(str(input_path))

        written = split_instruments(input_path, output_folder)

        assert len(written) == 1
        out = pretty_midi.PrettyMIDI(str(written[0]))
        assert len(out.instruments[0].pitch_bends) == 1
        assert out.instruments[0].pitch_bends[0].pitch == 100
        assert out.instruments[0].pitch_bends[0].time == pytest.approx(0.1)
        assert len(out.instruments[0].control_changes) == 1
        assert out.instruments[0].control_changes[0].number == 7
        assert out.instruments[0].control_changes[0].time == pytest.approx(0.2)
        assert len(out.lyrics) == 1
        assert out.lyrics[0].text == "hi"
        assert len(out.text_events) == 1
        assert out.text_events[0].text == "hello"