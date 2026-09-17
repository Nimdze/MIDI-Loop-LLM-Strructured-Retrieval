from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class Level:
    name: str
    weight: int
    description: str = ""
    index: int | None = None


class Normalizer(ABC):
    """Convert a raw feature value into a normalized representation, e.g., [0, 1]."""

    @abstractmethod
    def normalize(self, raw_value: Any, level: Level | None, concept: Any) -> Any:
        pass


class Quantizer(ABC):
    """Strategy that maps a raw feature value to a Level."""

    @abstractmethod
    def quantize(self, raw_value: Any) -> Level | None:
        pass


@dataclass
class Concept:
    """A measurable dimension with ordered levels."""

    name: str
    category: str  # rhythm, harmony, melody, expression, tonality, drums
    family: list[str]
    levels: list[Level]
    quantizer: Quantizer
    normalizer: Normalizer | None = None
    description: str = ""
    mutually_exclusive: bool = True
    default_weight: float = 1.0
    scope: Literal["summary", "detail"] = "summary"

    # Paired concept (e.g. grid_attempt_pct_X paired with grid_success_pct_X)
    pair_with: str | None = None
    pair_role: str | None = None  # "attempt" or "success" for grid pairs

    # LLM / search-facing metadata
    llm_description: str | None = None
    llm_interpretation: str | None = None
    llm_examples: list[str] | None = None
    llm_level_descriptions: dict[str, str] | None = None
    llm_subcategory: str | None = None
    # Explicit histogram/aggregation family, overriding the name-based
    # detection in the registry. Concepts sharing a family render as one
    # grouped block (e.g. the macro consonance aggregates).
    llm_bin_family: str | None = None
    llm_bin_label: str | None = None

    def quantize(self, raw_value: Any) -> Level | None:
        return self.quantizer.quantize(raw_value)

    def display_name(self) -> str:
        """Return the internal name used in the LLM prompt and search schema.

        The internal concept name is the single source of truth; no aliases are used.
        """
        return self.name


class FeatureExtractor(ABC):
    def __init__(
        self,
        name: str,
        concepts: list[Concept],
        llm_description: str = "",
        llm_subcategory: str | None = None,
        llm_category_description: str | None = None,
        llm_category_interpretation: str | None = None,
        llm_category_examples: list[str] | None = None,
    ):
        self.name = name
        self.concepts = concepts
        self.llm_description = llm_description
        self.llm_subcategory = llm_subcategory
        self.llm_category_description = llm_category_description
        self.llm_category_interpretation = llm_category_interpretation
        self.llm_category_examples = llm_category_examples or []

    @abstractmethod
    def extract(self, midi_data: Any) -> dict[str, Any]:
        pass

    def quantize(self, raw_features: dict[str, Any]) -> dict[str, Level | None]:
        return {concept.name: concept.quantize(raw_features.get(concept.name)) for concept in self.concepts}


@dataclass
class AnalysisPayload:
    """Output of the pipeline for one MIDI file."""

    family: str
    metadata: dict[str, Any]
    tags: dict[str, Level | None]
    raw_features: dict[str, Any]
    normalized_features: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "metadata": self.metadata,
            "tags": {name: level.name if level else None for name, level in self.tags.items()},
            "raw_features": self.raw_features,
            "normalized_features": self.normalized_features,
        }
