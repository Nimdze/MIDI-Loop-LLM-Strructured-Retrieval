import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.common.grid import GridExtractor


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


def test_groove_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = GridExtractor()
    raw = extractor.extract(data)

    assert raw == {
        "groove_total_events": 0,
        "groove_swing_shuffle_ratio": 1.0,
        "grid_macro_jitter": None,
        "grid_micro_jitter": None,
        "grid_attempt_pct_odd1": None,
        "grid_success_pct_odd1": None,
        "grid_attempt_pct_even1": None,
        "grid_success_pct_even1": None,
        "grid_attempt_pct_beat3": None,
        "grid_success_pct_beat3": None,
        "grid_attempt_pct_2and4": None,
        "grid_success_pct_2and4": None,
        "grid_attempt_pct_offbeat": None,
        "grid_success_pct_offbeat": None,
    }


def test_groove_extractor_quantizes():
    midi = _make_midi([i * 0.25 for i in range(16)])
    data = MidiData(midi)
    extractor = GridExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert tags["groove_swing_shuffle_ratio"].name == "Straight (Even Subdivisions)"
    assert tags["grid_macro_jitter"].name == "Tight Macro Pocket"
    assert tags["grid_micro_jitter"].name == "Tight Micro Execution"
