import sys
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.common.metadata import MetadataExtractor


def _make_midi(instrument, key_sig=None, time_sig=None):
    midi = pretty_midi.PrettyMIDI()
    if key_sig is not None:
        midi.key_signature_changes.append(key_sig)
    if time_sig is not None:
        midi.time_signature_changes.append(time_sig)
    midi.instruments.append(instrument)
    return midi


def test_metadata_extractor_empty_midi():
    midi = pretty_midi.PrettyMIDI()
    data = MidiData(midi)
    extractor = MetadataExtractor()
    raw = extractor.extract(data)

    expected = {
        "metadata_note_count": 0,
        "metadata_midi_program_number": -1,
        "metadata_instrument_family": "Unknown",
        "metadata_tempo": 120.0,
        "metadata_original_tempo": 120.0,
        "metadata_time_sig_num": 4,
        "metadata_time_sig_den": 4,
        "metadata_root_key": "Unknown",
        "metadata_scale_type": "Unknown",
        "metadata_measures": 0.0,
        "metadata_rounded_measures": 0,
    }

    assert raw == expected

    detail_concepts = {
        "metadata_time_sig_num",
        "metadata_time_sig_den",
    }
    hidden_detail_concepts = {
        "metadata_midi_program_number",
        "metadata_tempo",
        "metadata_original_tempo",
        "metadata_measures",
        "metadata_rounded_measures",
    }
    hidden_summary_concepts = {
        "metadata_note_count",
    }
    summary_concepts = {
        "metadata_instrument_family",
        "metadata_root_key",
        "metadata_scale_type",
    }
    for concept in extractor.concepts:
        if concept.name in detail_concepts:
            assert concept.scope == "detail"
            assert concept.default_weight > 0.0
        elif concept.name in hidden_detail_concepts:
            assert concept.scope == "detail"
            assert concept.default_weight == 0.0
        elif concept.name in hidden_summary_concepts:
            assert concept.scope == "summary"
            assert concept.default_weight == 0.0
        elif concept.name in summary_concepts:
            assert concept.scope == "summary"
            assert concept.default_weight > 0.0
        else:
            raise AssertionError(f"Unexpected concept {concept.name}")


def test_metadata_extractor_matches_old_module():
    old_root = Path(
        "/Users/nimo2/Desktop/MIDI_SEARCH/MIDI_STAT_NEW_CLEAN_V3 copy/midi_stat_calculator/src"
    )
    sys.path.insert(0, str(old_root))
    from extractor.common.metadata import meta as old_meta

    instrument = pretty_midi.Instrument(program=5, is_drum=False)
    instrument.notes.append(
        pretty_midi.Note(velocity=100, pitch=60, start=0.0, end=1.0)
    )

    key_sig = pretty_midi.KeySignature(key_number=0, time=0.0)
    time_sig = pretty_midi.TimeSignature(numerator=4, denominator=4, time=0.0)
    midi = _make_midi(instrument, key_sig=key_sig, time_sig=time_sig)

    old_raw = old_meta.get_stats(instrument, midi)
    data = MidiData(midi)
    new_raw = MetadataExtractor().extract(data)

    keys_to_compare = [
        "metadata_midi_program_number",
        "metadata_instrument_family",
        "metadata_tempo",
        "metadata_original_tempo",
        "metadata_time_sig_num",
        "metadata_time_sig_den",
        "metadata_root_key",
        "metadata_scale_type",
        "metadata_measures",
        "metadata_rounded_measures",
    ]

    for key in keys_to_compare:
        assert new_raw[key] == old_raw[key], f"{key} mismatch: {new_raw[key]} != {old_raw[key]}"

    assert "metadata_duration_sec" not in new_raw

    sys.path.pop(0)
