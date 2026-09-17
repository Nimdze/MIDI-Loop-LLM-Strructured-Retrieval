from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.common import dynamics, grid, rhythmic_density, spacing
from midi_analyzer_tagger.quantizers import ShareholderQuantizer

SHAREHOLDER_THRESHOLDS = [75.0, 50.0, 30.0, 20.0, 5.0, 0.0]


def _prevalence_levels(piece_name: str) -> list[Level]:
    return [
        Level(f"Defining {piece_name}", 5),
        Level(f"Primary {piece_name}", 4),
        Level(f"Significant {piece_name}", 3),
        Level(f"Present {piece_name}", 2),
        Level(f"Occasional {piece_name}", 1),
        Level(f"Negligible Presence", 0),
    ]


STEM_PITCHES = {
    "kick": [35, 36],
    "snare_clap": [37, 38, 39, 40],
    "hats_cymbals": [42, 44, 46, 49, 51, 52, 53, 55, 57, 59],
    "toms_others": [],
}

GM_DRUM_NAMES = {
    35: "Kick 1",
    36: "Kick 2",
    37: "Rimshot",
    38: "Snare 1",
    39: "Clap",
    40: "Snare 2",
    42: "Closed Hat",
    44: "Pedal Hat",
    46: "Open Hat",
    49: "Crash 1",
    51: "Ride 1",
    52: "Cymbal",
    53: "Ride 3",
    55: "Crash 1",
    57: "Crash 2",
    59: "Ride 2",
    41: "Low Floor Tom",
    43: "High Floor Tom",
    45: "Low Tom",
    47: "Low-Mid Tom",
    48: "Hi-Mid Tom",
    50: "High Tom",
}


class DrumRouterExtractor(FeatureExtractor):
    def __init__(self):
        self._stem_names = ["kick", "snare_clap", "hats_cymbals", "toms_others"]
        self._stem_extractors = {
            "spacing": spacing.SpacingExtractor(),
            "dynamics": dynamics.DynamicsExtractor(),
            "grid": grid.GridExtractor(),
            "rhythmic_density": rhythmic_density.RhythmicDensityExtractor(),
        }
        self._stem_compute = {
            "spacing": (spacing.compute_raw_features, spacing.empty_raw_features),
            "dynamics": (dynamics.compute_raw_features, dynamics.empty_raw_features),
            "grid": (grid.compute_raw_features, grid.empty_raw_features),
            "rhythmic_density": (rhythmic_density.compute_raw_features, rhythmic_density.empty_raw_features),
        }
        self._kit_concepts = _build_kit_concepts()

        concepts = []
        for stem_name in self._stem_names:
            for extractor in self._stem_extractors.values():
                concepts.extend(_build_stem_concepts(stem_name, extractor))
        concepts.extend(self._kit_concepts)
        super().__init__(
            "drum_router",
            concepts,
            llm_description="Drum analysis splits the kit into piece families (Kick, Snare/Clap, Hats/Cymbals, Toms/Others) and applies rhythm, spacing, dynamics, and grid metrics to each family. Kit prevalence describes which specific pieces are present.",
            llm_subcategory="rhythm",
        )

    def extract(self, midi_data) -> dict:
        notes = [note for note in midi_data.notes if note.get("is_drum", True)]
        if not notes:
            return self._empty_profile()

        stems = {name: [] for name in self._stem_names}
        for note in notes:
            stems[_get_stem(note["pitch"])].append(note)

        results = {}
        midi = midi_data.midi
        for stem_name in self._stem_names:
            stem_notes = stems[stem_name]
            if not stem_notes:
                # Family has no notes at all -> its features are absent (None),
                # NOT the "No X"/lowest level (that would wrongly imply the piece
                # exists but lacks the feature). Only prevalence records absence.
                continue
            for compute_fn, empty_fn in self._stem_compute.values():
                stem_raw = compute_fn(midi, stem_notes)
                for key, value in stem_raw.items():
                    results[f"drum_{stem_name}_{key}"] = value

        results.update(self._compute_kit_prevalence(notes))
        return results

    def _empty_profile(self):
        # No drum notes at all: every family is absent (features stay None); only
        # prevalence records that no piece is present.
        return {concept.name: 0.0 for concept in self._kit_concepts}

    def _compute_kit_prevalence(self, notes):
        family_counts = {name: {} for name in self._stem_names}

        for note in notes:
            pitch = note["pitch"]
            stem = _get_stem(pitch)
            raw_name = GM_DRUM_NAMES.get(pitch)
            if raw_name is None:
                continue
            clean_name = _clean_name(raw_name)
            family_counts[stem][clean_name] = family_counts[stem].get(clean_name, 0) + 1

        # Prevalence is relative to the WHOLE kit (all piece onsets), so a piece's
        # share reflects how much of the overall performance it is.
        total_kit = sum(sum(counts.values()) for counts in family_counts.values())

        results = {
            concept.name: 0.0 for concept in self._kit_concepts
        }
        if total_kit == 0:
            return results
        for stem, counts in family_counts.items():
            for clean_name, count in counts.items():
                key = f"drum_prevalence_{stem}_{clean_name}"
                if key in results:
                    results[key] = round((count / total_kit) * 100.0, 2)
        # Whole-family aggregate prevalence (share of the whole kit).
        for stem, counts in family_counts.items():
            key = f"drum_prevalence_{stem}"
            if key in results:
                results[key] = round((sum(counts.values()) / total_kit) * 100.0, 2)
        return results


def _get_stem(pitch):
    if pitch in STEM_PITCHES["kick"]:
        return "kick"
    if pitch in STEM_PITCHES["snare_clap"]:
        return "snare_clap"
    if pitch in STEM_PITCHES["hats_cymbals"]:
        return "hats_cymbals"
    return "toms_others"


def _clean_name(name):
    return name.lower().replace(" ", "_").replace("-", "_")



def _build_stem_concepts(stem_name, extractor):
    """Build drum-prefixed concepts, localizing llm_examples to the stem."""
    stem_display = {
        "kick": "the kick",
        "snare_clap": "the snare/clap",
        "hats_cymbals": "the hats/cymbals",
        "toms_others": "the toms",
    }.get(stem_name, stem_name)

    concepts = []
    for concept in extractor.concepts:
        paired = None
        if concept.pair_with:
            paired = f"drum_{stem_name}_{concept.pair_with}"
        
        # Localize examples: prepend the kit-piece family so the example unambiguously
        # routes to this piece (e.g. "the hats/cymbals attacks land on every eighth note").
        # Read as possessive: "the hats/cymbals' attacks land ...". Without the family
        # prefix the model can't tell which kit piece an example refers to (false negatives).
        local_examples = None
        if concept.llm_examples:
            local_examples = [f"{stem_display} {ex}" for ex in concept.llm_examples]

        concepts.append(
            Concept(
                name=f"drum_{stem_name}_{concept.name}",
                category=concept.category,
                family=["drums"],
                levels=concept.levels,
                quantizer=concept.quantizer,
                description=f"[{stem_name}] {concept.description}",
                llm_description=concept.llm_description and f"[{stem_name}] {concept.llm_description}",
                llm_interpretation=concept.llm_interpretation and f"[{stem_name}] {concept.llm_interpretation}",
                llm_examples=local_examples,
                llm_level_descriptions=concept.llm_level_descriptions,
                llm_subcategory=concept.llm_subcategory,
                scope=concept.scope,
                default_weight=concept.default_weight,
                mutually_exclusive=concept.mutually_exclusive,
                pair_with=paired,
                pair_role=concept.pair_role,
            )
        )
    return concepts


def _build_kit_concepts():
    family_to_names = {
        "kick": set(),
        "snare_clap": set(),
        "hats_cymbals": set(),
        "toms_others": set(),
    }
    for pitch, name in GM_DRUM_NAMES.items():
        stem = _get_stem(pitch)
        family_to_names[stem].add(_clean_name(name))

    concepts = []

    family_display = {
        "kick": "Kick",
        "snare_clap": "Snare/Clap",
        "hats_cymbals": "Hats/Cymbals",
        "toms_others": "Toms/Others",
    }
    # Whole-family aggregate prevalence.
    for family in ["kick", "snare_clap", "hats_cymbals", "toms_others"]:
        display = family_display[family]
        levels = _prevalence_levels(display)
        concepts.append(
            Concept(
                name=f"drum_prevalence_{family}",
                category="drums",
                family=["drums"],
                levels=levels,
                quantizer=ShareholderQuantizer(
                    levels=levels,
                    thresholds=SHAREHOLDER_THRESHOLDS,
                ),
                description=f"Percentage of {display} hits within the whole kit.",
                llm_description=f"Prevalence of the whole {display} family within the kit.",
                llm_interpretation="Use this for whole-family kit queries like 'busy kick', 'lots of hats', or 'a snare-heavy groove'.",
                llm_examples=[
                    f"a {display.lower()}-heavy kit",
                    f"lots of {display.lower()} overall",
                    f"the {display.lower()} family dominates the groove",
                ],
                llm_level_descriptions={
                    **{
                        level.name: f"The {display} family makes up {SHAREHOLDER_THRESHOLDS[i]}% or more of the kit."
                        for i, level in enumerate(levels[:-1])
                    },
                    levels[-1].name: f"The {display} family is not present in the kit.",
                },
                llm_subcategory="prevalence",
                scope="summary",
                default_weight=1.0,
            )
        )

    for family in ["kick", "snare_clap", "hats_cymbals", "toms_others"]:
        for name in sorted(family_to_names[family]):
            display_name = name.replace("_", " ").title()
            levels = _prevalence_levels(display_name)
            concepts.append(
                Concept(
                    name=f"drum_prevalence_{family}_{name}",
                    category="drums",
                    family=["drums"],
                    levels=levels,
                    quantizer=ShareholderQuantizer(
                        levels=levels,
                        thresholds=SHAREHOLDER_THRESHOLDS,
                    ),
                    description=f"Percentage of {display_name} hits within the {family} family.",
                    llm_description=f"Prevalence of {display_name} within the {family} family.",
                    llm_interpretation="Use this for specific kit-piece queries like 'kick 2', 'busy closed hats', or 'prominent rim'.",
                    llm_examples=[
                        f"the {display_name} is prominent",
                        f"there's a lot of {display_name}",
                        f"{display_name} shows up frequently",
                    ],
                    llm_level_descriptions={
                        **{
                            level.name: f"{display_name} makes up {SHAREHOLDER_THRESHOLDS[i]}% or more of the {family} family."
                            for i, level in enumerate(levels[:-1])
                        },
                        levels[-1].name: f"{display_name} is not present in the {family} family.",
                    },
                    llm_subcategory="prevalence",
                    scope="summary",
                    default_weight=1.0,
                )
            )
    return concepts
