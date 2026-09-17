import tempfile
from pathlib import Path

import pretty_midi
import pytest

from midi_preprocessor.slicer import slice_midi


def _write_long_midi(path: Path, tempo: float = 120):
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)

    inst = pretty_midi.Instrument(program=0)
    seconds_per_beat = 60.0 / tempo
    total_beats = 65
    for i in range(total_beats):
        inst.notes.append(
            pretty_midi.Note(
                pitch=60,
                velocity=100,
                start=i * seconds_per_beat,
                end=i * seconds_per_beat + 0.4,
            )
        )
    midi.instruments.append(inst)
    midi.write(str(path))


def test_slice_midi_creates_multiple_slices():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "long.mid"
        output_folder = Path(tmpdir) / "out"
        _write_long_midi(input_path, tempo=120)

        written = slice_midi(input_path, output_folder, slice_bars=4, beats_per_bar=4)

        assert len(written) == 4
        for path in written:
            assert path.exists()


def test_slice_midi_preserves_time_signature():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "long.mid"
        output_folder = Path(tmpdir) / "out"

        midi = pretty_midi.PrettyMIDI(initial_tempo=120)
        midi.time_signature_changes = [pretty_midi.TimeSignature(3, 4, 0.0)]
        inst = pretty_midi.Instrument(program=0)
        for i in range(13):
            inst.notes.append(
                pretty_midi.Note(
                    pitch=60,
                    velocity=100,
                    start=i * 0.5,
                    end=i * 0.5 + 0.4,
                )
            )
        midi.instruments.append(inst)
        midi.write(str(input_path))

        written = slice_midi(input_path, output_folder, slice_bars=4)

        assert len(written) >= 1
        out = pretty_midi.PrettyMIDI(str(written[0]))
        assert out.time_signature_changes[0].numerator == 3
        assert out.time_signature_changes[0].denominator == 4


def test_slice_midi_preserves_pitch_bends_and_control_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "long.mid"
        output_folder = Path(tmpdir) / "out"
        path = Path(input_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        midi = pretty_midi.PrettyMIDI(initial_tempo=120)
        inst = pretty_midi.Instrument(program=0)
        seconds_per_beat = 0.5
        for i in range(65):
            inst.notes.append(
                pretty_midi.Note(
                    pitch=60,
                    velocity=100,
                    start=i * seconds_per_beat,
                    end=i * seconds_per_beat + 0.4,
                )
            )
        inst.pitch_bends = [pretty_midi.PitchBend(pitch=100, time=1.0)]
        inst.control_changes = [pretty_midi.ControlChange(number=7, value=100, time=2.0)]
        midi.instruments.append(inst)
        midi.lyrics = [pretty_midi.Lyric(text="hi", time=3.0)]
        midi.text_events = [pretty_midi.Text(text="hello", time=4.0)]
        midi.write(str(input_path))

        written = slice_midi(input_path, output_folder, slice_bars=4, beats_per_bar=4)

        assert len(written) >= 1
        out = pretty_midi.PrettyMIDI(str(written[0]))
        assert len(out.instruments[0].pitch_bends) == 1
        assert out.instruments[0].pitch_bends[0].pitch == 100
        assert out.instruments[0].pitch_bends[0].time == pytest.approx(1.0)
        assert len(out.instruments[0].control_changes) == 1
        assert out.instruments[0].control_changes[0].number == 7
        assert out.instruments[0].control_changes[0].time == pytest.approx(2.0)
        assert len(out.lyrics) == 1
        assert out.lyrics[0].text == "hi"
        assert out.lyrics[0].time == 3.0
        assert len(out.text_events) == 1
        assert out.text_events[0].text == "hello"
        assert out.text_events[0].time == 4.0