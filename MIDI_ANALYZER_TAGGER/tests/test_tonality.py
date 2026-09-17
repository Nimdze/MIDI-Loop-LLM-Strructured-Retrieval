import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.pitched.tonality import TonalityExtractor

DIATONIC_NOTES_SHORT = [
    (60, 0.0, 0.5),
    (64, 0.5, 1.0),
    (67, 1.0, 1.5),
]


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


CHROMATIC_NOTES = [
    (60, 0.0, 0.5),
    (61, 0.5, 1.0),
    (62, 1.0, 1.5),
    (63, 1.5, 2.0),
    (66, 2.0, 2.5),
    (69, 2.5, 3.0),
    (70, 3.0, 3.5),
    (72, 3.5, 4.0),
    (75, 4.0, 4.5),
    (77, 4.5, 5.0),
    (80, 5.0, 5.5),
    (82, 5.5, 6.0),
]


def test_tonality_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = TonalityExtractor()
    raw = extractor.extract(data)

    expected = {
        "tonality_unique_pitches_count": 0,
        "tonality_out_of_key_notes": 0,
        "tonality_prevalent_pitch_pct": 0.0,
        "tonality_unique_pitches_count_trend": 0.0,
    }

    assert raw == expected
    assert all(concept.scope == "summary" for concept in extractor.concepts)


def test_tonality_extractor_matches_old_module_non_partitura_keys():
    old_root = Path(
        "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_STAT_NEW_CLEAN_V3 copy/midi_stat_calculator/src"
    )
    sys.path.insert(0, str(old_root))

    partitura_mock = ModuleType("partitura")
    musicanalysis_mock = SimpleNamespace(
        estimate_tonaltension=lambda note_array: {"cloud_diameter": [0.0], "tensile_strain": [0.0]}
    )
    partitura_mock.musicanalysis = musicanalysis_mock
    sys.modules["partitura"] = partitura_mock

    from extractor.pitched.tonality import tonality as old_tonality

    midi = _make_midi(CHROMATIC_NOTES)
    midi.instruments[0].is_drum = False
    instrument = midi.instruments[0]

    old_raw = old_tonality.get_stats(instrument, midi)
    data = MidiData(midi)
    new_raw = TonalityExtractor().extract(data)

    non_partitura_keys = [
        "tonality_unique_pitches_count",
        "tonality_out_of_key_notes",
        "tonality_prevalent_pitch_pct",
        "tonality_unique_pitches_count_trend",
    ]
    # The old module calls the concept dominant_pitch_pct; it was renamed to
    # prevalent_pitch_pct (to avoid clashing with music-theory "dominant").
    old_name = {"tonality_prevalent_pitch_pct": "tonality_dominant_pitch_pct"}
    for key in non_partitura_keys:
        old_key = old_name.get(key, key)
        assert new_raw[key] == old_raw[old_key], f"{key} mismatch: {new_raw[key]} != {old_raw[old_key]}"

    assert "tonality_melodic_complexity" not in new_raw
    assert "tonality_key_tension" not in new_raw

    sys.path.pop(0)
    sys.modules.pop("partitura", None)


def test_tonality_extractor_short_loop_trend_is_zero():
    midi = _make_midi(DIATONIC_NOTES_SHORT)
    data = MidiData(midi)
    raw = TonalityExtractor().extract(data)

    assert raw["tonality_unique_pitches_count_trend"] == 0.0


def test_tonality_extractor_diatonic_purity():
    midi = _make_midi(DIATONIC_NOTES_SHORT)
    data = MidiData(midi)
    raw = TonalityExtractor().extract(data)

    assert raw["tonality_out_of_key_notes"] == 0
