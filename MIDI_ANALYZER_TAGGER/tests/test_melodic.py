import pretty_midi
from midi_analyzer_tagger.analysis import MidiData
from midi_analyzer_tagger.extractors.pitched.melodic import MelodicExtractor


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


NOTES = [
    (60, 0.0, 1.0),
    (64, 1.0, 2.0),
    (67, 2.0, 3.0),
    (60, 3.0, 4.0),
    (64, 4.0, 5.0),
    (67, 5.0, 6.0),
    (72, 6.0, 7.0),
    (48, 7.0, 8.0),
    (60, 8.0, 9.0),
    (60, 9.0, 10.0),
    (60, 10.0, 11.0),
    (67, 10.0, 11.0),
]


def test_melodic_extractor_empty_notes():
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(pretty_midi.Instrument(program=0))
    data = MidiData(midi)
    extractor = MelodicExtractor()
    raw = extractor.extract(data)

    expected = {
        "melodic_intervals_absolute_median_semitones": 0.0,
        "melodic_intervals_max_leap_semitones": 0,
        "melodic_intervals_pct_ascending": 0.0,
        "melodic_intervals_pct_descending": 0.0,
        "melodic_intervals_sequence_repetition_pct": 0.0,
        "melodic_interval_vocabulary_count": 0,
        "profile_melodic_intervals_pct_static": 0.0,
        "profile_melodic_intervals_pct_asc_13plus_semitones": 0.0,
        "profile_melodic_intervals_pct_desc_13plus_semitones": 0.0,
    }
    for i in range(1, 13):
        expected[f"profile_melodic_intervals_pct_asc_{i}_semitones"] = 0.0
        expected[f"profile_melodic_intervals_pct_desc_{i}_semitones"] = 0.0

    assert raw == expected
