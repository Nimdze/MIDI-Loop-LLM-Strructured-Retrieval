import sys
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.common.duration import DurationExtractor


def _make_midi(durations: list[float], pitch: int = 60) -> pretty_midi.PrettyMIDI:
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    time = 0.0
    for duration in durations:
        instrument.notes.append(
            pretty_midi.Note(velocity=100, pitch=pitch, start=time, end=time + duration)
        )
        time += duration + 0.1
    midi.instruments.append(instrument)
    return midi


def test_duration_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = DurationExtractor()
    raw = extractor.extract(data)

    assert raw["duration_max_length_beats"] == 0.0
    assert raw["duration_short_profile"] == 0.0
    assert raw["duration_medium_profile"] == 0.0
    assert raw["duration_long_profile"] == 0.0


def test_duration_extractor_constant_eighth_notes():
    midi = _make_midi([0.25] * 8)
    data = MidiData(midi)
    extractor = DurationExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert raw["duration_8th_share"] == 100.0
    assert tags["duration_short_profile"].name == "Defining Short Duration"
    assert tags["duration_8th_share"].name == "Defining 8th Note Duration"
    assert raw["duration_max_length_beats"] == 0.5
    assert tags["duration_max_length_beats"].name == "Max Sustain 1/8-1/4 Bar"


def test_duration_extractor_long_chord():
    midi = _make_midi([2.0])
    data = MidiData(midi)
    extractor = DurationExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert raw["duration_max_length_beats"] == 4.0
    assert raw["duration_whole_share"] == 100.0
    assert tags["duration_long_profile"].name == "Defining Long Duration"
    assert tags["duration_max_length_beats"].name == "Contains Sustained Notes (1-2 Bars)"


def test_duration_extractor_matches_old_module_raw_values():
    old_root = Path(
        "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_STAT_NEW_CLEAN_V3 copy/midi_stat_calculator/src"
    )
    sys.path.insert(0, str(old_root))
    from extractor.common.rhythm import duration as old_duration

    midi = _make_midi([1.0, 0.25, 1.0, 0.25])
    midi.instruments[0].is_drum = False
    instrument = midi.instruments[0]

    old_raw = old_duration.get_stats(instrument, midi)
    data = MidiData(midi)
    extractor = DurationExtractor()
    new_raw = extractor.extract(data)

    assert new_raw["duration_max_length_beats"] == old_raw["duration_max_length_beats"]
    for _, old_key in [
        ("32nd", "duration_pct_32nd_range"),
        ("16th", "duration_pct_16th_range"),
        ("8th", "duration_pct_8th_range"),
        ("quarter", "duration_pct_quarter_range"),
        ("half", "duration_pct_half_range"),
        ("whole", "duration_pct_whole_range"),
        ("above_whole", "duration_pct_above_whole_range"),
    ]:
        new_key = old_key.replace("duration_pct_", "duration_").replace("_range", "_share")
        assert new_raw[new_key] == old_raw[old_key]

    sys.path.pop(0)
