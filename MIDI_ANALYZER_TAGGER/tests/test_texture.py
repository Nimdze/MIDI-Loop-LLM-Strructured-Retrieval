import sys
from pathlib import Path

import pretty_midi
import pytest
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.pitched.texture import TextureExtractor


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


def test_texture_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = TextureExtractor()
    raw = extractor.extract(data)

    expected = {
        "texture_pct_1_notes": 0.0,
        "texture_pct_2_notes": 0.0,
        "texture_pct_3_notes": 0.0,
        "texture_pct_4_notes": 0.0,
        "texture_pct_5_notes": 0.0,
        "texture_pct_6plus_notes": 0.0,
        "texture_monophonic_pct": 0.0,
        "texture_dyads_pct": 0.0,
        "texture_polyphonic_pct": 0.0,
        "texture_polyphonic_burst_rate": 0.0,
        "texture_polyphonic_burst_mean_duration_beats": 0.0,
        "texture_monophonic_median_pitch": 0.0,
        "texture_avg_wide_gaps_per_burst": 0.0,
    }

    assert raw == expected

    detail_names = {
        "texture_pct_3_notes",
        "texture_pct_4_notes",
        "texture_pct_5_notes",
        "texture_pct_6plus_notes",
        "texture_polyphonic_burst_rate",
        "texture_polyphonic_burst_mean_duration_beats",
        "texture_monophonic_median_pitch",
    }
    summary_names = {
        "texture_pct_1_notes",
        "texture_pct_2_notes",
        "texture_polyphonic_pct",
        "texture_avg_wide_gaps_per_burst",
    }
    for concept in extractor.concepts:
        if concept.name in detail_names:
            assert concept.scope == "detail"
            assert concept.default_weight > 0.0
        elif concept.name in summary_names:
            assert concept.scope == "summary"
            assert concept.default_weight > 0.0


def test_texture_summary_profiles_match_histogram():
    notes = [
        (60, 0.0, 0.5),
        (62, 0.5, 1.0),
        (60, 1.0, 1.5),
        (64, 1.0, 1.5),
        (48, 2.0, 3.0),
        (64, 2.0, 3.0),
        (72, 2.0, 3.0),
        (60, 3.5, 4.5),
        (72, 3.5, 4.5),
        (74, 3.5, 4.5),
    ]

    midi = _make_midi(notes)
    data = MidiData(midi)
    raw = TextureExtractor().extract(data)

    assert raw["texture_monophonic_pct"] == raw["texture_pct_1_notes"]
    assert raw["texture_dyads_pct"] == raw["texture_pct_2_notes"]
    assert raw["texture_polyphonic_pct"] == pytest.approx(
        raw["texture_pct_3_notes"]
        + raw["texture_pct_4_notes"]
        + raw["texture_pct_5_notes"]
        + raw["texture_pct_6plus_notes"],
        abs=0.01,
    )
