import numpy as np
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps
from midi_analyzer_tagger.quantizers import ShareholderQuantizer, TieredQuantizer

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]
ALL_DIATONIC_SCALES = []
for root in range(12):
    ALL_DIATONIC_SCALES.append(set((root + i) % 12 for i in MAJOR_INTERVALS))
    ALL_DIATONIC_SCALES.append(set((root + i) % 12 for i in MINOR_INTERVALS))

VOCABULARY_LEVELS = [
    Level("8+ Pitch Classes", 4),
    Level("5-7 Pitch Classes", 3),
    Level("2-4 Pitch Classes", 2),
    Level("1 Pitch Class", 1),
]

VOCABULARY_THRESHOLDS = [8, 5, 2]

DIATONIC_LEVELS = [
    Level("4-5 Out-of-Key Notes", 4),
    Level("2-3 Out-of-Key Notes", 3),
    Level("1 Out-of-Key Note", 2),
    Level("0 Out-of-Key Notes", 1),
]

DIATONIC_THRESHOLDS = [4, 2, 1]

DOMINANT_PITCH_LEVELS = [
    Level("Anchor Centered", 3),
    Level("Loosely Following Tonal Anchor", 2),
    Level("Straying From Tonal Anchor", 1),
]

DOMINANT_PITCH_THRESHOLDS = [45.0, 15.0]

VOCABULARY_TREND_LEVELS = [
    Level("Expanding Pitch Vocabulary", 3),
    Level("Stable Pitch Vocabulary", 2),
    Level("Contracting Pitch Vocabulary", 1),
]

VOCABULARY_TREND_THRESHOLDS = [0.30, -0.30]


class TonalityExtractor(FeatureExtractor):
    def __init__(self):
        concepts = [
            Concept(
                name="tonality_unique_pitches_count",
                category="tonality",
                family=["pitched"],
                levels=VOCABULARY_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=VOCABULARY_THRESHOLDS,
                    levels=VOCABULARY_LEVELS,
                ),
                description="Number of unique pitch classes (0-12).",
                llm_description="Number of unique pitch classes used in the file.",
                llm_interpretation="Use this for the pitch vocabulary — how many different pitch classes the part draws on. 1 = a drone or single-pitch focus; 2-4 = a small, limited set; 5-7 = a scale-sized set; 8+ = chromatic or wide-ranging.",
                llm_examples=["drone-like single pitch focus", "diatonic simple pitch vocabulary", "chromatic extended vocabulary"],
                llm_level_descriptions={
                    "1 Pitch Class": "A single pitch class — a drone or single-note focus.",
                    "2-4 Pitch Classes": "Two to four distinct pitch classes — a small, limited set.",
                    "5-7 Pitch Classes": "Five to seven distinct pitch classes — a scale-sized vocabulary.",
                    "8+ Pitch Classes": "Eight or more distinct pitch classes — chromatic or wide-ranging.",
                },
                llm_subcategory="tonality",
                scope="summary",
            ),
            Concept(
                name="tonality_out_of_key_notes",
                category="tonality",
                family=["pitched"],
                levels=DIATONIC_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=DIATONIC_THRESHOLDS,
                    levels=DIATONIC_LEVELS,
                ),
                description="Minimum number of unique notes that don't fit into any standard diatonic scale.",
                llm_description="How many notes fall outside a standard major/minor scale.",
                llm_interpretation="Use this for the 'spice'/chromaticism — how many unique notes fall outside a standard major/minor scale. 0 = strictly diatonic (fully in-key); 1 = a single chromatic note; 2-3 = noticeable chromaticism; 4-5 = heavily chromatic or near-atonal.",
                llm_examples=["mostly diatonic in key", "heavily chromatic out of key", "atonal no clear tonal center"],
                llm_level_descriptions={
                    "0 Out-of-Key Notes": "Every note fits a standard major or minor scale — strictly in-key, consonant.",
                    "1 Out-of-Key Note": "A single chromatic note outside the scale — mild spice.",
                    "2-3 Out-of-Key Notes": "A few chromatic notes outside the scale — noticeable chromaticism.",
                    "4-5 Out-of-Key Notes": "Many chromatic notes outside the scale — heavily chromatic or near-atonal.",
                },
                llm_subcategory="tonality",
                scope="summary",
            ),
            Concept(
                name="tonality_prevalent_pitch_pct",
                category="tonality",
                family=["pitched"],
                levels=DOMINANT_PITCH_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=DOMINANT_PITCH_THRESHOLDS,
                    levels=DOMINANT_PITCH_LEVELS,
                ),
                description="Percentage of duration spent on the most frequent pitch class.",
                llm_description="How strongly the melody/harmony is anchored to one pitch (tonal center).",
                llm_interpretation="Use this for how stable and focused the tonal center is. Strongly anchor-centered = a clear, drone-like tonal center; loosely following = some center but not dominant; straying = ambiguous or wandering tonality.",
                llm_examples=["strong tonal center anchored", "drone note holds throughout", "ambiguous wandering tonality"],
                llm_level_descriptions={
                    "Anchor Centered": "One pitch strongly dominates — a clear, stable tonal center.",
                    "Loosely Following Tonal Anchor": "A tonal center is present but not strongly dominant.",
                    "Straying From Tonal Anchor": "No strong tonal center — ambiguous or wandering.",
                },
                llm_subcategory="tonality",
                scope="summary",
            ),
            Concept(
                name="tonality_unique_pitches_count_trend",
                category="tonality",
                family=["pitched"],
                levels=VOCABULARY_TREND_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=VOCABULARY_TREND_THRESHOLDS,
                    levels=VOCABULARY_TREND_LEVELS,
                ),
                description="Change in pitch variety between first and second half of the loop.",
                llm_description="How the pitch vocabulary changes over time.",
                llm_interpretation="Use this for 'introducing new notes', 'expanding', or 'narrowing focus'. It compares the distinct pitch classes used in the first vs second half of the loop: expanding = noticeably more distinct notes in the second half (e.g. 3 → 6); contracting = noticeably fewer (e.g. 5 → 2); stable = a similar set throughout.",
                llm_examples=["pitch vocabulary expands over time", "more chromatic notes added", "narrows to a single pitch center"],
                llm_level_descriptions={
                    "Expanding Pitch Vocabulary": "Adds distinct pitch classes in the second half — the note set grows (e.g. going from 3 to 6 notes).",
                    "Stable Pitch Vocabulary": "Uses a similar number of distinct pitch classes in both halves.",
                    "Contracting Pitch Vocabulary": "Drops distinct pitch classes in the second half — the set narrows (e.g. going from 5 to 2 notes).",
                },
                llm_subcategory="tonality",
                scope="summary",
            ),
        ]

        super().__init__(
            "tonality",
            concepts,
            llm_description="Tonality describes the pitch collection, tonal center stability, and pitch vocabulary evolution.",
            llm_subcategory="tonality",
        )

    def extract(self, midi_data) -> dict:
        notes = midi_data.notes
        return _get_tonality(notes, midi_data.midi)


def _get_tonality(notes, midi):
    if not notes:
        return {
            "tonality_unique_pitches_count": 0,
            "tonality_out_of_key_notes": 0,
            "tonality_prevalent_pitch_pct": 0.0,
            "tonality_unique_pitches_count_trend": 0.0,
        }

    results = {}
    results.update(_get_note_variety(notes))
    results.update(_get_diatonic_purity(notes))
    results.update(_get_pitch_prevalence(notes))
    results.update(_get_pc_delta(notes, midi))
    return results


def _get_note_variety(notes):
    return {"tonality_unique_pitches_count": len(set(note["pitch"] % 12 for note in notes))}


def _get_diatonic_purity(notes):
    unique_pcs = set(note["pitch"] % 12 for note in notes)
    total = len(unique_pcs)
    if total == 0:
        return {"tonality_out_of_key_notes": 0}

    max_fit = max(len(unique_pcs.intersection(scale)) for scale in ALL_DIATONIC_SCALES)
    return {"tonality_out_of_key_notes": int(total - max_fit)}


def _get_pitch_prevalence(notes):
    pcp = np.zeros(12)
    for note in notes:
        pcp[note["pitch"] % 12] += note["end"] - note["start"]
    total = np.sum(pcp)
    if total == 0:
        return {"tonality_prevalent_pitch_pct": 0.0}
    return {"tonality_prevalent_pitch_pct": round(float((np.max(pcp) / total) * 100), 2)}


def _get_pc_delta(notes, midi):
    bps = get_bps(midi)
    start_beat = min(note["start"] * bps for note in notes)
    end_beat = max(note["end"] * bps for note in notes)
    dur = end_beat - start_beat
    if dur < 4.0:
        return {"tonality_unique_pitches_count_trend": 0.0}

    mid = start_beat + (dur / 2.0)
    first_half = set()
    second_half = set()
    for note in notes:
        note_start = note["start"] * bps
        if note_start < mid:
            first_half.add(note["pitch"] % 12)
        else:
            second_half.add(note["pitch"] % 12)

    delta = (np.log2(len(second_half)) if second_half else 0.0) - (np.log2(len(first_half)) if first_half else 0.0)
    return {"tonality_unique_pitches_count_trend": round(delta, 3)}
