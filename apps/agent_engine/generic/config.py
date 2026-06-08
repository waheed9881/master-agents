"""Configuration dataclasses for generic business agents."""
from dataclasses import dataclass, field


@dataclass
class HandoffConfig:
    """Agent-specific handoff triggers."""

    handoff_intents: frozenset = frozenset()
    safety_keywords: tuple[str, ...] = ()
    urgent_keywords: tuple[str, ...] = ()


@dataclass
class ScoringConfig:
    """Rules for lead scoring and hot-lead detection."""

    hot_signal_sets: list[frozenset] = field(default_factory=list)
    qualified_intents: frozenset = frozenset()
    demo_intents: frozenset = frozenset()


@dataclass
class ExtractorConfig:
    """Domain keyword patterns for intent and field extraction."""

    intent_keywords: dict[str, list[str]] = field(default_factory=dict)
    need_keywords: dict[str, str] = field(default_factory=dict)
    location_keywords: tuple[str, ...] = ()
    property_type_keywords: dict[str, str] = field(default_factory=dict)


@dataclass
class AgentBrainConfig:
    """Full configuration for a GenericBusinessAgent."""

    template_slug: str
    extractor: ExtractorConfig = field(default_factory=ExtractorConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    handoff: HandoffConfig = field(default_factory=HandoffConfig)
    lead_title_prefix: str = "Inquiry"
    follow_up_intents: frozenset = frozenset()
