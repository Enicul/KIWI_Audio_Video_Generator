"""
KIWI-Video: Multi-Agent Text-to-Video Generation Framework

A production-ready framework for generating videos from text using AI agents.
"""

__version__ = "0.1.0"
__author__ = "KIWI-Video Team"

from kiwi_video.core.orchestrator import DirectorOrchestrator
from kiwi_video.schemas.project import ProjectStatus

__all__ = ["DirectorOrchestrator", "ProjectStatus"]

