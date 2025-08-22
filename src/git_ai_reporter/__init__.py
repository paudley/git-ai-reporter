# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""AI-Driven Git Repository Analysis and Narrative Generation.

Copyright (c) 2025 Blackcat Informatics® Inc.
Licensed under the MIT License.
"""

__version__ = "0.1.0"
__author__ = "Blackcat Informatics® Inc."
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 Blackcat Informatics® Inc."

from .analysis.git_analyzer import GitAnalyzer
from .cache.manager import CacheManager
from .cli import APP
from .config import Settings
from .models import AnalysisResult
from .models import CommitAnalysis
from .orchestration import AnalysisOrchestrator
from .services.gemini import GeminiClient
from .writing.artifact_writer import ArtifactWriter

__all__ = ['APP', 'AnalysisOrchestrator', 'AnalysisResult', 'ArtifactWriter', 'CacheManager',
 'CommitAnalysis', 'GeminiClient', 'GitAnalyzer', 'Settings']
