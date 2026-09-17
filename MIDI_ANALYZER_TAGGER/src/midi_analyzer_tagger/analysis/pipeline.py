from midi_analyzer_tagger.analysis.midi_data import MidiData
from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.core import AnalysisPayload
from midi_analyzer_tagger.normalizers import DefaultNormalizer


class Pipeline:
    def __init__(self, registry: ExtractorRegistry, default_normalizer=None):
        self.registry = registry
        self.default_normalizer = default_normalizer or DefaultNormalizer()

    def analyze(self, midi_data: MidiData) -> AnalysisPayload:
        tags = {}
        raw_features = {}
        normalized_features = {}

        for extractor in self.registry.get_for_family(midi_data.family):
            plugin_raw = extractor.extract(midi_data)
            plugin_tags = extractor.quantize(plugin_raw)

            valid_concepts = {c.name for c in extractor.concepts if self.registry.owns_concept(extractor.name, c.name)}

            for concept_name, raw_value in plugin_raw.items():
                if concept_name not in valid_concepts:
                    continue
                raw_features[concept_name] = raw_value

            for concept_name, level in plugin_tags.items():
                if concept_name not in valid_concepts:
                    continue
                tags[concept_name] = level

            for concept in extractor.concepts:
                if concept.name not in valid_concepts:
                    continue
                normalizer = concept.normalizer or self.default_normalizer
                normalized_features[concept.name] = normalizer.normalize(
                    plugin_raw.get(concept.name),
                    plugin_tags.get(concept.name),
                    concept,
                )

        metadata = {
            "duration": midi_data.duration,
            "note_count": len(midi_data.notes),
            "family": midi_data.family,
        }

        return AnalysisPayload(
            family=midi_data.family,
            metadata=metadata,
            tags=tags,
            raw_features=raw_features,
            normalized_features=normalized_features,
        )
