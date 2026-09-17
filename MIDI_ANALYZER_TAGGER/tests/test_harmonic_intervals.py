import sys
from pathlib import Path

import pretty_midi
import pytest
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.pitched.harmonic_intervals import HarmonicIntervalsExtractor


def _make_midi(notes):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for pitch, start, end in notes:
        instrument.notes.append(
            pretty_midi.Note(
                velocity=100,
                pitch=pitch,
                start=start,
                end=end,
            )
        )
    midi.instruments.append(instrument)
    return midi


def test_harmonic_intervals_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = HarmonicIntervalsExtractor()
    raw = extractor.extract(data)

    expected = {f"profile_harmonic_intervals_pct_{i:02d}_semitones": 0.0 for i in range(25)}
    expected.update(
        {
            "harmonic_perfect_consonance_pct": 0.0,
            "harmonic_imperfect_consonance_pct": 0.0,
            "harmonic_dissonance_pct": 0.0,
        }
    )

    assert raw == expected


def test_harmonic_intervals_extractor_matches_old_module():
    old_root = Path(
        "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_STAT_NEW_CLEAN_V3 copy/midi_stat_calculator/src"
    )
    sys.path.insert(0, str(old_root))
    from extractor.pitched.harmony import harmonic_intervals_profile as old_profile

    notes = [
        (60, 0.0, 2.0),
        (64, 0.0, 2.0),
        (67, 0.0, 2.0),
    ]

    midi = _make_midi(notes)
    midi.instruments[0].is_drum = False
    instrument = midi.instruments[0]

    old_raw = old_profile.get_stats(instrument, midi)
    data = MidiData(midi)
    new_raw = HarmonicIntervalsExtractor().extract(data)

    for key in old_raw:
        assert new_raw[key] == old_raw[key], f"{key} mismatch: {new_raw[key]} != {old_raw[key]}"

    sys.path.pop(0)


def test_harmonic_intervals_extractor_consonance_summary():
    notes = [
        (60, 0.0, 2.0),
        (64, 0.0, 2.0),
        (67, 0.0, 2.0),
    ]
    midi = _make_midi(notes)
    data = MidiData(midi)
    extractor = HarmonicIntervalsExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert raw["profile_harmonic_intervals_pct_03_semitones"] == pytest.approx(33.33, abs=0.01)
    assert raw["profile_harmonic_intervals_pct_04_semitones"] == pytest.approx(33.33, abs=0.01)
    assert raw["profile_harmonic_intervals_pct_07_semitones"] == pytest.approx(33.33, abs=0.01)
    assert raw["harmonic_perfect_consonance_pct"] == pytest.approx(33.33, abs=0.01)
    assert raw["harmonic_imperfect_consonance_pct"] == pytest.approx(66.66, abs=0.01)
    assert raw["harmonic_dissonance_pct"] == 0.0

    assert tags["harmonic_perfect_consonance_pct"].name == "Significant Perfect Consonance"
    assert tags["harmonic_imperfect_consonance_pct"].name == "Primary Imperfect Consonance"
    assert tags["harmonic_dissonance_pct"].name == "No Dissonance"
