import sys
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.pitched.register import RegisterExtractor


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


def test_register_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = RegisterExtractor()
    raw = extractor.extract(data)

    assert raw == {
        "register_lowest_note_midi": 0,
        "register_highest_note_midi": 0,
        "register_median_note_midi": 0,
        "register_spread_semitones": 0.0,
        "register_boundary_shift_semitones": 0.0,
    }


def test_register_extractor_matches_old_module():
    old_root = Path(
        "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_STAT_NEW_CLEAN_V3 copy/midi_stat_calculator/src"
    )
    sys.path.insert(0, str(old_root))
    from extractor.pitched.harmony import register as old_register

    notes = [
        (60, 0.0, 0.5),
        (64, 0.5, 1.0),
        (72, 1.0, 1.5),
        (76, 1.5, 2.0),
        (48, 2.0, 2.5),
    ]

    midi = _make_midi(notes)
    midi.instruments[0].is_drum = False
    instrument = midi.instruments[0]

    old_raw = old_register.get_stats(instrument, midi)
    data = MidiData(midi)
    new_raw = RegisterExtractor().extract(data)

    # register_boundary_shift_semitones is intentionally different now: it measures
    # central-register (median) migration, not the old floor+ceiling shift sum.
    for key in old_raw:
        if key == "register_boundary_shift_semitones":
            continue
        assert new_raw[key] == old_raw[key], f"{key} mismatch: {new_raw[key]} != {old_raw[key]}"

    sys.path.pop(0)


def test_register_extractor_quantizes():
    notes = [
        (50, 0.0, 0.5),
        (64, 0.5, 1.0),
        (78, 1.0, 1.5),
        (80, 1.5, 2.0),
    ]
    midi = _make_midi(notes)
    data = MidiData(midi)
    extractor = RegisterExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert tags["register_lowest_note_midi"].name == "Register: Mid"
    assert tags["register_median_note_midi"].name == "Register: Upper-Mid"
    assert tags["register_highest_note_midi"].name == "Register: High"
    assert tags["register_spread_semitones"].name == "Medium Pitch Spread (1-3 Octaves)"
    assert tags["register_boundary_shift_semitones"].name == "Active Register Migration"


def test_register_extractor_shifting_boundary_shift():
    notes = [
        (60, 0.0, 1.0),
        (64, 1.0, 2.0),
    ]
    midi = _make_midi(notes)
    data = MidiData(midi)
    extractor = RegisterExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert tags["register_boundary_shift_semitones"].name == "Stable"
