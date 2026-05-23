"""Independent Python client for the public OpenCaseLaw API."""

from .client import OpenCaseLawClient
from .config import DEFAULT_CONFIG, OpenCaseLawConfig, load_config
from .models import (
    Citation,
    Court,
    Decision,
    DecisionSearchResult,
    DecisionSummary,
    Law,
    LawArticle,
)

__version__ = "0.1.0"

__all__ = [
    "Citation",
    "Court",
    "DEFAULT_CONFIG",
    "Decision",
    "DecisionSearchResult",
    "DecisionSummary",
    "Law",
    "LawArticle",
    "OpenCaseLawClient",
    "OpenCaseLawConfig",
    "load_config",
]
