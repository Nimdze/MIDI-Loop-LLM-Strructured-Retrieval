import pytest
import pretty_midi
from dataclasses import FrozenInstanceError

from midi_exploration.plotting.piano_rolls import (
    config,
    plot_inspector_roll_to_base64,
    plot_mosaic_roll_to_base64,
    plot_piano_roll_to_base64,
    renderer,
    styles,
)


def _make_midi(note_count: int = 5, drum: bool = False) -> pretty_midi.PrettyMIDI:
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0, is_drum=drum)
    for i in range(note_count):
        pitch = 60 + i if not drum else 35 + i
        inst.notes.append(
            pretty_midi.Note(velocity=100, pitch=pitch, start=i * 0.25, end=i * 0.25 + 0.1)
        )
    pm.instruments.append(inst)
    return pm


def test_config_is_frozen():
    cfg = config.PianoRollConfig()
    with pytest.raises(FrozenInstanceError):
        cfg.height = 5.0


def test_mosaic_render():
    pm = _make_midi()
    b64 = plot_mosaic_roll_to_base64(pm, title="mosaic")
    assert b64 is not None
    assert b64.startswith("iVBOR")


def test_inspector_render():
    pm = _make_midi()
    b64 = plot_inspector_roll_to_base64(pm, title="inspector")
    assert b64 is not None
    assert b64.startswith("iVBOR")


def test_backward_compatible_render():
    pm = _make_midi()
    b64 = plot_piano_roll_to_base64(pm, title="compat")
    assert b64 is not None
    assert b64.startswith("iVBOR")


def test_resolve_highlight_kick():
    pm = _make_midi(1, drum=True)
    notes = renderer._collect_notes(pm, config.PianoRollConfig(time_axis="seconds"))
    target, is_perc, family = renderer._resolve_highlight(notes, "kick")
    assert family == "kick"
    assert target == {35, 36}
    assert is_perc is False


def test_resolve_highlight_perc():
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0, is_drum=True)
    inst.notes.append(pretty_midi.Note(velocity=100, pitch=41, start=0, end=0.1))
    pm.instruments.append(inst)

    notes = renderer._collect_notes(pm, config.PianoRollConfig(time_axis="seconds"))
    target, is_perc, family = renderer._resolve_highlight(notes, "perc")
    assert is_perc is True
    assert target == set()
    assert family == "perc"


def test_resolve_highlight_no_family():
    pm = _make_midi(1, drum=True)
    notes = renderer._collect_notes(pm, config.PianoRollConfig(time_axis="seconds"))
    target, is_perc, family = renderer._resolve_highlight(notes, None)
    assert target == set()
    assert is_perc is False
    assert family is None


def test_pitched_in_drum_range_is_not_drum():
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0, is_drum=False)
    inst.notes.append(pretty_midi.Note(velocity=100, pitch=60, start=0, end=0.5))
    pm.instruments.append(inst)
    assert styles._is_drum_track(pm) is False
