import tempfile
from pathlib import Path

import pretty_midi
import pytest

from midi_preprocessor.tempo_normalizer import normalize_tempo


def _write_midi_with_tempo(path: Path, tempo: float, notes_count: int = 4):
    path.parent.mkdir(parents=True, exist_ok=True)
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)

    inst = pretty_midi.Instrument(program=0)
    for i in range(notes_count):
        inst.notes.append(
            pretty_midi.Note(
                pitch=60,
                velocity=100,
                start=i * 0.5,
                end=i * 0.5 + 0.4,
            )
        )
    midi.instruments.append(inst)
    midi.write(str(path))


def test_normalize_tempo_stretches_notes():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.mid"
        output_path = Path(tmpdir) / "output.mid"
        _write_midi_with_tempo(input_path, tempo=60, notes_count=4)

        normalize_tempo(input_path, output_path, target_bpm=120)

        midi = pretty_midi.PrettyMIDI(str(output_path))
        note = midi.instruments[0].notes[0]
        assert note.end < 0.3  # note was stretched by 0.5 ratio


def test_normalize_tempo_preserves_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.mid"
        output_path = Path(tmpdir) / "output.mid"

        midi = pretty_midi.PrettyMIDI(initial_tempo=60)
        midi.time_signature_changes = [pretty_midi.TimeSignature(3, 4, 0.0)]
        inst = pretty_midi.Instrument(program=0)
        inst.notes.append(
            pretty_midi.Note(pitch=60, velocity=100, start=0, end=0.5)
        )
        midi.instruments.append(inst)
        midi.write(str(input_path))

        normalize_tempo(input_path, output_path, target_bpm=120)

        out = pretty_midi.PrettyMIDI(str(output_path))
        assert out.time_signature_changes[0].numerator == 3
        assert out.time_signature_changes[0].denominator == 4
        _, tempos = out.get_tempo_changes()
        assert tempos[0] == pytest.approx(120.0)


def test_normalize_tempo_preserves_and_scales_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.mid"
        output_path = Path(tmpdir) / "output.mid"

        midi = pretty_midi.PrettyMIDI(initial_tempo=60)
        inst = pretty_midi.Instrument(program=0)
        inst.notes.append(pretty_midi.Note(pitch=60, velocity=100, start=0, end=1.0))
        inst.pitch_bends = [pretty_midi.PitchBend(pitch=100, time=0.5)]
        inst.control_changes = [pretty_midi.ControlChange(number=7, value=100, time=0.75)]
        midi.instruments.append(inst)
        midi.lyrics = [pretty_midi.Lyric(text="hi", time=0.9)]
        midi.text_events = [pretty_midi.Text(text="hello", time=1.1)]
        midi.write(str(input_path))

        normalize_tempo(input_path, output_path, target_bpm=120)

        out = pretty_midi.PrettyMIDI(str(output_path))
        assert out.instruments[0].pitch_bends[0].time == pytest.approx(0.25)
        assert out.instruments[0].control_changes[0].time == pytest.approx(0.375)
        assert out.lyrics[0].time == pytest.approx(0.45)
        assert out.text_events[0].time == pytest.approx(0.55)
        assert out.lyrics[0].text == "hi"
        assert out.text_events[0].text == "hello"