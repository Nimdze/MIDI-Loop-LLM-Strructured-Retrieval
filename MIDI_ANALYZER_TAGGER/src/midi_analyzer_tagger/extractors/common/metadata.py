import logging
import math
import os

from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.quantizers import CategoricalQuantizer, RawValueQuantizer

logger = logging.getLogger(__name__)

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Hidden numeric metadata concepts store their exact value as the tag (see
# RawValueQuantizer). The levels list is only a placeholder for the taxonomy;
# the actual stored level is the raw value (e.g. "120" for tempo, "500" for
# note count).
RAW_VALUE_LEVELS = [Level("Value", 1)]

TIME_SIG_NUM_VALUES = list(range(1, 17))
TIME_SIG_NUM_LEVELS: dict[int, Level] = {v: Level(str(v), v) for v in TIME_SIG_NUM_VALUES}
TIME_SIG_NUM_DEFAULT = Level("Other", 0)

TIME_SIG_DEN_VALUES = [1, 2, 4, 8, 16, 32]
TIME_SIG_DEN_LEVELS: dict[int, Level] = {v: Level(str(v), v) for v in TIME_SIG_DEN_VALUES}
TIME_SIG_DEN_DEFAULT = Level("Other", 0)

PROGRAM_NUMBER_LEVELS: dict[int, Level] = {i: Level(str(i), i + 1) for i in range(0, 129)}
PROGRAM_NUMBER_DEFAULT = Level("Unknown", 0)

INSTRUMENT_FAMILIES = {
    "Piano": [0, 1, 2, 3, 4, 5, 6, 7],
    "Tonal Percussion": [8, 9, 10, 11, 12, 13, 14, 15],
    "Organ": [16, 17, 18, 19, 20, 21, 22, 23],
    "Guitar": [24, 25, 26, 27, 28, 29, 30, 31],
    "Bass": [32, 33, 34, 35, 36, 37, 38, 39],
    "Strings": [40, 41, 42, 43, 44, 45, 46, 47],
    "Strings Ensemble": [48, 49, 50, 51],
    "Choir/Voice": [52, 53, 54],
    "Orchestra Hit": [55],
    "Brass": [56, 57, 58, 59, 60, 61, 62, 63],
    "Reed": [64, 65, 66, 67, 68, 69, 70, 71],
    "Pipe": [72, 73, 74, 75, 76, 77, 78, 79],
    "Synth Lead": [80, 81, 82, 83, 84, 85, 86, 87],
    "Synth Pad": [88, 89, 90, 91, 92, 93, 94, 95],
    "Synth Effects": [96, 97, 98, 99, 100, 101, 102, 103],
    "Ethnic": [104, 105, 106, 107, 108, 109, 110, 111],
    "Percussive": [112, 113, 114, 115, 116, 117, 118, 119],
    "Sound Effects": [120, 121, 122, 123, 124, 125, 126, 127],
    "Drum Kit": [128],
}


def _get_instrument_family(prog_num):
    if prog_num < 0:
        return "Unknown"
    for family, programs in INSTRUMENT_FAMILIES.items():
        if prog_num in programs:
            return family
    return "Unknown"


INSTRUMENT_FAMILY_NAMES = list(INSTRUMENT_FAMILIES.keys()) + ["Unknown"]
INSTRUMENT_FAMILY_LEVELS = {name: Level(name, index + 1) for index, name in enumerate(INSTRUMENT_FAMILY_NAMES)}

KEY_NAMES = ["Unknown"] + PITCH_CLASSES
KEY_LEVELS = {name: Level(name, index + 1) for index, name in enumerate(KEY_NAMES)}

SCALE_NAMES = ["Unknown", "Major", "Minor"]
SCALE_LEVELS = {name: Level(name, index + 1) for index, name in enumerate(SCALE_NAMES)}


class MetadataExtractor(FeatureExtractor):
    def __init__(self):
        concepts = [
            Concept(
                name="metadata_note_count",
                category="metadata",
                family=["pitched", "drums"],
                levels=RAW_VALUE_LEVELS,
                quantizer=RawValueQuantizer(),
                description="Total number of notes in the file.",
                llm_description="Total note count from the MIDI file.",
                llm_interpretation="Use this for queries about density, sparsity, or note count. For grid-feature gating, use groove_total_events instead.",
                llm_examples=["a lot of notes in the loop", "very few notes total", "moderate number of events"],
                llm_subcategory="metadata",
                scope="summary",
                default_weight=0.0,
            ),
            Concept(
                name="metadata_midi_program_number",
                category="metadata",
                family=["pitched", "drums"],
                levels=list(PROGRAM_NUMBER_LEVELS.values()) + [PROGRAM_NUMBER_DEFAULT],
                quantizer=CategoricalQuantizer(
                    mapping=PROGRAM_NUMBER_LEVELS,
                    default=PROGRAM_NUMBER_DEFAULT,
                ),
                description="The raw General MIDI Program Number (0-128), where 128 indicates a drum kit.",
                llm_description="Exact MIDI program number — identifies the specific instrument patch from the General MIDI standard.",
                llm_interpretation="Return only for an explicitly named numbered patch or specific program (e.g. 'acoustic grand piano'). For general instruments like 'synth lead', use metadata_instrument_family.",
                llm_examples=["acoustic grand piano", "overdriven guitar", "synth brass"],
                llm_subcategory="metadata",
                scope="detail",
                default_weight=0.0,
            ),
            Concept(
                name="metadata_instrument_family",
                category="metadata",
                family=["pitched", "drums"],
                levels=list(INSTRUMENT_FAMILY_LEVELS.values()),
                quantizer=CategoricalQuantizer(
                    mapping=INSTRUMENT_FAMILY_LEVELS,
                ),
                description="Broad instrument family derived from the MIDI program number.",
                llm_description="Detected instrument family (e.g., Piano, Bass, Synth Lead, Drum Kit).",
                llm_interpretation="Default choice for instrument queries. Covers broad families: Piano, Guitar, Bass, Strings, Synth Lead, etc. Use metadata_midi_program_number only for a specific numbered patch.",
                llm_examples=["synth lead", "bass", "drums", "piano", "acoustic guitar", "strings"],
                llm_subcategory="metadata",
                scope="summary",
                default_weight=1.0,
                mutually_exclusive=True,
            ),
            Concept(
                name="metadata_tempo",
                category="metadata",
                family=["pitched", "drums"],
                levels=RAW_VALUE_LEVELS,
                quantizer=RawValueQuantizer(),
                description="Beats Per Minute (BPM) from the MIDI header or the normalized Target BPM if overridden.",
                scope="detail",
                default_weight=0.0,
            ),
            Concept(
                name="metadata_original_tempo",
                category="metadata",
                family=["pitched", "drums"],
                levels=RAW_VALUE_LEVELS,
                quantizer=RawValueQuantizer(),
                description="The BPM written in the MIDI header before normalization.",
                scope="detail",
                default_weight=0.0,
            ),
            Concept(
                name="metadata_time_sig_num",
                category="metadata",
                family=["pitched", "drums"],
                levels=list(TIME_SIG_NUM_LEVELS.values()) + [TIME_SIG_NUM_DEFAULT],
                quantizer=CategoricalQuantizer(
                    mapping=TIME_SIG_NUM_LEVELS,
                    default=TIME_SIG_NUM_DEFAULT,
                ),
                description="Time signature numerator.",
                llm_description="Time signature — number of beats per measure.",
                llm_interpretation="The numerator is the number of beats per measure. Match the exact value (e.g., 4 for 4/4, 3 for 3/4).",
                llm_examples=["four beats to the measure"],
                llm_subcategory="metadata",
                scope="detail",
                default_weight=1.0,
                pair_with="metadata_time_sig_den",
                pair_role="num",
            ),
            Concept(
                name="metadata_time_sig_den",
                category="metadata",
                family=["pitched", "drums"],
                levels=list(TIME_SIG_DEN_LEVELS.values()) + [TIME_SIG_DEN_DEFAULT],
                quantizer=CategoricalQuantizer(
                    mapping=TIME_SIG_DEN_LEVELS,
                    default=TIME_SIG_DEN_DEFAULT,
                ),
                description="Time signature denominator.",
                llm_description="Time signature — beat unit (4=quarter note, 8=eighth note).",
                llm_interpretation="The denominator is the beat unit value (4=quarter note, 8=eighth note). Match the exact value (e.g., 4 for quarter-note beat, 8 for eighth-note beat).",
                llm_examples=["quarter note as the beat unit"],
                llm_subcategory="metadata",
                scope="detail",
                default_weight=1.0,
                pair_with="metadata_time_sig_num",
                pair_role="den",
            ),
             Concept(
                 name="metadata_root_key",
                 category="metadata",
                 family=["pitched"],
                 levels=list(KEY_LEVELS.values()),
                 quantizer=CategoricalQuantizer(
                     mapping=KEY_LEVELS,
                 ),
                 description="Root key from file metadata.",
                 llm_description="Root pitch class from the MIDI key signature.",
                 llm_examples=["the tonal center is the note F"],
                 llm_subcategory="metadata",
                 scope="summary",
                 default_weight=1.0,
                 mutually_exclusive=True,
             ),
             Concept(
                 name="metadata_scale_type",
                 category="metadata",
                 family=["pitched"],
                 levels=list(SCALE_LEVELS.values()),
                 quantizer=CategoricalQuantizer(
                     mapping=SCALE_LEVELS,
                 ),
                 description="Scale type (Major/Minor) from file metadata.",
                 llm_description="Major or minor scale from the MIDI key signature.",
                 llm_examples=["the key signature indicates major mode"],
                 llm_subcategory="metadata",
                 scope="summary",
                 default_weight=1.0,
                 mutually_exclusive=True,
             ),
            Concept(
                name="metadata_measures",
                category="metadata",
                family=["pitched", "drums"],
                levels=RAW_VALUE_LEVELS,
                quantizer=RawValueQuantizer(),
                description="Exact length in musical bars.",
                scope="detail",
                default_weight=0.0,
            ),
            Concept(
                name="metadata_rounded_measures",
                category="metadata",
                family=["pitched", "drums"],
                levels=RAW_VALUE_LEVELS,
                quantizer=RawValueQuantizer(),
                description="Intended length in bars, rounded up.",
                scope="detail",
                default_weight=0.0,
            ),
        ]
        super().__init__(
            "metadata",
            concepts,
            llm_description="Basic facts about the file: instrument family, tempo, length, and time signature.",
            llm_subcategory="metadata",
        )

    def extract(self, midi_data) -> dict:
        midi = midi_data.midi
        if len(midi.instruments) > 1:
            logger.warning(
                "MetadataExtractor expects a single-instrument file, but %d instruments were found. "
                "Only the first instrument will be used.",
                len(midi.instruments),
            )
        first_instrument = midi.instruments[0] if midi.instruments else None

        return {
            "metadata_note_count": len(midi_data.notes) if midi_data.notes else 0,
            "metadata_midi_program_number": _calc_program_number(first_instrument),
            "metadata_instrument_family": _calc_instrument_family(first_instrument),
            "metadata_tempo": _calc_tempo(midi),
            "metadata_original_tempo": _calc_original_tempo(midi),
            "metadata_time_sig_num": _calc_time_sig_num(midi),
            "metadata_time_sig_den": _calc_time_sig_den(midi),
            "metadata_root_key": _calc_root_key(midi),
            "metadata_scale_type": _calc_scale_type(midi),
            "metadata_measures": _calc_measures(midi),
            "metadata_rounded_measures": _calc_rounded_measures(midi),
        }


def _calc_program_number(instrument):
    if instrument is None:
        return -1
    if instrument.is_drum:
        return 128
    return int(instrument.program)


def _calc_instrument_family(instrument):
    prog_num = _calc_program_number(instrument)
    return _get_instrument_family(prog_num)


def _calc_tempo(midi):
    if "TARGET_BPM" in os.environ:
        return float(os.environ["TARGET_BPM"])
    return _get_file_tempo(midi)


def _get_file_tempo(midi):
    _, tempos = midi.get_tempo_changes()
    return float(tempos[0]) if len(tempos) > 0 else 120.0


def _calc_original_tempo(midi):
    # The original tempo before normalization must come from the file itself,
    # not from the TARGET_BPM override that the preprocessor may have set.
    return _get_file_tempo(midi)


def _get_time_signature(midi):
    if midi.time_signature_changes:
        ts = midi.time_signature_changes[0]
        return ts.numerator, ts.denominator
    return 4, 4


def _calc_time_sig_num(midi):
    num, _ = _get_time_signature(midi)
    return int(num)


def _calc_time_sig_den(midi):
    _, den = _get_time_signature(midi)
    return int(den)


def _calc_root_key(midi):
    if not midi.key_signature_changes:
        return "Unknown"
    key_number = midi.key_signature_changes[0].key_number
    if key_number < 12:
        return PITCH_CLASSES[key_number]
    return PITCH_CLASSES[key_number - 12]


def _calc_scale_type(midi):
    if not midi.key_signature_changes:
        return "Unknown"
    key_number = midi.key_signature_changes[0].key_number
    return "Major" if key_number < 12 else "Minor"


def _calc_measures(midi):
    tempo = _calc_tempo(midi)
    ts_num = _calc_time_sig_num(midi)
    ts_den = _calc_time_sig_den(midi)
    duration = midi.get_end_time()

    if tempo <= 0:
        tempo = 120.0

    quarter_note_duration = 60.0 / tempo
    beat_duration = quarter_note_duration * (4.0 / ts_den)
    seconds_per_bar = beat_duration * ts_num

    return round(float(duration / seconds_per_bar), 3) if seconds_per_bar > 0 else 0.0


def _calc_rounded_measures(midi):
    measures = _calc_measures(midi)
    return int(math.ceil(measures - 0.1)) if measures > 0 else 0
