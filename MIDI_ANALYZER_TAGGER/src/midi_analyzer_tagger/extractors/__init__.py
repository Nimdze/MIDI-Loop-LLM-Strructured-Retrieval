from midi_analyzer_tagger.extractors.common.duration import DurationExtractor
from midi_analyzer_tagger.extractors.common.dynamics import DynamicsExtractor
from midi_analyzer_tagger.extractors.common.grid import GridExtractor
from midi_analyzer_tagger.extractors.common.metadata import MetadataExtractor
from midi_analyzer_tagger.extractors.common.rhythmic_density import RhythmicDensityExtractor
from midi_analyzer_tagger.extractors.common.spacing import SpacingExtractor
from midi_analyzer_tagger.extractors.drums.drum_router import DrumRouterExtractor
from midi_analyzer_tagger.extractors.pitched.texture import TextureExtractor
from midi_analyzer_tagger.extractors.pitched.harmonic_intervals import HarmonicIntervalsExtractor
from midi_analyzer_tagger.extractors.pitched.melodic import MelodicExtractor
from midi_analyzer_tagger.extractors.pitched.register import RegisterExtractor
from midi_analyzer_tagger.extractors.pitched.tonality import TonalityExtractor

PLUGINS = [
    DrumRouterExtractor(),
    DynamicsExtractor(),
    DurationExtractor(),
    GridExtractor(),
    TextureExtractor(),
    HarmonicIntervalsExtractor(),
    MelodicExtractor(),
    MetadataExtractor(),
    RhythmicDensityExtractor(),
    RegisterExtractor(),
    SpacingExtractor(),
    TonalityExtractor(),
]
