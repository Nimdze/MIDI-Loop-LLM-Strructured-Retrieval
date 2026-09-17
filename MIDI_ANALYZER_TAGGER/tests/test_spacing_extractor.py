import sys
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.common.spacing import SpacingExtractor


def _make_midi(onsets: list[float], pitch: int = 60) -> pretty_midi.PrettyMIDI:
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for start in onsets:
        instrument.notes.append(
            pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=start + 0.1)
        )
    midi.instruments.append(instrument)
    return midi


def test_spacing_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = SpacingExtractor()
    raw = extractor.extract(data)

    assert raw["spacing_max_silence_beats"] == 0.0
    assert raw["spacing_short_profile"] == 0.0
    assert raw["spacing_medium_profile"] == 0.0
    assert raw["spacing_long_profile"] == 0.0


def test_spacing_extractor_constant_quarters():
    onsets = [i * 1.0 for i in range(5)]
    midi = _make_midi(onsets)
    data = MidiData(midi)
    extractor = SpacingExtractor()
    raw = extractor.extract(data)
    tags = extractor.quantize(raw)

    assert raw["spacing_half_share"] == 100.0 or raw["spacing_quarter_share"] == 100.0
    assert raw["spacing_medium_profile"] == 100.0 or raw["spacing_long_profile"] == 100.0

    # Some summary profile concept should register a Defining level.
    has_defining = any(
        tags.get(f"spacing_{m}_profile") is not None
        and tags[f"spacing_{m}_profile"].name.startswith("Defining")
        for m in ("short", "medium", "long")
    )
    assert has_defining


def test_spacing_extractor_matches_old_module_raw_values():
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
    from extractor.common.rhythm import spacing as old_spacing

    onsets = [i * 0.5 for i in range(9)]
    midi = _make_midi(onsets)
    midi.instruments[0].is_drum = False
    instrument = midi.instruments[0]

    old_raw = old_spacing.get_stats(instrument, midi)
    data = MidiData(midi)
    extractor = SpacingExtractor()
    new_raw = extractor.extract(data)

    assert new_raw["spacing_max_silence_beats"] == old_raw["spacing_max_silence_beats"]
    assert new_raw["spacing_8th_share"] == old_raw["spacing_pct_8th_range"]
    assert new_raw["spacing_quarter_share"] == old_raw["spacing_pct_quarter_range"]
    assert new_raw["spacing_half_share"] == old_raw["spacing_pct_half_range"]

    sys.path.pop(0)
