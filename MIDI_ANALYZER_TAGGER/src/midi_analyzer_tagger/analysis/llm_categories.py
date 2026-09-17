"""LLM-facing descriptions and interpretation guides for analyzer categories."""

from typing import Any


LLM_CATEGORY_METADATA: dict[str, dict[str, Any]] = {
    "metadata": {
        "description": "Core file-level descriptors: instrument identity, key, time signature, tempo, loop length.",
        "interpretation": (
            "Use these when the query explicitly references instrument type, musical key, time signature, "
            "or loop length. These are factual file attributes that complement musical-dimension concepts. "
            "Note: some of these features (other than instrument identity) may be unavailable or unreliable "
            "for a given file, so they may be missing from the taxonomy. If a concept is absent from the "
            "taxonomy, do not attempt to return or reason about it."
        ),
        "examples": ["bass", "synth", "piano", "key of C", "minor", "3/4", "120 bpm", "8 bars"],
    },
    "rhythm": {
        "description": "When and how often notes occur. Includes spacing (count-based metrics for distance between event onsets), duration (time-based metrics for how long events ring), rhythmic density (how many events there are and how they are distributed), and grid (positional accuracy and timing feel).",
        "interpretation": (
            "Queries about speed, busyness, gaps, pauses, note length, swing, or beat patterns belong here. "
            "Be precise: spacing measures a count-based histogram of distances between event onsets (short-biased), "
            "duration measures a time-based histogram of event lengths (long-biased), "
            "rhythmic density measures event count and distribution. "
            "Spacing is the 'motor'/drive (how often attacks start); duration is the 'sustain' (how long they ring). "
            "Synthesize them: spacing gives the attack rhythm; duration tells whether the space between attacks is "
            "filled with sound or is silence. Short duration = staccato with silent gaps (dense if spacing is tight, "
            "airy with open spaces if spacing is wide). Long duration fills the gaps: tight spacing + long sustain "
            "appears mainly in rolled chords / sustained arps / two-handed playing (rhythmic attacks that sustain); "
            "wide spacing + long sustain = continuous ambient/pads. "
            "For a 'fast' feel, prefer spacing and density; for 'sustained', use duration. "
            "GRID POSITION REASONING: attempt rate measures how often a position is played; "
            "success rate measures how accurately those attempts land. These must be considered together — "
            "\"nails\" implies high attempt AND high success, \"consistently misses\" implies high attempt AND low success, "
            "\"rarely plays\" implies low attempt. Always reason about both dimensions in the interpretation field. "
            "SYNCOPATION: for syncopation the relative approach should be taken — high success and high attempts on the "
            "offbeat could very well not mean a syncopated loop but a straight 8ths or a straight offbeat loop; syncopation "
            "is more related to a mixture of rhythmic values, uneven rhythmic distribution, partial grid omissions and "
            "partial failed attempts, commonly combined with high attempts and success on stronger beats such as odd1 "
            "and/or even1."
        ),
        "examples": [
            "busy",
            "sparse",
            "fast",
            "slow",
            "sustained",
            "staccato",
            "tight timing",
            "swing",
            "four-on-the-floor",
            "backbeat",
            "off-beat",
            "syncopated",
        ],
    },
    "voicing": {
        "description": "Vertical pitch layout — how many notes sound together (texture: monophonic, dyads, polyphonic, etc), which HARMONIC interval distances are used between chord tones (e.g. fifths, octaves, tritones), and what pitch range (register) the voicing occupies.",
        "interpretation": (
            "Queries about the vertical arrangement of music: chord density, voicing width, harmonic interval quality, "
            "and register placement belong here. These are grouped together because they correlate: as the number of "
            "voices grows or the largest harmonic interval grows, the register range (highest minus lowest note) "
            "naturally widens. "
            "Unless directed otherwise (or a mixture of the two), \"harmonic\", \"harmony\" etc. describe polyphonic "
            "textures (3+ notes sounding together), while \"melodic\"/\"melody\" etc. describe monophonic textures "
            "(1 note at a time)."
        ),
        "examples": [
            "wide open voicing chords",
            "dense close-position voicing in the mid-register",
            "low register bass",
            "soprano register",
            "monophonic texture",
            "triads",
            "chords built on stacked fifths",
            "voicings with many simultaneous notes",
        ],
    },
    "melody": {
        "description": "Linear aspects of a single line: melodic motion size, direction, repetition, complexity, and which melodic intervals are used.",
        "interpretation": (
            "Queries about a melody's shape, stepwise vs. leaping, rising vs. falling, repetition, or interval palette belong here. "
            "Melody is about the horizontal relationship between consecutive notes, not the vertical chordal voicing."
        ),
        "examples": [
            "stepwise",
            "scalar",
            "leaps",
            "jumps",
            "rising melody",
            "falling pitch",
            "ascending",
            "descending",
            "melodically repetitive",
            "motivic",
            "flowing melodic contour",
            "complex melody",
            "simple melody",
            "melodic fifths",
            "ascending thirds",
            "descending fourths",
            "octave leaps",
        ],
    },
    "dynamics": {
        "description": "How loud or accented the notes are: average velocity, dynamic range, accent presence, and velocity trends over time.",
        "interpretation": (
            "Queries about loudness, softness, accent emphasis, dynamic variation, or intensity building/fading belong here. "
            "Velocity is a proxy for loudness in MIDI."
        ),
        "examples": [
            "loud",
            "soft",
            "quiet",
            "accented",
            "dynamic",
            "consistent loudness",
            "building volume",
            "fading volume",
            "aggressive",
            "gentle",
        ],
    },
    "tonality": {
        "description": "Pitch vocabulary and tonal center behavior: number of unique pitches and how diatonic vs. chromatic the pitch collection is.",
        "interpretation": (
            "Queries about modal vs. chromatic, diatonic vs. atonal, tonal center, drone-like pitch focus, or pitch expansion belong here. "
            "This is about the pitch collection, not the rhythm or the chordal voicing."
        ),
        "examples": [
            "modal",
            "chromatic",
            "diatonic",
            "atonal",
            "tonal center",
            "drone",
            "tonally complex",
            "tonally simple",
        ],
    },
    "drums": {
        "description": "Percussion analysis. A router that separates the drum tracks into distinct kit piece families (Kick, Snare/Clap, Hats/Cymbals, Toms/Others) and analyzes each family separately with the rhythmic density, spacing, dynamics, and grid subcategories (note: duration is not computed per piece). Each family also has a prevalence subcategory describing which specific pieces are present.",
        "interpretation": (
            "Queries about drum patterns, beats, breaks, or specific kit pieces belong here. "
            "Think about kick/snare as anchors and hats/cymbals as timekeepers. Queries like 'four-on-the-floor' or 'backbeat' need grid analysis. "
            "When the query names a drum piece (e.g. 'kick', 'snare', 'hi-hat'), restrict the returned concepts to that piece's family."
        ),
        "examples": [
            "kick",
            "snare",
            "hats",
            "toms",
            "four on the floor drums",
            "backbeat",
            "off-beat hats",
            "breakbeat",
            "techno kick",
            "busy hi-hats",
        ],
    },
}


LLM_UNKNOWN_CATEGORY_DESCRIPTION: dict[str, Any] = {
    "description": "Concepts not covered by a known category.",
    "interpretation": "Use only if the query explicitly mentions this category.",
    "examples": [],
}


# Shared subcategory docs. The description may be overridden by the extractor's
# own llm_description (which is more concept-specific); interpretation and
# examples live here, once per subcategory.
LLM_SUBCATEGORY_METADATA: dict[str, dict[str, Any]] = {
    "rhythmic density": {
        "families": ["pitched", "drums"],
        "interpretation": (
            "How many events occur and how they are distributed over time. "
            "Use for busyness, sparsity, clustering, and whether density builds or evolves. "
            "Burstiness reveals rolls/fills vs a consistent flow; trend and turnaround reveal build-ups and breaks."
        ),
        "examples": ["very busy rhythm", "sparse feel", "density builds over time", "drum fill at the turnaround"],
    },
    "spacing": {
        "families": ["pitched", "drums"],
        "interpretation": (
            "Gaps between event onsets — how far apart attacks start. "
            "Spacing is the rhythmic 'motor' / drive. Distinguish from duration (how long notes ring — the sustain histogram) "
            "and from rhythmic density (how many events per beat; spacing is a time-unit based histogram). "
            "Short spacing = tight, driving; long spacing = wide, open. "
            "Max-silence measures actual dead air where no notes ring, distinct from the onset-gap histogram. "
            "Note: spacing is a count-based histogram, so it is short-biased — each gap counts equally, "
            "and short gaps outnumber long ones."
        ),
        "disambiguation": (
            "Extreme long-gap queries — \"extremely long\" / \"very very long gaps\" / \"spaces longer than a whole note\" / "
            "\"above whole note\" — "
            "use the specific spacing_above_whole_share bin. "
            "Non-extreme 'long' queries — \"long spacing\" / \"long silences\" / \"sparse\" (without \"extremely long\") — "
            "use the general spacing_long_profile aggregation. "
            "Max-silence (spacing_max_silence_beats) is complementary and should be used alongside the matching "
            "histogram choice: it measures true dead air where nothing rings, which helps tell whether long gaps "
            "are sustained notes or actual silence (the duration histogram is the main signal for that). "
            "Use it together with the relevant histogram bin or profile for queries about actual silence — "
            "\"biggest silence\" / \"maximum spacing\"."
        ),
        "examples": ["steady gaps", "8th note gaps", "half note gaps", "very very long gaps", "wide open spacing", "tightly packed attacks", "extremely long gaps"],
    },
    "duration": {
        "families": ["pitched"],
        "interpretation": (
            "How long notes are held or ring — the sustained character of the part, distinct from spacing (how far apart attacks start). "
            "Duration is a time-based histogram, so it is long-biased — long notes dominate the sustained time. "
            "Use for sustained vs staccato, long pads, or short plucks."
        ),
        "disambiguation": (
            "Long-sustain queries: 'sustained', 'pads', or 'long' (non-extreme) use the duration_long_profile aggregation. "
            "Notes sustained beyond a whole measure use the specific duration_above_whole_share bin (the proportion of durations exceeding a whole note). "
            "duration_max_length_beats is complementary — it is the single longest note (a ceiling on maximal length) and says nothing about the share of the other notes. "
            "It is for ceiling statements ('no note longer than X' / 'the longest note is …'). "
            "Do NOT use duration_max_length_beats to fulfill a specific 'no X sustains' negation (e.g. 'no half-note sustains', 'no eighth-note sustains'): "
            "it caps at X and therefore also excludes everything longer (X AND above), which is broader than the user asked. "
            "Use the specific share bin (e.g. duration_half_share, duration_8th_share) with its 'No X' negation level to exclude exactly that duration."
        ),
        "examples": ["long sustained notes", "short staccato plucks", "notes ring out", "half note sustain", "16th note durations", "whole note holds"],
    },
    "grid": {
        "families": ["pitched", "drums"],
        "description": "Timing accuracy — which beat positions are attacked and how accurately they land, plus overall timing feel.",
        "interpretation": (
            "Two dimensions: (1) positional accuracy — attempt = how often a position is played, "
            "success = how accurately those attempts land. Consider them together: 'nails it' = high attempt + high success. "
            "(2) timing feel — macro jitter (16th-level drift) and micro jitter (32nd-level precision). "
            "Jitter complements position metrics: a position can land accurately (high success) but drift overall (high jitter). "
            "Use for beat emphasis like backbeat, downbeats, off-beats, and for looseness/tightness of execution."
        ),
        "examples": ["nails the two and four", "hits the downbeats", "off-beat accents", "tight locked timing", "loose drifted feel", "misses the one"],
    },
    "texture": {
        "families": ["pitched"],
        "interpretation": (
            "How many notes sound at once — monophonic, dyads, or polyphonic voicings. "
            "Use for chord thickness, single-note lines, voicing openness, and the width of chordal spread. "
            "Voicings are labeled by note count (not implied harmony) — a 3-note voicing is not necessarily a triad. "
            "Queries naming a specific count (e.g. 'triads', '4-note chords', '5-voice voicings') map to the specific note-count bins."
        ),
        "examples": [
            "monophonic line",
            "two-note dyads",
            "thick polyphonic chords",
            "wide open voicings",
            "four-note chords",
            "six-note voicings",
        ],
    },
    "register": {
        "families": ["pitched"],
        "interpretation": (
            "Queries about vertical placement belong here. Map the central position with "
            "register_median_note_midi, the overall width with register_spread_semitones, "
            "the ceiling/floor with register_highest_note_midi / register_lowest_note_midi, "
            "and movement over time with register_boundary_shift_semitones."
        ),
        "examples": ["low register", "high register", "wide pitch range", "register shifts over time"],
    },
    "harmonic intervals": {
        "families": ["pitched"],
        "interpretation": (
            "Vertical intervals between simultaneously sounding notes (chord voicings). "
            "Use for consonance/dissonance character and specific interval sizes like fifths and octaves. "
            "This is vertical (chordal), not horizontal (melodic). "
            "Think macro character (perfect/imperfect/dissonant) plus micro vocabulary (the specific intervals). "
            "Semitone-to-interval reference (the XX_semitones suffix is the semitone count): "
            "00=unison, 01=minor second, 02=major second, 03=minor third, 04=major third, 05=perfect fourth, "
            "06=tritone/augmented fourth, 07=perfect fifth, 08=minor sixth, 09=major sixth, 10=minor seventh, "
            "11=major seventh, 12=octave, 13=minor ninth, 14=major ninth, 15=minor tenth, 16=major tenth, "
            "17=eleventh, 18=augmented eleventh, 19=minor twelfth, 20=twelfth/perfect twelfth, 21=minor thirteenth, "
            "22=major thirteenth, 23=minor fourteenth, 24=double octave. "
            "Map musical interval names to semitones exactly (e.g. perfect fourth = 05, perfect fifth = 07, "
            "octave = 12, minor twelfth = 19, double octave = 24)."
        ),
        "examples": ["dissonance", "perfect consonance", "open fifths", "dissonant seconds", "octave voicings"],
    },
    "melodic intervals": {
        "families": ["pitched"],
        "description": "Linear aspects of a single line: melodic motion size, direction, repetition, complexity, and which melodic intervals are used.",
        "interpretation": (
            "Queries about a melody's shape, stepwise vs. leaping, rising vs. falling, repetition, or interval palette belong here. "
            "Melody is about the horizontal relationship between consecutive notes, not the vertical chordal voicing. "
            "Semitone-to-interval reference (the XX_semitones suffix is the semitone count): "
            "01=minor second, 02=major second, 03=minor third, 04=major third, 05=perfect fourth, "
            "06=tritone, 07=perfect fifth, 08=minor sixth, 09=major sixth, 10=minor seventh, "
            "11=major seventh, 12=octave. "
            "Map musical interval names to semitones exactly (e.g. perfect fourth = 05, perfect fifth = 07, octave = 12)."
        ),
        "examples": [
            "stepwise",
            "scalar",
            "leaps",
            "jumps",
            "rising melody",
            "falling pitch",
            "ascending",
            "descending",
            "melodically repetitive",
            "motivic",
            "flowing melodic contour",
            "complex melody",
            "simple melody",
            "melodic fifths",
            "ascending thirds",
            "descending fourths",
            "octave leaps",
        ],
    },
    "dynamics": {
        "families": ["pitched", "drums"],
        "description": "How loud or accented the notes are: average velocity, dynamic range, accent presence, and velocity trends over time.",
        "interpretation": (
            "Queries about loudness, softness, accent emphasis, dynamic variation, or intensity building/fading belong here. "
            "Velocity is a proxy for loudness in MIDI."
        ),
        "examples": [
            "loud",
            "soft",
            "quiet",
            "accented",
            "dynamic",
            "consistent loudness",
            "building volume",
            "fading volume",
            "aggressive",
            "gentle",
        ],
    },
    "tonality": {
        "families": ["pitched"],
        "description": "Pitch vocabulary and tonal center behavior: number of unique pitches and how diatonic vs. chromatic the pitch collection is.",
        "interpretation": (
            "Queries about modal vs. chromatic, diatonic vs. atonal, tonal center, drone-like pitch focus, or pitch expansion belong here. "
            "This is about the pitch collection, not the rhythm or the chordal voicing."
        ),
        "examples": [
            "modal",
            "chromatic",
            "diatonic",
            "atonal",
            "tonal center",
            "drone",
            "tonally complex",
            "tonally simple",
        ],
    },
    "metadata": {
        "families": ["pitched", "drums"],
        "description": "Core file-level descriptors: instrument identity, key, time signature, tempo, loop length.",
        "interpretation": (
            "Use these when the query explicitly references instrument type, musical key, time signature, "
            "or loop length. These are factual file attributes that complement musical-dimension concepts. "
            "Note: some of these features (other than instrument identity) may be unavailable or unreliable "
            "for a given file, so they may be missing from the taxonomy. If a concept is absent from the "
            "taxonomy, do not attempt to return or reason about it."
        ),
        "examples": ["bass", "synth", "piano", "key of C", "minor", "3/4", "120 bpm", "8 bars"],
    },
    "prevalence": {
        "families": ["drums"],
        "interpretation": (
            "Which specific drum kit pieces are present in the file and how much they appear. "
            "Use when the query names a specific drum piece."
        ),
        "examples": ["snare 1 present", "lots of open hi-hats", "has a ride cymbal"],
    },
}
