"""
NLP Processing Package for Job Description Analysis.

This package provides a complete NLP pipeline for extracting structured
information from job descriptions, including:

- Text preprocessing and cleaning
- Rule-based information extraction
- Named Entity Recognition (NER)
- Keyword matching with fuzzy search
- Confidence scoring and validation

Main Components:
- processor: Main orchestrator class (JobDescriptionProcessor)
- preprocessor: Text cleaning (TextPreprocessor)
- rule_extractor: Regex-based extraction (RuleBasedExtractor)
- ner_extractor: SpaCy NER (NERExtractor)
- keyword_matcher: Dictionary matching (KeywordMatcher)

Example Usage:
    from core.processing import JobDescriptionProcessor

    processor = JobDescriptionProcessor()
    result = processor.process("Job description text...")
    print(f"Extracted skills: {result.skills}")
"""

from .processor import JobDescriptionProcessor, ProcessedJobInfo
from .preprocessor import TextPreprocessor
from .rule_extractor import RuleBasedExtractor
from .ner_extractor import NERExtractor
from .keyword_matcher import KeywordMatcher

__version__ = "1.0.0"
__author__ = "HR Automation Team"

__all__ = [
    "JobDescriptionProcessor",
    "ProcessedJobInfo",
    "TextPreprocessor",
    "RuleBasedExtractor",
    "NERExtractor",
    "KeywordMatcher"
]
