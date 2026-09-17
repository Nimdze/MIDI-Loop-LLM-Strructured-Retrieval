import sys
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.common.rhythmic_density import RhythmicDensityExtractor


def _make_midi(onsets, pitch=60, duration=0.1):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for start in onsets:
        instrument.notes.append(
            pretty_midi.Note(
                velocity=100,
                pitch=pitch,
                start=start,
                end=start + duration,
            )
        )
    midi.instruments.append(instrument)
    return midi


def test_rhythmic_density_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = RhythmicDensityExtractor()
    raw = extractor.extract(data)

    assert raw == {
        "rhythmic_density_average_events_per_beat": 0.0,
        "rhythmic_density_burstiness": 0.0,
        "rhythmic_density_bar_to_bar_evolution": 0.0,
        "rhythmic_density_turnaround_shift": 0.0,
        "rhythmic_density_trend": 0.0,
    }


def test_rhythmic_density_extractor_matches_old_module():
    import os
    import sys
    from pathlib import Path

    env = os.getenv("MIDI_STAT_SRC")
    if not env:
        import pytest

        pytest.skip(
            "set MIDI_STAT_SRC to a legacy midi_stat_calculator 'src' directory "
            "to run this comparison"
        )
    old_root = Path(env)
    sys.path.insert(0, str(old_root))
    from extractor.common.rhythm import rhythmic_density as old_rhythmic_density

    onsets = [
        0.0,
        0.5,
        1.0,
        1.5,
        2.0,
        2.5,
        3.0,
        3.5,
        4.0,
        4.5,
        5.0,
        5.5,
        6.0,
        6.5,
        7.0,
        7.5,
        8.0,
        8.25,
        8.5,
        8.75,
        9.0,
        9.25,
        9.5,
        9.75,
        10.0,
        10.25,
        10.5,
        10.75,
        11.0,
        11.25,
        11.5,
        11.75,
    ]

    midi = _make_midi(onsets)
    midi.instruments[0].is_drum = False
    instrument = midi.instruments[0]

    old_raw = old_rhythmic_density.get_stats(instrument, midi)
    data = MidiData(midi)
    new_raw = RhythmicDensityExtractor().extract(data)

    expected_keys = [
        "rhythmic_density_average_events_per_beat",
        "rhythmic_density_burstiness",
        "rhythmic_density_bar_to_bar_evolution",
        "rhythmic_density_turnaround_shift",
        "rhythmic_density_trend",
    ]

    for key in expected_keys:
        assert new_raw[key] == old_raw[key], f"{key} mismatch: {new_raw[key]} != {old_raw[key]}"

    sys.path.pop(0)


def test_rhythmic_density_extractor_quantizes():
    midi = _make_midi([i * 0.5 for i in range(8)])
    data = MidiData(midi)
    extractor = RhythmicDensityExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert tags["rhythmic_density_average_events_per_beat"].name == "Moderately (not too) Busy"
