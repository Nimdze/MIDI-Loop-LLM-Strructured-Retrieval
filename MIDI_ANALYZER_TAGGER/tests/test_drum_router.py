import sys
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.drums.drum_router import DrumRouterExtractor

HAT_EIGHTHS = [
    (42, 0.00, 0.05),  # Closed Hat
    (42, 0.25, 0.30),
    (42, 0.50, 0.55),
    (42, 0.75, 0.80),
    (42, 1.00, 1.05),
    (42, 1.25, 1.30),
    (42, 1.50, 1.55),
    (42, 1.75, 1.80),
    (35, 0.00, 0.05),  # Kick on downbeat
    (38, 1.00, 1.05),  # Snare on beat 2
]

KICK_EIGHTHS = [
    (35, 0.00, 0.05),
    (35, 0.25, 0.30),
    (35, 0.50, 0.55),
    (35, 0.75, 0.80),
    (35, 1.00, 1.05),
    (35, 1.25, 1.30),
    (35, 1.50, 1.55),
    (35, 1.75, 1.80),
    (42, 1.25, 1.30),  # One hat to avoid empty hat stem
]


def _make_drum_midi(notes):
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0, is_drum=True)
    for pitch, start, end in notes:
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end))
    midi.instruments.append(inst)
    return midi


def _get_drum_data(notes):
    midi = _make_drum_midi(notes)
    return MidiData(midi)


DRUM_PITCHES = [
    (35, 0.00, 0.05),
    (38, 0.50, 0.55),
    (42, 0.25, 0.30),
    (42, 0.75, 0.80),
    (46, 1.00, 1.05),
    (50, 1.50, 1.55),
]


def test_drum_router_extractor_empty_drum_track():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0, is_drum=True))
    data = MidiData(midi)
    extractor = DrumRouterExtractor()
    raw = extractor.extract(data)

    assert all(concept.family == ["drums"] for concept in extractor.concepts)
    assert "drum_kick_rhythmic_density_average_events_per_beat" in raw
    assert raw["drum_kick_rhythmic_density_average_events_per_beat"] == 0.0
    assert raw["drum_hats_cymbals_groove_total_events"] == 0


def test_drum_router_extractor_hat_vs_kick_eighths():
    hat_data = _get_drum_data(HAT_EIGHTHS)
    kick_data = _get_drum_data(KICK_EIGHTHS)
    extractor = DrumRouterExtractor()

    hat_raw = extractor.extract(hat_data)
    kick_raw = extractor.extract(kick_data)

    hats_key = "drum_hats_cymbals_rhythmic_density_average_events_per_beat"
    kick_key = "drum_kick_rhythmic_density_average_events_per_beat"

    assert hat_raw[hats_key] > hat_raw[kick_key]
    assert kick_raw[kick_key] > kick_raw[hats_key]

    assert hat_raw["drum_prevalence_hats_cymbals_closed_hat"] == 100.0
    assert kick_raw["drum_prevalence_kick_kick_1"] == 100.0


def test_drum_router_extractor_kit_pieces_matches_old_module():
    old_root = Path(
        "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_STAT_NEW_CLEAN_V3 copy/midi_stat_calculator/src"
    )
    sys.path.insert(0, str(old_root))
    from extractor.drums import kit_pieces as old_kit_pieces

    midi = _make_drum_midi(DRUM_PITCHES)
    instrument = midi.instruments[0]

    old_raw = old_kit_pieces.get_stats(instrument, midi)
    data = MidiData(midi)
    new_raw = DrumRouterExtractor().extract(data)

    for key, value in old_raw.items():
        assert key in new_raw, f"new output missing key {key}"
        assert new_raw[key] == value, f"{key} mismatch: {new_raw[key]} != {value}"

    sys.path.pop(0)
