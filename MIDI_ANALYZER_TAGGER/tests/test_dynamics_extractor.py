import pretty_midi
import pytest
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.common.dynamics import DynamicsExtractor


def _make_midi(velocities, pitch=60, step=0.25):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for i, velocity in enumerate(velocities):
        start = i * step
        instrument.notes.append(
            pretty_midi.Note(
                velocity=velocity,
                pitch=pitch,
                start=start,
                end=start + 0.1,
            )
        )
    midi.instruments.append(instrument)
    return midi


def test_dynamics_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = DynamicsExtractor()
    raw = extractor.extract(data)
    assert raw == {
        "dynamics_average_velocity": 0.0,
        "dynamics_accents_presence": 0.0,
        "dynamics_velocity_spread": 0.0,
        "dynamics_intensity_trend": 0.0,
        "dynamics_max_velocity": 0,
    }


def test_dynamics_extractor_constant_high_velocity_notes():
    velocities = [100] * 8
    midi = _make_midi(velocities)
    data = MidiData(midi)
    extractor = DynamicsExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert raw["dynamics_average_velocity"] == 100.0
    assert raw["dynamics_max_velocity"] == 100
    assert raw["dynamics_accents_presence"] == 0.0
    assert raw["dynamics_velocity_spread"] == 0.0
    assert raw["dynamics_intensity_trend"] == 0.0

    assert tags["dynamics_average_velocity"].name == "Hard/Aggressive Velocity"
    assert tags["dynamics_accents_presence"].name == "No Dynamic Accents"
    assert tags["dynamics_velocity_spread"].name == "Flat/Programmed Dynamics"
    assert tags["dynamics_intensity_trend"].name == "Stable Intensity"
    assert tags["dynamics_max_velocity"].name == "Maximum Velocity"


def test_dynamics_extractor_detects_accent_and_building_trend():
    velocities = [70] * 4 + [130] * 4
    midi = _make_midi(velocities)
    data = MidiData(midi)
    extractor = DynamicsExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert raw["dynamics_average_velocity"] == 100.0
    assert raw["dynamics_max_velocity"] == 130
    assert raw["dynamics_accents_presence"] == 30.0
    assert raw["dynamics_velocity_spread"] == pytest.approx(30.0, abs=0.1)
    assert raw["dynamics_intensity_trend"] > 45.0

    assert tags["dynamics_accents_presence"].name == "Contains Dynamic Accents"
    assert tags["dynamics_intensity_trend"].name == "Building Intensity"


def test_dynamics_extractor_fades_velocity():
    velocities = [130] * 4 + [70] * 4
    midi = _make_midi(velocities)
    data = MidiData(midi)
    extractor = DynamicsExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert raw["dynamics_intensity_trend"] < -45.0
    assert tags["dynamics_intensity_trend"].name == "Fading Intensity"


def test_dynamics_extractor_matches_old_module_raw_values():
    import sys
    from pathlib import Path

    old_root = Path(
        "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_STAT_NEW_CLEAN_V3 copy/midi_stat_calculator/src"
    )
    sys.path.insert(0, str(old_root))
    from extractor.common.expression import dynamics as old_dynamics

    velocities = [100] * 8
    midi = _make_midi(velocities)
    midi.instruments[0].is_drum = False
    instrument = midi.instruments[0]
    pm = midi

    old_raw = old_dynamics.get_stats(instrument, pm)
    data = MidiData(midi)
    extractor = DynamicsExtractor()
    new_raw = extractor.extract(data)

    assert new_raw["dynamics_average_velocity"] == old_raw["dynamics_average_velocity"]
    assert new_raw["dynamics_max_velocity"] == old_raw["dynamics_max_velocity"]
    assert new_raw["dynamics_velocity_spread"] == old_raw["dynamics_velocity_spread"]
    assert new_raw["dynamics_intensity_trend"] == old_raw["dynamics_intensity_trend"]

    sys.path.pop(0)
